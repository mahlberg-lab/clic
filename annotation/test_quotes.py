import re
import unittest
from lxml import etree

from quotes import quotes

class TestQuotes(unittest.TestCase):
    def test_shortphrase(self):
        out = quotes(etree.fromstring("""
<div0 id="canada" type="book" subcorpus="ChiLit" filename="canada.txt">
<!--NB: canada is a double-quote book -->

<title>The Settlers in Canada</title>
<author>Frederick Marryat</author>
<p pid="1" id="canada.c0.p1"><s>[Illustration:</s> <s>BEE-HUNTING.]</s> </p>

<div id="canada.1" subcorpus="ChiLit" booktitle="The Settlers in Canada" book="canada" type="chapter" num="1">
<title>CHAPTER I.</title>

<p pid="1" id="canada.c1.p1"><s sid="1" id="canada.c1.s1">She would have Sophie to look over all her "toilettes," as she called frocks; to furbish up any that were "passees," and to air and arrange the new.</s></p>
<p pid="2" id="canada.c1.p2"><s sid="2" id="canada.c1.s2">My Lady Dedlock has been down at what she calls, in familiar conversation, her "place" in Lincolnshire.</s></p>

<p pid="3" id="canada.c1.p3"><s sid="3" id="canada.c1.s3">"Because"--"because father and mamma have to go away," I was going to say, when suddenly the full meaning of the words seemed to rush over me.</s></p>
</div>
</div0>
        """))
        out_string = etree.tostring(out)

        # 2 of the quoted short-phrases have been picked out
        self.assertEqual(re.findall(r'<qs/>.*?<qe/>', out_string), [
            '<qs/>"toilettes,"<qe/>',
            '<qs/>"passees,"<qe/>',
            '<qs/>"Because"<qe/>',
            '<qs/>"because father and mamma have to go away,"<qe/>',
        ])

    def test_single(self):
        out = quotes(etree.fromstring("""
<div0 id="singlequote" type="book" subcorpus="ChiLit" filename="canada.txt">

<div id="singlequote.1" subcorpus="ChiLit" booktitle="The Settlers in singlequote" book="singlequote" type="chapter" num="1">
<title>CHAPTER I.</title>

<p pid="1" id="singlequote.c1.p1">
  <s sid="1" id="singlequote.c1.s1">'Are you sure?' she said.</s>
  <s sid="2" id="singlequote.c1.s2">`Are you sure?' she said.</s>
</p>

<p pid="2" id="singlequote.c1.p2">
  <s sid="1" id="singlequote.c1.s1">Yet 'twas this very errand, namely, to fix with the _Bonaventure_'s men.</s>
  <s sid="2" id="singlequote.c1.s2">'It's H. O.'s fault as much as mine, anyhow.</s> <s sid="8" id="seekers.c4.s8">Why shouldn't he pay?'</s>
</p>

</div>
</div0>
        """))
        out_string = etree.tostring(out)
        self.assertEqual(re.findall(r'<qs/>.*?<qe/>', out_string), [
            "<qs/>'Are you sure?'<qe/>",
            "<qs/>`Are you sure?'<qe/>",
            '<qs/>\'It\'s H. O.\'s fault as much as mine, anyhow.</s> <s sid="8" id="seekers.c4.s8">Why shouldn\'t he pay?\'<qe/>',
        ])


if __name__ == '__main__':
    unittest.main()
