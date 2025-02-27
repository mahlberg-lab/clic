import json
import unittest
import responses

from flexiclic import FlexiClic


class TestFlexiClic(unittest.TestCase):
    maxDiff = None

    def _compute_path(self, data=[], path=[]):
        query_opts = {
            "corpora": ["BH"],
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
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://unittest.example.com/api/concordance",
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "version": meta['version'],
                    "data": data,
                    "chapter_start": meta['chapter_start'],
                    "word_count_all": meta["word_count_all"]
                }),
            )
            fc = FlexiClic(api_root="https://unittest.example.com")
            for out_i, out_l in enumerate(fc.compute_path(query_opts, path)):
                if out_i == 0:
                    # CLiC metadata passes through untouched
                    for k in meta.keys():
                        self.assertEqual(out_l[k], meta[k])
                    continue
                data_i = 0
                for data_l in data:
                    if out_l[0] == data_l[0] and out_l[1] == data_l[1] and out_l[2] == data_l[2] and out_l[3] == data_l[3] and out_l[4] == data_l[4]:
                        # Matches a data line, just return the index, not the full thing
                        yield (data_i,) + out_l[5:]
                        break
                    data_i += 1
                else:
                    # No matching line, return full thing
                    yield out_l

    def test_compute_path_nopartition(self):
        data = [
            [["by"," ","Temple"," ","Bar",", ","in"," ","Lincoln's"," ","Inn"," ","Hall",", ","at"," ","the"," ","very"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",2547,2552],[1,4,18]],
            [["patience",", ","courage",", ","hope",", ","so"," ","overthrows"," ","the"," ","brain"," ","and"," ","breaks"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","that"," ","there"," ","is"," ","not"," ","an"," ","honourable"," ","man"," ","among"," ","its"," ","practitioners",[1,3,5,7,9,11,13,15,17,19]],["BH",5230,5235],[1,6,24]],
            [["Thus",", ","in"," ","the"," ","midst"," ","of"," ","the"," ","mud"," ","and"," ","at"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",11558,11563],[1,11,59]],
            [["to"," ","open"," ","my"," ","lips",", ","and"," ","never"," ","dared"," ","to"," ","open"," ","my"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","to"," ","anybody"," ","else",". ","It"," ","almost"," ","makes"," ","me"," ","cry"," ","to"," ","think",[1,3,5,7,9,11,13,15,17,19]],["BH",32184,32189],[3,2,6]],
            [["used"," ","ardently"," ","to"," ","hope"," ","that"," ","I"," ","might"," ","have"," ","a"," ","better"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",";",[0]],[" ","and"," ","I"," ","talked"," ","it"," ","over"," ","very"," ","often"," ","with"," ","the"," ","dear",[1,3,5,7,9,11,13,15,17,19]],["BH",33835,33840],[3,3,20]],
            [["she"," ","looked"," ","at"," ","me",", ","and"," ","laid"," ","it"," ","on"," ","my"," ","fluttering"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",".",[0]],[" ","She"," ","raised"," ","me",", ","sat"," ","in"," ","her"," ","chair",", ","and"," ","standing"," ","me",[1,3,5,7,9,11,13,15,17,19]],["BH",37435,37440],[3,14,58]],
            [["I"," ","had"," ","brought"," ","no"," ","joy"," ","at"," ","any"," ","time"," ","to"," ","anybody's"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","and"," ","that"," ","I"," ","was"," ","to"," ","no"," ","one"," ","upon"," ","earth"," ","what",[1,3,5,7,9,11,13,15,17,19]],["BH",38895,38900],[3,16,69]],
        ]
        # No path, just get lines back in same order
        out = list(self._compute_path(data=data, path=[
        ]))
        self.assertEqual(out, [
            (0, 0, 0, {'matches': None}),
            (1, 0, 1, {'matches': None}),
            (2, 0, 2, {'matches': None}),
            (3, 0, 3, {'matches': None}),
            (4, 0, 4, {'matches': None}),
            (5, 0, 5, {'matches': None}),
            (6, 0, 6, {'matches': None}),
        ])

        # Random sample, get given line
        out = list(self._compute_path(data=data, path=[
            {"algorithm_name":"Random Sample","sample_size":"2","seed":"3"},
        ]))
        self.assertEqual(out, [
            (1, 0, 1, {'matches': None}),
            (4, 0, 4, {'matches': None})
        ])

        # Random sample+sort
        out = list(self._compute_path(data=data, path=[
            {"algorithm_name":"Random Sample","sample_size":"4","seed":"3"},
            {"algorithm_name":"Random Sort","seed":"3"},
        ]))
        self.assertEqual(out, [
            (4, 0, 4, {'matches': None}),
            (6, 0, 6, {'matches': None}),
            (5, 0, 5, {'matches': None}),
            (1, 0, 1, {'matches': None}),
        ])

    def test_compute_path_partition(self):
        data = [
            [["by"," ","Temple"," ","Bar",", ","in"," ","Lincoln's"," ","Inn"," ","Hall",", ","at"," ","the"," ","very"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",2547,2552],[1,4,18]],
            [["patience",", ","courage",", ","hope",", ","so"," ","overthrows"," ","the"," ","brain"," ","and"," ","breaks"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","that"," ","there"," ","is"," ","not"," ","an"," ","honourable"," ","man"," ","among"," ","its"," ","practitioners",[1,3,5,7,9,11,13,15,17,19]],["BH",5230,5235],[1,6,24]],
            [["Thus",", ","in"," ","the"," ","midst"," ","of"," ","the"," ","mud"," ","and"," ","at"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",11558,11563],[1,11,59]],
            [["to"," ","open"," ","my"," ","lips",", ","and"," ","never"," ","dared"," ","to"," ","open"," ","my"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","to"," ","anybody"," ","else",". ","It"," ","almost"," ","makes"," ","me"," ","cry"," ","to"," ","think",[1,3,5,7,9,11,13,15,17,19]],["BH",32184,32189],[3,2,6]],
            [["used"," ","ardently"," ","to"," ","hope"," ","that"," ","I"," ","might"," ","have"," ","a"," ","better"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",";",[0]],[" ","and"," ","I"," ","talked"," ","it"," ","over"," ","very"," ","often"," ","with"," ","the"," ","dear",[1,3,5,7,9,11,13,15,17,19]],["BH",33835,33840],[3,3,20]],
            [["she"," ","looked"," ","at"," ","me",", ","and"," ","laid"," ","it"," ","on"," ","my"," ","fluttering"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",".",[0]],[" ","She"," ","raised"," ","me",", ","sat"," ","in"," ","her"," ","chair",", ","and"," ","standing"," ","me",[1,3,5,7,9,11,13,15,17,19]],["BH",37435,37440],[3,14,58]],
            [["I"," ","had"," ","brought"," ","no"," ","joy"," ","at"," ","any"," ","time"," ","to"," ","anybody's"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","and"," ","that"," ","I"," ","was"," ","to"," ","no"," ","one"," ","upon"," ","earth"," ","what",[1,3,5,7,9,11,13,15,17,19]],["BH",38895,38900],[3,16,69]],
        ]
        out = list(self._compute_path(data=data, path=[
            {"algorithm_name":"KWIC Patterns","positions":["1","3"],"tokens_attribute":"word"},
        ]))
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

    def test_compute_path_term_highlight(self):
        data = [
            [["by"," ","Temple"," ","Bar",", ","in"," ","Lincoln's"," ","Inn"," ","Hall",", ","at"," ","the"," ","very"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",2547,2552],[1,4,18]],
            [["patience",", ","courage",", ","hope",", ","so"," ","overthrows"," ","the"," ","brain"," ","and"," ","breaks"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","that"," ","there"," ","is"," ","not"," ","an"," ","honourable"," ","man"," ","among"," ","its"," ","practitioners",[1,3,5,7,9,11,13,15,17,19]],["BH",5230,5235],[1,6,24]],
            [["Thus",", ","in"," ","the"," ","midst"," ","of"," ","the"," ","mud"," ","and"," ","at"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",11558,11563],[1,11,59]],
            [["to"," ","open"," ","my"," ","lips",", ","and"," ","never"," ","dared"," ","to"," ","open"," ","my"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","to"," ","anybody"," ","else",". ","It"," ","almost"," ","makes"," ","me"," ","cry"," ","to"," ","think",[1,3,5,7,9,11,13,15,17,19]],["BH",32184,32189],[3,2,6]],
            [["used"," ","ardently"," ","to"," ","hope"," ","that"," ","I"," ","might"," ","have"," ","a"," ","better"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",";",[0]],[" ","and"," ","I"," ","talked"," ","it"," ","over"," ","very"," ","often"," ","with"," ","the"," ","dear",[1,3,5,7,9,11,13,15,17,19]],["BH",33835,33840],[3,3,20]],
            [["she"," ","looked"," ","at"," ","me",", ","and"," ","laid"," ","it"," ","on"," ","my"," ","fluttering"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",".",[0]],[" ","She"," ","raised"," ","me",", ","sat"," ","in"," ","her"," ","chair",", ","and"," ","standing"," ","me",[1,3,5,7,9,11,13,15,17,19]],["BH",37435,37440],[3,14,58]],
            [["I"," ","had"," ","brought"," ","no"," ","joy"," ","at"," ","any"," ","time"," ","to"," ","anybody's"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","and"," ","that"," ","I"," ","was"," ","to"," ","no"," ","one"," ","upon"," ","earth"," ","what",[1,3,5,7,9,11,13,15,17,19]],["BH",38895,38900],[3,16,69]],
        ]
        out = list(self._compute_path(data=data, path=[
            { "algorithm_name": "KWIC Grouper Ranker", "count_types": "on", "search_term": "the", "tokens_attribute": "word", "window_end": "10", "window_start": "-10"},
        ]))
        self.assertEqual(out, [
            (0, 0, 0, {'matches': [[2], [], []], 'rank_keys': {'algo_0': 1}}),
            (1, 0, 1, {'matches': [[5], [], []], 'rank_keys': {'algo_0': 1}}),
            (2, 0, 2, {'matches': [[8], [], []], 'rank_keys': {'algo_0': 1}}),
            (4, 0, 4, {'matches': [[], [], [9]], 'rank_keys': {'algo_0': 1}}),
            (3, 0, 3, {'matches': None, 'rank_keys': {'algo_0': 0}}),
            (5, 0, 5, {'matches': None, 'rank_keys': {'algo_0': 0}}),
            (6, 0, 6, {'matches': None, 'rank_keys': {'algo_0': 0}}),
        ])
