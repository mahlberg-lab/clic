'''
    ./bin/python tests/exerciser.py
'''
import sys
import asyncio
from flexiclic import FlexiClic

fc = FlexiClic(api_root="https://clic-fiction.com")

test_query = sys.argv[1] if len(sys.argv) > 1 else "no_path"

if test_query == "no_path":
    opts = dict(
        corpora="BH",
        subset="all",
        q="hoarding",
        contextsize=10,
    )
    annotations = []
    path = []
elif test_query == "match_label":
    opts = {'corpora': ['BH'], 'subset': 'all', 'q': 'foot', 'contextsize': 10, 'metadata': ['chapter_start', 'word_count_all']}
    annotations = [
        {
            'algorithm_name': 'Annotate with spaCy POS tags',
            'spacy_model': 'en_core_web_md',
            'tokens_attribute': 'word',
            'spacy_attributes': 'pos_',
        },
    ]
    path = [
        {
            'algorithm_name': 'Select by Token-Level String Attribute',
            'search_terms': ['noun', 'verb'],
            'tokens_attribute': 'pos_',
            'offset': '2',
            'case_sensitive': None,
            'regex': None,
            'negative': None,
        },
    ]
elif test_query == "kwic_grouper_ranker":
    opts = {"corpora":["corpus:DE19"],"subset":"all","q":"hinter","contextsize":10,"metadata":["chapter_start","word_count_all"]}
    annotations = []
    path = [
        {
            "regex":None,
            "case_sensitive":None,
            "include_node":None,
            "algorithm_name":"KWIC Grouper Ranker",
            "search_term":"er",
            "tokens_attribute":"word",
            "window_start":"",
            "window_end":"",
            "count_types": "on",
        },
    ]
else:
    raise ValueError("Unknown test query %s" % test_query)

async def main():
    async for x in fc.compute_path(opts, annotations, path):
        print(x)

asyncio.run(main())
