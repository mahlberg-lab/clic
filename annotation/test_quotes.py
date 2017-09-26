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

</div>
</div0>
        """))
        out_string = etree.tostring(out)
        # 2 of the quoted short-phrases have been picked out
        self.assertEqual(len(out_string.split('<qs/>')), 3)
        self.assertTrue('<qs/>"toilettes,"<qe/>' in out_string)
        self.assertTrue('<qs/>"passees,"<qe/>' in out_string)

    def test_single(self):
        out = quotes(etree.fromstring("""
<div0 id="singlequote" type="book" subcorpus="ChiLit" filename="canada.txt">

<div id="singlequote.1" subcorpus="ChiLit" booktitle="The Settlers in singlequote" book="singlequote" type="chapter" num="1">
<title>CHAPTER I.</title>

<p pid="1" id="singlequote.c1.p1">
  <s sid="1" id="singlequote.c1.s1">'Are you sure?' she said.</s>
  <s sid="1" id="singlequote.c1.s1">`Are you sure?' she said.</s>
</p>

</div>
</div0>
        """))
        out_string = etree.tostring(out)
        self.assertEqual(re.split(r'<qs/>|<qe/>', out_string)[1:], [
            "'Are you sure?'",
            ' she said.</s>\n  <s sid="1" id="singlequote.c1.s1">',
            "`Are you sure?'",
            ' she said.</s>\n</p>\n\n</div>\n</div0>'
        ])


if __name__ == '__main__':
    unittest.main()
