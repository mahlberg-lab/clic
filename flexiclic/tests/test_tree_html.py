import re
import json
import unittest
import responses

from flexiclic import FlexiClic


class TestTreeHtml(unittest.IsolatedAsyncioTestCase):
    maxDiff = None

    async def _render_tree(self, data=[], paths=[]):
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
            if not hasattr(self, "_fc"):
                self._fc = FlexiClic(api_root="https://unittest.example.com")
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
            out = "\n".join(await self._fc.render_tree_html(opts=query_opts, annotations=[], paths=paths))
            # Filter button-group down to path-name, we don't need to check the specifics
            out = re.sub(r'<div class="button-group" data-path-name="(\d+)".*?</div>', '<div class="button-group" data-path-name="\\1"></div>', out)
            return out

    async def test_from_node(self):
        data = [
            [["by"," ","Temple"," ","Bar",", ","in"," ","Lincoln's"," ","Inn"," ","Hall",", ","at"," ","the"," ","very"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",2547,2552],[1,4,18]],
            [["patience",", ","courage",", ","hope",", ","so"," ","overthrows"," ","the"," ","brain"," ","and"," ","breaks"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","that"," ","there"," ","is"," ","not"," ","an"," ","honourable"," ","man"," ","among"," ","its"," ","practitioners",[1,3,5,7,9,11,13,15,17,19]],["BH",5230,5235],[1,6,24]],
            [["Thus",", ","in"," ","the"," ","midst"," ","of"," ","the"," ","mud"," ","and"," ","at"," ","the"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","of"," ","the"," ","fog",", ","sits"," ","the"," ","Lord"," ","High"," ","Chancellor"," ","in"," ","his",[1,3,5,7,9,11,13,15,17,19]],["BH",11558,11563],[1,11,59]],
            [["to"," ","open"," ","my"," ","lips",", ","and"," ","never"," ","dared"," ","to"," ","open"," ","my"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",",",[0]],[" ","to"," ","anybody"," ","else",". ","It"," ","almost"," ","makes"," ","me"," ","cry"," ","to"," ","think",[1,3,5,7,9,11,13,15,17,19]],["BH",32184,32189],[3,2,6]],
            [["used"," ","ardently"," ","to"," ","hope"," ","that"," ","I"," ","might"," ","have"," ","a"," ","better"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",";",[0]],[" ","and"," ","I"," ","talked"," ","it"," ","over"," ","very"," ","often"," ","with"," ","the"," ","dear",[1,3,5,7,9,11,13,15,17,19]],["BH",33835,33840],[3,3,20]],
            [["she"," ","looked"," ","at"," ","me",", ","and"," ","laid"," ","it"," ","on"," ","my"," ","fluttering"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",".",[0]],[" ","She"," ","raised"," ","me",", ","sat"," ","in"," ","her"," ","chair",", ","and"," ","standing"," ","me",[1,3,5,7,9,11,13,15,17,19]],["BH",37435,37440],[3,14,58]],
            [["I"," ","had"," ","brought"," ","no"," ","joy"," ","at"," ","any"," ","time"," ","to"," ","anybody's"," ",[0,2,4,6,8,10,12,14,16,18]],["heart",[0]],[" ","and"," ","that"," ","I"," ","was"," ","to"," ","no"," ","one"," ","upon"," ","earth"," ","what",[1,3,5,7,9,11,13,15,17,19]],["BH",38895,38900],[3,16,69]],
        ]

        # Compute 2 paths, get the combined tree
        out = await self._render_tree(data=data, paths={"1": [
            {"algorithm_name":"Random Sample","sample_size":"2","seed":"3"},
        ], "2" : [
            {"algorithm_name":"Random Sample","sample_size":"4","seed":"3"},
            {"algorithm_name":"Random Sort","seed":"3"},
        ]})
        self.assertEqual(out, """
<ul class="tree"><li class="tree"><div class="node root">7 lines</div><ul class="tree">
<li class="tree"><div class="node subset">
  <header>subset <span style="float: right">2 lines</span></header>
  <ul class="subset"><li class="subset"><h4>Random Sample</h4>{&#x27;sample_size&#x27;: 2, &#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="button-group" data-path-name="1"></div></li>
</ul></li>
<li class="tree"><div class="node subset">
  <header>subset <span style="float: right">4 lines</span></header>
  <ul class="subset"><li class="subset"><h4>Random Sample</h4>{&#x27;sample_size&#x27;: 4, &#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="node arrangement">
  <header>arrangement <span style="float: right">4 lines</span></header>
  <ul class="ordering"><li class="sorting"><h4>Random Sort</h4>{&#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="button-group" data-path-name="2"></div></li>
</ul></li>
</ul></li>
</ul></li></ul>
        """.strip())

        # Compute 0 paths, get an epty tree
        out = await self._render_tree(data=data, paths={})
        self.assertEqual(out, """
<ul class="tree"><li class="tree"><div class="node root">7 lines</div>
</li></ul>
        """.strip())

        # Compute 3 paths, with overlapping terminal nodes
        out = await self._render_tree(data=data, paths={"1": [
            {"algorithm_name":"Random Sample","sample_size":"2","seed":"3"},
        ], "2" : [
            {"algorithm_name":"Random Sample","sample_size":"4","seed":"3"},
            {"algorithm_name":"Random Sort","seed":"3"},
        ], "3" : [
            {"algorithm_name":"Random Sample","sample_size":"4","seed":"3"},
            {"algorithm_name":"Random Sort","seed":"3"},
        ]})
        self.assertEqual(out, """
<ul class="tree"><li class="tree"><div class="node root">7 lines</div><ul class="tree">
<li class="tree"><div class="node subset">
  <header>subset <span style="float: right">2 lines</span></header>
  <ul class="subset"><li class="subset"><h4>Random Sample</h4>{&#x27;sample_size&#x27;: 2, &#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="button-group" data-path-name="1"></div></li>
</ul></li>
<li class="tree"><div class="node subset">
  <header>subset <span style="float: right">4 lines</span></header>
  <ul class="subset"><li class="subset"><h4>Random Sample</h4>{&#x27;sample_size&#x27;: 4, &#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="node arrangement">
  <header>arrangement <span style="float: right">4 lines</span></header>
  <ul class="ordering"><li class="sorting"><h4>Random Sort</h4>{&#x27;seed&#x27;: 3}</li></ul>
</div><ul class="tree">
<li class="tree"><div class="button-group" data-path-name="2"></div></li>
<li class="tree"><div class="button-group" data-path-name="3"></div></li>
</ul></li>
</ul></li>
</ul></li></ul>
        """.strip())

        # Path with only root node
        out = await self._render_tree(data=data, paths={"1": []})
        self.assertEqual(out, """
<ul class="tree"><li class="tree"><div class="node root">7 lines</div><ul class="tree">
<li class="tree"><div class="button-group" data-path-name="1"></div></li>
</ul></li></ul>
        """.strip())
