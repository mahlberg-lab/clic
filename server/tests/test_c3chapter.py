import re
import unittest
from lxml import etree

from clic.c3chapter import Chapter


def word_indices(l):
    """Return indicies of an array which contain word-y strings"""
    out = []
    for i, x in enumerate(l):
        if re.match(r'\w', x):
            out.append(i)
    return out


class TestChapter(unittest.TestCase):
    def test_get_conc_line(self):
        dom = etree.fromstring('''
            <div book="0" num="0">
              <toks>
                <qs/><n>'</n><w>You'll</w><n> </n><w>BOTH</w><n> </n><w>stay</w><n> </n><w>while</w><n> </n>
                <w>this</w><n> </n><w>shower</w><n> </n><w>gets</w><n> </n><w>owered</w><qe/>

                <sls/><n>,'</n><n> </n><w>said</w><n> </n><w>Nancy</w><n>,</n><n> </n><w>as</w><n> </n><w>she</w><n> </n>
                <w>stirred</w><n> </n><w>the</w><n> </n><w>fire</w><n>,</n><n> </n><w>and</w><n> </n><w>placed</w><n> </n>
                <w>another</w><n> </n><w>chair</w><n> </n><w>beside</w><n> </n><w>it</w><sle/>

                <qs/><n>;</n><n> </n><n>'</n><w>what</w><n>!</n><w>there's</w><n> </n><w>room</w><n> </n>
                <w>for</w><n> </n><w>all</w><n>.'</n></toks>
            </div>
        ''')
        toks = dom.xpath("/div/descendant::*[self::n or self::w]")
        ch = Chapter(
            tuple(n.text for n in toks),
            tuple(i for i, n in enumerate(toks) if n.tag == 'w'),
            'parp', 1
        )

        def conc_line(*args):
            out = []
            for l in ch.get_conc_line(*args):
                # Check the word indices match
                self.assertEqual(word_indices(l[:-1]), l[-1])
                out.append(l[:-1])
            return out

        self.assertEqual(conc_line(0, 3, 0), [
            ("'", "You'll", ' ', 'BOTH', ' ', 'stay'),
        ])
        self.assertEqual(conc_line(3, 3, 0), [
            (' ', 'while', ' ', 'this', ' ', 'shower'),
        ])

        # We prefer to split the node on the nearest space
        self.assertEqual(conc_line(0, 8, 0), [
            ("'", "You'll", ' ', 'BOTH', ' ', 'stay', ' ', 'while', ' ', 'this', ' ', 'shower', ' ', 'gets', ' ', 'owered', ",'"),
        ])
        self.assertEqual(conc_line(0, 8, 3), [
            (),
            ("'", "You'll", ' ', 'BOTH', ' ', 'stay', ' ', 'while', ' ', 'this', ' ', 'shower', ' ', 'gets', ' ', 'owered', ",'"),
            (' ', 'said', ' ', 'Nancy', ',', ' ', 'as'),
        ])
        self.assertEqual(conc_line(3, 5, 3), [
            ("You'll", ' ', 'BOTH', ' ', 'stay'),
            (' ', 'while', ' ', 'this', ' ', 'shower', ' ', 'gets', ' ', 'owered', ",'"),
            (' ', 'said', ' ', 'Nancy', ',', ' ', 'as'),
        ])

        # We can request a zero-length node
        self.assertEqual(conc_line(3, 0, 3), [
            ("You'll", ' ', 'BOTH', ' ', 'stay', ' '),
            (),
            ('while', ' ', 'this', ' ', 'shower'),
        ])

        # A concordance starting at the end is dumb, but certainly possible as chapters end with <qs/>
        self.assertEqual(conc_line(22, 3, 0), [
            # NB: There's no space between there's and the previous word, just exclamation.
            ('!', "there's", ' ', 'room', ' ', 'for'),
        ])
        self.assertEqual(conc_line(23, 3, 0), [
            (' ', 'room', ' ', 'for', ' ', 'all', ".'"),
        ])
        self.assertEqual(conc_line(24, 3, 0), [
            (' ', 'for', ' ', 'all', ".'"),
        ])
        self.assertEqual(conc_line(25, 3, 0), [
            (' ', 'all', ".'"),
        ])
        self.assertEqual(conc_line(26, 3, 0), [
            (),
        ])
        self.assertEqual(conc_line(26, 3, 3), [
            ('room', ' ', 'for', ' ', 'all', ".'"),
            (),
            (),
        ])
