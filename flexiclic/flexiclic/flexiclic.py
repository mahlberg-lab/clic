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
            self._retrieve_from_clic(
                **opts,
                api_base_url="%s/api/concordance" % (self._api_root),
            )
            # TODO: Do we need to rebuild the flexiconc tree?
        return self._clic_meta

    def next_algorithms_at(self, path, index):
        concordance = self._flexiconc_concordance()

        return list(concordance.root.available_algorithms().keys())

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
            out = tokens['word'].tolist()
            out.append(list(range(0,len(tokens))))  # TODO: Assume everything is a word for now
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

    def _retrieve_from_clic(
        self,
        query,
        corpora,
        subset = "all",
        contextsize = 20,
        api_base_url = "https://clic.bham.ac.uk/api/concordance",
        metadata_attrs = None,
        tokens_attrs = None
    ):
        """
        Modified version of flexiconc.utils.retrieve.retrieve_from_clic():

        * import AnalysisTreeNode
        * Modify self._flexiconc_concordance() instead of self
        * Request all query parameters in one go
        * Request required CLiC metadata, stash for returning to client
        * Store cpos_start / cpos_end in concordance.metadata
        """
        import requests
        from flexiconc.utils.logging import add_to_tree
        import pandas as pd
        import re

        from flexiconc.concordance import AnalysisTreeNode

        if metadata_attrs is None:
            metadata_attrs = ['text_id', 'chapter', 'paragraph', 'sentence']
        if tokens_attrs is None:
            tokens_attrs = ['word']

        params = {
            'q': query,
            'corpora': corpora,
            'subset': subset,
            'contextsize': contextsize,
            'metadata': ['chapter_start', 'word_count_all'],
        }
        response = requests.get(api_base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Stash required CLiC metadata to return to client later
        self._clic_meta = {k:data[k] for k in params['metadata'] + ['version']}
        data = data.get('data', [])

        if not data:
            raise ValueError(f"No data returned from CLiC API for the provided set of queries.")

        # Initialize lists to store metadata and tokens
        metadata_list = []
        token_entries = []
        matches_list = []

        global_token_id = 0
        token_pattern = re.compile(r'(\w+|[^\w\s])')

        for line_id, line_data in enumerate(data):
            left_context = line_data[0]
            node = line_data[1]
            right_context = line_data[2]
            corpus_info = line_data[3]
            structural_info = line_data[4]

            corpus_name = corpus_info[0]
            cpos_start = corpus_info[1]
            cpos_end = corpus_info[2]

            chapter = structural_info[0] if len(structural_info) > 0 else None
            paragraph = structural_info[1] if len(structural_info) > 1 else None
            sentence = structural_info[2] if len(structural_info) > 2 else None

            metadata_entry = {
                'line_id': line_id,
                'text_id': corpus_name,
                'chapter': chapter,
                'paragraph': paragraph,
                'sentence': sentence,
                'cpos_start': cpos_start,
                'cpos_end': cpos_end,
            }
            metadata_list.append(metadata_entry)

            id_in_line = 0

            def process_context(context_data, context_type):
                nonlocal id_in_line, global_token_id
                context_items = context_data[:-1]
                offsets_info = context_data[-1]
                context_str = ''.join(context_items)

                split_tokens = token_pattern.findall(context_str)
                tokens_list = [t for t in split_tokens if t.strip() != '' and not re.match(r'\s', t)]

                num_tokens = len(tokens_list)

                if context_type == 'left':
                    offsets_list = list(range(-num_tokens, 0))
                elif context_type == 'node':
                    offsets_list = [0] * num_tokens
                elif context_type == 'right':
                    offsets_list = list(range(1, num_tokens + 1))
                else:
                    raise ValueError("Invalid context_type.")

                tokens_result = []
                for tok, off in zip(tokens_list, offsets_list):
                    token_entry = {
                        'id': global_token_id,
                        'id_in_line': id_in_line,
                        'line_id': line_id,
                        'offset': off,
                        'word': tok
                    }
                    tokens_result.append(token_entry)
                    id_in_line += 1
                    global_token_id += 1
                return tokens_result

            left_tokens = process_context(left_context, 'left')
            node_tokens = process_context(node, 'node')
            right_tokens = process_context(right_context, 'right')

            line_tokens = left_tokens + node_tokens + right_tokens
            token_entries.extend(line_tokens)

            if node_tokens:
                match_start_id = node_tokens[0]['id']
                match_end_id = node_tokens[-1]['id']
            else:
                match_start_id = None
                match_end_id = None

            matches_entry = {
                'line_id': line_id,
                'match_start': match_start_id,
                'match_end': match_end_id,
                'slot': 0
            }
            matches_list.append(matches_entry)

        tokens_df = pd.DataFrame(token_entries)
        tokens_df.set_index('id', inplace=True)

        metadata_df = pd.DataFrame(metadata_list)
        matches_df = pd.DataFrame(matches_list)

        concordance = self._flexiconc_concordance()
        concordance.metadata = metadata_df
        concordance.tokens = tokens_df
        concordance.matches = matches_df
        concordance.info["query"] = query
        concordance.root = AnalysisTreeNode(id=0, node_type="subset", parent=None, concordance=concordance, line_count=len(concordance.metadata))
