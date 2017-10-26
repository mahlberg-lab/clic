import re
import unittest
from lxml import etree

from sentences import sentences

class TestQuotes(unittest.TestCase):
    maxDiff = None

    def test_dotdotdotending(self):
        """Chapters ending with a ... should keep their final sentence"""
        out = sentences(etree.fromstring("""
<div0 id="canada" type="book" subcorpus="ChiLit" filename="canada.txt">
<!--NB: canada is a double-quote book -->

<title>The Settlers in Canada</title>
<author>Frederick Marryat</author>

<p pid="1" id="canada.c0.p1">absurd. Good Lord! mustn't a man ever--Here, give me some tobacco."...</p>
</div0>
        """))
        out_string = etree.tostring(out)
        self.assertTrue("""<s>Good Lord! mustn\'t a man ever--Here, give me some tobacco."...</s>""" in out_string)


if __name__ == '__main__':
    unittest.main()
