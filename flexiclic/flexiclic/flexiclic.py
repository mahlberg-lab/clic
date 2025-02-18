import collections
import requests
import pandas as pd
import re

import flexiconc
# TODO: Does this even need to be a thing? Should we just merge into flexiconc package?

from . import algo_html
from . import path_util

class FlexiClic():
    def __init__(self, api_root=""):
        """
        Create a flexiconc<->CLiC adapter

        - api_root: Prefix for API calls, e.g. "https://api.clic-project.org"
        """
        self._api_root = api_root
        self._source_opts = {}
        self._clic_meta = {}

    def _flexiconc_concordance(self, data=None):
        if data is not None:
            self._flexiconc = flexiconc.Concordance()
            self._flexiconc.load(**self._convert_to_flexiconc(data))
        elif not hasattr(self, "_flexiconc"):
            self._flexiconc = flexiconc.Concordance()
        return self._flexiconc

    def _follow_path(self, opts, path):
        """
        Follow path of algorithms, return Node at end

        - opts: dict of arguments to /api/concordance
        - path: List of unsorted algorithms to apply
        """
        concordance = self._flexiconc_concordance()
        path, annotations = path_util.normalize(path, concordance.available_algorithms)

        if self._source_opts != opts or self._source_annotations != annotations:
            self._source_opts = opts
            self._source_annotations = annotations

            # Fetch query from CLiC server
            response = requests.get("%s/api/concordance" % (self._api_root), params=opts)
            response.raise_for_status()
            data = response.json()
            self._clic_meta = {k:data[k] for k in opts.get('metadata', []) + ['version']}

            # Re-create concordance object, add any required annotations
            concordance = self._flexiconc_concordance(data=data.get('data', []))
            for a in annotations:  # NB: Assume first entry is annotations
                concordance.add_annotation(
                    a["algorithm_name"],
                    a,
                    a["column_name"],
                )

        node = concordance.root
        for node_spec in path:
            if node_spec["algorithm_type"] == "subset" or node_spec["algorithm_type"] == "selection":
                node = node.add_subset_node(node_spec["algorithm_name"], node_spec["args"])
            elif node_spec["algorithm_type"] == "arrangement":
                node = node.add_arrangement_node(
                    ordering=node_spec["ordering"],
                    grouping=node_spec["grouping"],
                )
            else:
                raise ValueError("Unknown node spec: %s" % node_spec)

        return self._clic_meta, node

    def algorithms_by_type(self):
        concordance = self._flexiconc_concordance()

        out = collections.defaultdict(list)
        for algo_name, algo_metadata in concordance.available_algorithms.items():
            out[algo_metadata["algorithm_type"]].append(dict(
                name=algo_name,
                label=algo_name,
            ))
        return out

    def algorithm_render_html(self, algo_name, index):
        concordance = self._flexiconc_concordance()

        return algo_html.from_schema(concordance.available_algorithms[algo_name], index)

    def compute_path(self, opts, path):
        """
        Return concordance line data for a path of algorithms

        - opts: CLiC concordance API options
        - path: Array of algorithms to apply to query results
        """
        def sorted_line_ids(line_ids):
            if hasattr(node, 'ordering_result') and 'sort_keys' in node.ordering_result:
                # Filter sort_keys to include only line_ids in this partition
                partition_sort_keys = {line_id: node.ordering_result["sort_keys"][line_id] for line_id in line_ids if line_id in node.ordering_result["sort_keys"]}
                # Sort line_ids based on sort_keys
                line_ids = sorted(partition_sort_keys, key=partition_sort_keys.get)
            return line_ids

        def to_clic_context(tokens):
            before = tokens['before_token'].tolist()
            word = tokens['word'].tolist()
            after = tokens['after_token'].tolist()

            out = []
            type_idx = []
            for i, _ in enumerate(word):
                if before[i]:  # i.e. ignore 0-length strings
                    out.append(before[i])
                if word[i]:
                    type_idx.append(len(out))
                    out.append(word[i])
                if after[i]:
                    out.append(after[i])
            out.append(type_idx)
            return out

        # Deep arguments, so will be proxy objects from Javascript
        if hasattr(opts, "to_py"):
            opts = opts.to_py()
        if hasattr(path, "to_py"):
            path = path.to_py()

        clic_meta, node = self._follow_path(opts, path)
        view = node.view()

        # Pull concordance DataFrames back out of FlexiConc
        concordance = self._flexiconc_concordance()
        tokens = concordance.tokens
        metadata = concordance.metadata

        if "grouping" in view:
            partition_line_ids = {
                p["label"]: p["line_ids"]
                for p in view["grouping"]
            }
        else:
            partition_line_ids = {
                "": view["ordering"],
            }

        if "global_info" in view:
            clic_meta["global_info"] = view["global_info"]

        if "token_spans" in view:
            raise NotImplementedError

        yield clic_meta  # Return clic metadata to client first

        for partition_label, line_ids in partition_line_ids.items():
            # TODO: Header row for partition
            for line_id in line_ids:
                # Borrowed from html_visualizer:_generate_lines_html
                # Get tokens for this line
                line_tokens = tokens[tokens['line_id'] == line_id]

                # Sort tokens by offset and id_in_line to preserve order
                line_tokens = line_tokens.sort_values(by=['offset', 'id_in_line'])
                line_meta = metadata[metadata['line_id'] == line_id].to_dict('records')[0]

                # Create array entry to be digested in page_flexiconc.js:table_opts.non_tag_columns
                yield (
                    to_clic_context(line_tokens[line_tokens['offset'] < 0]),
                    to_clic_context(line_tokens[line_tokens['offset'] == 0]),
                    to_clic_context(line_tokens[line_tokens['offset'] > 0]),
                    [
                        line_meta['text_id'],  # Book
                        line_meta['cpos_start'],  # Start position
                        line_meta['cpos_end'],  # End position
                    ],
                    [
                        line_meta['chapter'],  # Chapter
                        line_meta['paragraph'],  # Paragraph
                        line_meta['sentence'],  # Sentence
                    ],
                    partition_label,
                    line_id,
                    view.get("line_info", {}).get(line_id, {}),
                )

    def _convert_to_flexiconc(self, data):
        """
        Convert CLiC concordance lines into FlexiConc DataFrames

        - data: Concordance lines from CLiC's /api/concordance endpoint

        Returns a dict of:

        - metadata: DataFrame of concordance line metadata
        - tokens: DataFrame of concordance line tokens
        - matches: DataFrame of concordance line matches
        """
        def process_context(context_data, context_type):
            def inside_flextoken(i):
                if i < 0 or i >= len(context_data) - 1:
                    # Hit an end of context array
                    return False
                if i in context_data[-1]:
                    # Hit another type, stop
                    return False
                if re.fullmatch(r"\s*", context_data[i]):
                    # Whitespace token, this marks the end
                    return False
                return True

            type_pos = context_data[-1]
            tokens = context_data[:-1]
            out = []
            division_idx = -1
            for type_offset, type_idx in enumerate(type_pos):
                # Find the token after the type_idx that marks a division in flexconc tokens
                next_division_idx = type_idx
                while inside_flextoken(next_division_idx + 1):
                    next_division_idx += 1

                if context_type == 'left':
                    offset = 0 - len(type_pos) + type_offset
                elif context_type == 'node':
                    offset = 0
                elif context_type == 'right':
                    offset = type_offset + 1
                else:
                    raise ValueError("Invalid context_type.")

                out.append(dict(
                    offset=offset,
                    before_token=''.join(tokens[division_idx + 1:type_idx]),
                    word=tokens[type_idx],
                    # NB: This needs to be developed in lock-step with client/lib/concordance_utils.js / server/clic/tokenizer.py
                    norm=''.join(tokens[type_idx]).lower(),
                    after_token=''.join(tokens[type_idx + 1:next_division_idx + 1]),
                ))
                division_idx = next_division_idx
            return out

        # Initialize lists to store metadata and tokens
        metadata_list = []
        token_entries = []
        matches_list = []

        global_token_id = 0
        for line_id, line_data in enumerate(data):
            corpus_info = line_data[3]
            structural_info = line_data[4]
            metadata_list.append({
                'line_id': line_id,
                'text_id': corpus_info[0],
                'chapter': structural_info[0] if len(structural_info) > 0 else None,
                'paragraph': structural_info[1] if len(structural_info) > 1 else None,
                'sentence': structural_info[2] if len(structural_info) > 2 else None,
                'cpos_start': corpus_info[1],
                'cpos_end': corpus_info[2],
            })

            left_tokens = process_context(line_data[0], 'left')
            node_tokens = process_context(line_data[1], 'node')
            right_tokens = process_context(line_data[2], 'right')
            for id_in_line, t in enumerate(left_tokens + node_tokens + right_tokens):
                t['line_id'] = line_id
                t['id_in_line'] = id_in_line
                t['id'] = global_token_id
                global_token_id += 1
            token_entries.extend(left_tokens + node_tokens + right_tokens)

            matches_list.append({
                'line_id': line_id,
                'match_start': node_tokens[0]['id'],
                'match_end': node_tokens[-1]['id'],
                'slot': 0
            })

        tokens_df = pd.DataFrame(token_entries)
        tokens_df.set_index('id', inplace=True)
        return dict(
            metadata=pd.DataFrame(metadata_list),
            tokens=tokens_df,
            matches=pd.DataFrame(matches_list),
        )
