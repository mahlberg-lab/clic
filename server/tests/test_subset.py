import re
import unittest

from clic.clicdb import ClicDb
from clic.subset import subset

def only_word(l):
    return [x for x in l if re.match(r'\w', x)]

class TestSubset(unittest.TestCase):
    def test_subset(self):
        cdb = ClicDb()
        out = [x for x in subset(cdb, ['AgnesG'], ['quote'])]
        self.assertTrue(len(out) > 0)
        # TODO: Actual tests

    def test_contextsize(self):
        """Contextsize should be configurable"""
        cdb = ClicDb()

        out_nocontext = [x for x in subset(
            cdb,
            corpora=['AgnesG'],
            subset=['longsus'],
            contextsize=[0],
        )]
        out_context3 = [x for x in subset(
            cdb,
            corpora=['AgnesG'],
            subset=['longsus'],
            contextsize=[3],
        )]
        out_context5 = [x for x in subset(
            cdb,
            corpora=['AgnesG'],
            subset=['longsus'],
            contextsize=[5],
        )]

        # We don't include empty context columns
        self.assertEqual(
            set(["".join(l[0]) for l in out_nocontext[1:]]),
            set(["".join(l[1]) for l in out_context3[1:]]),
        )
        self.assertEqual(
            set(["".join(l[1]) for l in out_context3[1:]]),
            set(["".join(l[1]) for l in out_context5[1:]]),
        )

        # Context length is configurable
        self.assertEqual(
            set([len(only_word(l[0])) for l in out_context3[1:]]),
            set([3]),
        )
        self.assertEqual(
            set([len(only_word(l[2])) for l in out_context3[1:]]),
            set([3]),
        )
        self.assertEqual(
            set([len(only_word(l[0])) for l in out_context5[1:]]),
            set([3, 5]),  # NB: One of the subsets is at the end of the chapter
        )
        self.assertEqual(
            set([len(only_word(l[2])) for l in out_context5[1:]]),
            set([5]),
        )
