import re

import pandas as pd

def clic_to_flexiconc(data, annotation_lines={}):
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
    metadata_df = pd.DataFrame(metadata_list)

    for column_name, column_data in annotation_lines.items():
        # i.e. the equivalent of flexiconc/concordance:add_annotation
        metadata_df[column_name] = pd.Series(
            data=column_data,
            index=range(len(column_data)),
            name=column_name,
        )

    return dict(
        metadata=metadata_df,
        tokens=tokens_df,
        matches=pd.DataFrame(matches_list),
    )
