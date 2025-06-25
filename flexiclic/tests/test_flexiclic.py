import json
import unittest
import responses

from flexiclic import FlexiClic
from flexiclic import errors


class TestFlexiClic(unittest.IsolatedAsyncioTestCase):
    maxDiff = None

    conc_data = [
        [["by"," ","Temple"," ","Bar",", ","in"," ","Lincoln's"," ","Inn"," ","Hall",", ","at"," ","the"," ","very"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",2547,2552],[1,4,18]],
        [["patience",", ","courage",", ","hope",", ","so"," ","overthrows"," ","the"," ","brain"," ","and"," ","breaks"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","that"," ","there"," ","is"," ","not"," ","an"," ","honourable"," ","man"," ","among"," ","its"," ","practitioners",[1,3,5,7,9,11,13,15,17,19]],["BH",5230,5235],[1,6,24]],
        [["Thus",", ","in"," ","the"," ","midst"," ","of"," ","the"," ","mud"," ","and"," ","at"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",11558,11563],[1,11,59]],
        [["to"," ","open"," ","my"," ","lips",", ","and"," ","never"," ","dared"," ","to"," ","open"," ","my"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","to"," ","anybody"," ","else",". ","It"," ","almost"," ","makes"," ","me"," ","cry"," ","to"," ","think",[1,3,5,7,9,11,13,15,17,19]],["BH",32184,32189],[3,2,6]],
        [["used"," ","ardently"," ","to"," ","hope"," ","that"," ","I"," ","might"," ","have"," ","a"," ","better"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",";",[0]],[" ","and"," ","I"," ","talked"," ","it"," ","over"," ","very"," ","often"," ","with"," ","the"," ","dear",[1,3,5,7,9,11,13,15,17,19]],["BH",33835,33840],[3,3,20]],
        [["she"," ","looked"," ","at"," ","me",", ","and"," ","laid"," ","it"," ","on"," ","my"," ","fluttering"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",".",[0]],[" ","She"," ","raised"," ","me",", ","sat"," ","in"," ","her"," ","chair",", ","and"," ","standing"," ","me",[1,3,5,7,9,11,13,15,17,19]],["BH",37435,37440],[3,14,58]],
        [["I"," ","had"," ","brought"," ","no"," ","joy"," ","at"," ","any"," ","time"," ","to"," ","anybody's"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","and"," ","that"," ","I"," ","was"," ","to"," ","no"," ","one"," ","upon"," ","earth"," ","what",[1,3,5,7,9,11,13,15,17,19]],["BH",38895,38900],[3,16,69]],
    ]

    async def _compute_path(self, data=[], annotations=[], path=[], speculative=False, should_fetch=None, expect_params={}):
        query_opts = {
            "corpora": "BH",
            "subset": "all",
            "q": "hello",
            "contextsize": 10,
            "metadata": ["chapter_start","word_count_all"],
        }
        meta = dict(
            version={"clic":"wip-flexiconc:d22612b","clic-import":"2.2:9c824c5","corpora":"64b4590"},
            chapter_start={"BH":{"1":53}},
            word_count_all={"BH":354273},
        )
        data = json.loads(json.dumps(data))
        for d in data:
            # The Flexiconc loop removes whitespace on left context, strip
            d[0].pop(len(d[0]) - 2)
        if should_fetch is None:
            should_fetch = not hasattr(self, "_fc")
        with responses.RequestsMock() as rsps:
            if should_fetch:
                # Only fetching when creating a new object
                rsps.add(
                    responses.GET,
                    "https://unittest.example.com/api/concordance",
                    match=[
                        responses.matchers.query_param_matcher(query_opts | expect_params),
                    ],
                    status=200,
                    content_type="application/json",
                    body=json.dumps({
                        "version": meta['version'],
                        "data": data,
                        "chapter_start": meta['chapter_start'],
                        "word_count_all": meta["word_count_all"]
                    }),
                )
            if not hasattr(self, "_fc"):
                self._fc = FlexiClic(api_root="https://unittest.example.com")
            for out_i, out_batch in enumerate([x async for x in self._fc.compute_path(opts=query_opts, annotations=annotations, path=path, speculative=speculative)]):
                if out_i == 0:
                    # CLiC metadata passes through untouched
                    for k in meta.keys():
                        self.assertEqual(out_batch[k], meta[k])
                    if "fc_extra_cols" in out_batch:
                        # If this query returns extra cols, we want to know about it
                        yield dict(fc_extra_cols=out_batch["fc_extra_cols"])
                    continue
                for out_l in out_batch:
                    data_i = 0
                    for data_l in data:
                        if out_l[0] == data_l[0] and out_l[1] == data_l[1] and out_l[2] == data_l[2] and out_l[3] == data_l[3] and out_l[4] == data_l[4]:
                            # Matches a data line, just return the index, not the full thing
                            yield tuple([data_i] + out_l[5:])
                            break
                        data_i += 1
                    else:
                        # No matching line, return full thing
                        yield tuple(out_l)

    async def test_compute_path_annotations(self):
        """
        Re-fetch happens when annotatios change
        """
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
        ], should_fetch=True)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
        ], should_fetch=False)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name": "Annotate with TF-IDF",
                "exclude_values_attribute": "",
                "include_node": "on",
                "tokens_attribute": "word",
                "window_end": "5",
                "window_start": "-5"
            }
        ], should_fetch=True)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name": "Annotate with TF-IDF",
                "exclude_values_attribute": "",
                "include_node": "on",
                "tokens_attribute": "word",
                "window_end": "5",
                "window_start": "-5"
            }
        ], should_fetch=False)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name": "Annotate with TF-IDF",
                "exclude_values_attribute": "",
                "include_node": "on",
                "tokens_attribute": "word",
                "window_end": "1",  # NB: Changed parameter
                "window_start": "-5"
            }
        ], should_fetch=True)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name": "Annotate with TF-IDF",
                "exclude_values_attribute": "",
                "include_node": "on",
                "tokens_attribute": "word",
                # NB: Parameter types changed, but post-normalisation this is fine
                "window_end": 1,
                "window_start": -5
            }
        ], should_fetch=False)]

        # Fetch unknown algorithm an error
        with self.assertRaisesRegex(KeyError, "unknown"):
            out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
                {
                    "algorithm_name": "unknown",
                }
            ], should_fetch=False)]
        # Try again, it's still an error
        with self.assertRaisesRegex(KeyError, "unknown"):
            out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
                {
                    "algorithm_name": "unknown",
                }
            ], should_fetch=False)]

    async def test_compute_path_noresults(self):
        """
        Should produce empty results if asked
        """
        out = [x async for x in self._compute_path(data=[], annotations=[
        ], should_fetch=True)]
        self.assertEqual(out, [])
        # Still has correct columns
        self.assertEqual(
            sorted(list(self._fc._flexiconc.metadata.columns)),
            ['chapter', 'cpos_end', 'cpos_start', 'line_id', 'paragraph', 'sentence', 'text_id'],
        )
        self.assertEqual(
            sorted(list(self._fc._flexiconc.tokens.columns)),
            ['after_token', 'before_token', 'id_in_line', 'line_id', 'norm', 'offset', 'word'],
        )

    async def test_compute_path_annotations_server_side(self):
        """
        Some annotations result in server-side arguments
        """
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
        ], should_fetch=True)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
        ], should_fetch=False)]
        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name": "Annotate with Sentence Transformers",
                "model_name": "bertha",
            }
        ], should_fetch=True, expect_params=dict(st_model_name="bertha"))]

    async def test_compute_path_speculate(self):
        """
        Don't recompute source concordance in speculate
        """
        with self.assertRaises(errors.UserConfirmError):
            out = [x async for x in self._compute_path(data=self.conc_data, path=[
            ], speculative=True, should_fetch=False)]
        # After running the query, can speculate
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
        ], should_fetch=True)]
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
        ], speculative=True, should_fetch=False)]

    async def test_compute_path_nopartition(self):
        # No path, just get lines back in same order
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
        ])]
        self.assertEqual(out, [
            (0, 0, 0, {'matches': None}),
            (1, 0, 1, {'matches': None}),
            (2, 0, 2, {'matches': None}),
            (3, 0, 3, {'matches': None}),
            (4, 0, 4, {'matches': None}),
            (5, 0, 5, {'matches': None}),
            (6, 0, 6, {'matches': None}),
        ])

        # Columns match what FlexiConc expects
        self.assertEqual(
            sorted(list(self._fc._flexiconc.metadata.columns)),
            ['chapter', 'cpos_end', 'cpos_start', 'line_id', 'paragraph', 'sentence', 'text_id'],
        )
        self.assertEqual(
            sorted(list(self._fc._flexiconc.tokens.columns)),
            ['after_token', 'before_token', 'id_in_line', 'line_id', 'norm', 'offset', 'word'],
        )

        # Random sample, get given line
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
            {"algorithm_name":"Random Sample","sample_size":"2","seed":"3"},
        ])]
        self.assertEqual(out, [
            (1, 0, 1, {'matches': None}),
            (4, 0, 4, {'matches': None})
        ])

        # Random sample+sort
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
            {"algorithm_name":"Random Sample","sample_size":"4","seed":"3"},
            {"algorithm_name":"Random Sort","seed":"3"},
        ])]
        self.assertEqual(out, [
            (4, 0, 4, {'matches': None}),
            (6, 0, 6, {'matches': None}),
            (5, 0, 5, {'matches': None}),
            (1, 0, 1, {'matches': None}),
        ])

    async def test_compute_path_partition(self):
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
            {"algorithm_name":"Partition by Ngrams","positions":["1","3"],"tokens_attribute":"word"},
        ])]
        self.assertEqual(out, [
            (['Partition', []], ['hello', []], ["('of', 'fog')", []], ['', '', ''], ['', '', ''], 0, '', {'rowcount': 2}),
            (0, 0, 0, {'matches': None}),
            (2, 0, 2, {'matches': None}),
            (['Partition', []], ['hello', []], ["('and', 'i')", []], ['', '', ''], ['', '', ''], 1, '', {'rowcount': 1}),
            (6, 1, 6, {'matches': None}),
            (['Partition', []], ['hello', []], ["('and', 'talked')", []], ['', '', ''], ['', '', ''], 2, '', {'rowcount': 1}),
            (4, 2, 4, {'matches': None}),
            (['Partition', []], ['hello', []], ["('she', 'me')", []], ['', '', ''], ['', '', ''], 3, '', {'rowcount': 1}),
            (5, 3, 5, {'matches': None}),
            (['Partition', []], ['hello', []], ["('that', 'is')", []], ['', '', ''], ['', '', ''], 4, '', {'rowcount': 1}),
            (1, 4, 1, {'matches': None}),
            (['Partition', []], ['hello', []], ["('to', 'else')", []], ['', '', ''], ['', '', ''], 5, '', {'rowcount': 1}),
            (3, 5, 3, {'matches': None}),
        ])

    async def test_compute_path_term_highlight(self):
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
            { "algorithm_name": "KWIC Grouper Ranker", "count_types": "on", "search_terms": ["the"], "tokens_attribute": "word", "window_end": "10", "window_start": "-10"},
        ])]
        self.assertEqual(out, [
            dict(fc_extra_cols=[
                dict(title='Ranking: KWIC Grouper Ranker', description='Ranking score of the line from KWIC Grouper Ranker (ordering algorithm #0)'),
            ]),
            (0, 0, 0, {'matches': [[2], [], [2, 5]], 'fc_extra_cols': [1]}),
            (1, 0, 1, {'matches': [[5, 1], [], []], 'fc_extra_cols': [1]}),
            (2, 0, 2, {'matches': [[8, 5, 1], [], [2, 5]], 'fc_extra_cols': [1]}),
            (4, 0, 4, {'matches': [[], [], [9]], 'fc_extra_cols': [1]}),
            (3, 0, 3, {'matches': None, 'fc_extra_cols': [0]}),
            (5, 0, 5, {'matches': None, 'fc_extra_cols': [0]}),
            (6, 0, 6, {'matches': None, 'fc_extra_cols': [0]}),
        ])
        # Make a query without extra columns afterwards, they clear from results
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
        ])]
        self.assertEqual(out, [
            (0, 0, 0, {'matches': None}),
            (1, 0, 1, {'matches': None}),
            (2, 0, 2, {'matches': None}),
            (3, 0, 3, {'matches': None}),
            (4, 0, 4, {'matches': None}),
            (5, 0, 5, {'matches': None}),
            (6, 0, 6, {'matches': None}),
        ])

    async def test_compute_path_term_tokenlabel(self):
        try:
            import spacy
            import en_core_web_md
        except ImportError:
            self.skipTest("We need spaCy / en_core_web_md installed for this test")

        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                'algorithm_name': 'Annotate with spaCy POS tags',
                'spacy_model': 'en_core_web_md',
                'tokens_attribute': 'word',
                'spacy_attributes': 'pos_',
            },
        ], path=[
            {
                'algorithm_name': 'Select by Token-Level String Attribute',
                'search_terms': ['noun', 'verb'],
                'tokens_attribute': 'pos_',
                'offset': '2',
                'case_sensitive': None,
                'regex': None,
                'negative': None,
            },
        ], should_fetch=True)]
        self.assertEqual(out, [
            (5, 0, 5, {'matches': [[], [], [2]], 'match_label': [{}, {}, {3: 'VERB'}]}),
        ])

        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                'algorithm_name': 'Annotate with spaCy POS tags',
                'spacy_model': 'en_core_web_md',
                'tokens_attribute': 'word',
                'spacy_attributes': 'pos_',
            },
        ], path=[
            {
                'algorithm_name': 'Select by Token-Level String Attribute',
                'search_terms': ['noun', 'verb'],
                'tokens_attribute': 'pos_',
                'offset': '-2',
                'case_sensitive': None,
                'regex': None,
                'negative': None,
            },
        ], should_fetch=False)]
        self.assertEqual(out, [
            (1, 0, 1, {'matches': [[2], [], []], 'match_label': [{16: 'VERB'}, {}, {}]}),
            (3, 0, 3, {'matches': [[2], [], []], 'match_label': [{16: 'VERB'}, {}, {}]}),
        ])

    async def test_algorithm_render_html_context(self):
        try:
            import spacy
            import en_core_web_md
        except ImportError:
            self.skipTest("We need spaCy / en_core_web_md installed for this test")

        # Before FlexiConc available, don't get an enum
        out = "".join(x for x in FlexiClic(api_root="https://unittest.example.com").algorithm_render_html("Flat Clustering by Embeddings", "utprefix") if "embeddings_column" in x)
        self.assertEqual(out, "\n".join((
            '<label for="ctlb-flexiconc-utprefix[embeddings_column]"><span style="color: red" title="This property is required">*</span> The metadata column containing embeddings for each line.</label>',
            '<input type="text" name="utprefix[embeddings_column]" id="ctlb-flexiconc-utprefix[embeddings_column]" class="form-control" >',
        )))

        out = [x async for x in self._compute_path(data=self.conc_data, annotations=[
            {
                "algorithm_name":"Annotate with SpaCy Embeddings",
                "exclude_values_attribute":"",
                "include_node":"on",
                "spacy_model":"en_core_web_md",
                "tokens_attribute":"word",
                "window_end":"5",
                "window_start":"-5"
            },
        ], path=[
        ], should_fetch=True)]

        # Now we have a FlexiConc, we get decorated with an enum
        out = "".join(x for x in self._fc.algorithm_render_html("Flat Clustering by Embeddings", "utprefix") if "embeddings_column" in x)
        self.assertEqual(out, "\n".join((
            '<label for="ctlb-flexiconc-utprefix[embeddings_column]"><span style="color: red" title="This property is required">*</span> The metadata column containing embeddings for each line.</label>',
            '<select name="utprefix[embeddings_column]" id="ctlb-flexiconc-utprefix[embeddings_column]" class="tomselect " ><option value="embeddings_spacy" >embeddings_spacy</option></select>',
        )))


    async def test_tidy_paths(self):
        out = [x async for x in self._compute_path(data=self.conc_data, path=[
            {"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"},
        ])]
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2]],
        )
        await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "1": [{"algorithm_name":"Partition by Ngrams","positions":["1","3"],"tokens_attribute":"word"}],
        })
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2], [3]],
        )
        await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "1": [{"algorithm_name":"Partition by Ngrams","positions":["1","3"],"tokens_attribute":"word"}],
            "2": [{"algorithm_name":"Partition by Ngrams","positions":["1","5"],"tokens_attribute":"word"}],
        })
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2], [3], [4]],
        )
        await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "2": [{"algorithm_name":"Partition by Ngrams","positions":["1","5"],"tokens_attribute":"word"}],
        })
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2], [4]],
        )
        await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "2": [{"algorithm_name":"Partition by Ngrams","positions":["1","5"],"tokens_attribute":"word"}],
            "3": [{"algorithm_name":"Partition by Ngrams","positions":["1","6"],"tokens_attribute":"word"}],
        })
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2], [4], [5]],
        )

        out = await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "2": [{"algorithm_name":"Partition by Ngrams","positions":["1","5"],"tokens_attribute":"word"}],
            # NB: This error is included in the response
            "3": [{"algorithm_name":"Nonexistant algo","positions":["1","6"],"tokens_attribute":"word"}],
        })
        self.assertEqual(out, {
            '0': 2,
            '2': 4,
            '3': "KeyError: 'Nonexistant algo'",
        })
        self.assertEqual(
            self._fc.tree_ids(),
            [1, [2], [4]],
        )

    async def test_tidy_paths_noopts(self):
        """Try tidying without setting up opts/annotations"""
        self._fc = FlexiClic(api_root="https://unittest.example.com")
        out = await self._fc.tidy_paths(paths={
            "0": [{"algorithm_name":"Partition by Ngrams","positions":["1","2"],"tokens_attribute":"word"}],
            "2": [{"algorithm_name":"Partition by Ngrams","positions":["1","5"],"tokens_attribute":"word"}],
        })
        self.assertEqual(out, {
            '0': 'UserError: No valid CLiC query has been entered yet',
            '2': 'UserError: No valid CLiC query has been entered yet',
        })
