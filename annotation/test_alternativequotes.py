import unittest
from lxml import etree

from quotes import quotes
from alternativequotes import alternativequotes

class TestAlternativeQuotes(unittest.TestCase):
    def test_singlequote(self):
        out_quotes = quotes(etree.fromstring("""
<div0 id="singlequote" type="book" subcorpus="ChiLit" filename="canada.txt">
  <div>
    <title>CHAPTER I.</title>

    <p pid="1" id="singlequote.c1.p1">
      <s sid="1" id="singlequote.c1.s1">'Please, sir, can you tell me which gentleman of your party wears a bright blue dress-coat, with "a gilt" button with "P. C." on it?'</s>
    </p>

  </div>
</div0>
        """))
        out_quotestring = etree.tostring(out_quotes)
        out_altquotes = alternativequotes(etree.fromstring(etree.tostring(out_quotes)))
        out_string = etree.tostring(out_altquotes)

        # Note we're still testing for quotes, which "a gilt" isn't. (P.C. probably isn't either, but meh)
        self.assertTrue("""
<qs/>'Please, sir, can you tell me which gentleman of your party wears a bright blue dress-coat, with "a gilt" button with <alt-qs/>"P. C."<alt-qe/> on it?'<qe/>
        """.strip() in out_string)

    def test_backtickquote(self):
        '''Backtick quotes are detected as single quotes'''
        out_quotes = quotes(etree.fromstring("""
<div0 id="canada" type="book" subcorpus="ChiLit" filename="canada.txt">
<!--NB: canada is a double-quote book -->

<title>The Settlers in Canada</title>
<author>Frederick Marryat</author>
<p pid="1" id="canada.c0.p1"><s>[Illustration:</s> <s>BEE-HUNTING.]</s> </p>

<div id="canada.1" subcorpus="ChiLit" booktitle="The Settlers in Canada" book="canada" type="chapter" num="1">
<title>CHAPTER I.</title>

<p pid="1" id="canada.c1.p1"><s sid="1" id="canada.c1.s1">"There's the thing," said Hugh.  "When Miss Harold is here, I can think of nothing but fifty-six.  It seems to sound in my ears, as if somebody spoke it, `four times seven is fifty-six.' So there."</s></p>

</div>
</div0>
        """))
        out_quotestring = etree.tostring(out_quotes)
        out_altquotes = alternativequotes(etree.fromstring(etree.tostring(out_quotes)))
        out_string = etree.tostring(out_altquotes)
        self.assertTrue(
          """<qs/>"There's the thing,"<qe/> said Hugh.  """ +
          """<qs/>"When Miss Harold is here, I can think of nothing but fifty-six.  """ +
          """It seems to sound in my ears, as if somebody spoke it, """ +
          """<alt-qs/>`four times seven is fifty-six.'<alt-qe/> So there."<qe/>""" in out_string)


if __name__ == '__main__':
    unittest.main()
