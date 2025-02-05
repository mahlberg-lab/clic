import collections
import requests
import pandas as pd
import re

import flexiconc
# TODO: Does this even need to be a thing? Should we just merge into flexiconc package?

class FlexiClic():
    def __init__(self, api_root=""):
        """
        Create a flexiconc<->CLiC adapter

        - api_root: Prefix for API calls, e.g. "https://api.clic-project.org"
        """
        self._api_root = api_root
        self._source_opts = {}
        self._clic_meta = {}

    def _flexiconc_concordance(self):
        if not hasattr(self, "_flexiconc"):
            self._flexiconc = flexiconc.Concordance()
        return self._flexiconc

    def set_source_data(self, **opts):
        """
        (re)fetch the root node for the flexiconc analysis tree

        - opts: kwargs passed to `flexiconc.concordance.retrieve_from_clic`.

        return the CLiC version dict from the server response
        """
        concordance = self._flexiconc_concordance()

        if self._source_opts != opts:
            self._source_opts = opts

            # Fetch query from CLiC server
            response = requests.get("%s/api/concordance" % (self._api_root), params=opts)
            response.raise_for_status()
            data = response.json()
            self._clic_meta = {k:data[k] for k in opts.get('metadata', []) + ['version']}

            self._flexiconc = flexiconc.Concordance()
            self._flexiconc.load(**self._convert_to_flexiconc(data.get('data', [])))
            # TODO: Do we need to rebuild the flexiconc tree?
        return self._clic_meta

    def algorithms_by_type(self):
        concordance = self._flexiconc_concordance()

        out = collections.defaultdict(list)
        for algo_name, algo_metadata in concordance.available_algorithms.items():
            out[algo_metadata["algorithm_type"]].append(dict(
                name=algo_name,
                label=algo_name,
            ))
        return out

    def algorithm_render_html(self, algo_name):
        return '\n'.join([
            "<legend>%s</legend>" % algo_name,
        ])

    def data_at(self, path, index):
        """
        Return concordance line data

        - path: The (flexiclic) path integer to query
        - index: The (flexiclic) index of the node along that path, 0 is the analysis tree root
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

        concordance = self._flexiconc_concordance()
        node = concordance.root
        subset = concordance.subset_at_node(node)

        tokens = subset.tokens
        metadata = subset.metadata

        # Collapse line groupings / sortings
        if hasattr(node, 'grouping_result') and 'partitions' in node.grouping_result:
            partition_line_ids = {
                partition_info.get('label', f'Partition {partition_id}'): sorted_line_ids(partition_info.get('line_ids', []))
                for partition_id, partition_info in enumerate(node.grouping_result['partitions'])
            }
        else:
            partition_line_ids = {
                "": sorted_line_ids(metadata['line_id'].unique().tolist()),
            }

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
