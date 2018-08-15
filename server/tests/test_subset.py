import re
import unittest

from clic.clicdb import ClicDb
from clic.subset import subset

def only_word(l):
    """Use final word-position-index to filter array"""
    return [l[i] for i in l[-1]]

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
        )][1:]
        out_context3 = [x for x in subset(
            cdb,
            corpora=['AgnesG'],
            subset=['longsus'],
            contextsize=[3],
        )][1:]
        out_context5 = [x for x in subset(
            cdb,
            corpora=['AgnesG'],
            subset=['longsus'],
            contextsize=[5],
        )][1:]

        # We don't include empty context columns
        self.assertEqual(
            set(["".join(l[0][:-1]) for l in out_nocontext]),
            set(["".join(l[1][:-1]) for l in out_context3]),
        )
        self.assertEqual(
            set(["".join(l[1][:-1]) for l in out_context3]),
            set(["".join(l[1][:-1]) for l in out_context5]),
        )

        # Context length is configurable
        self.assertEqual(
            set([len(only_word(l[0])) for l in out_context3]),
            set([3]),
        )
        self.assertEqual(
            set([len(only_word(l[2])) for l in out_context3]),
            set([3]),
        )
        self.assertEqual(
            set([len(only_word(l[0])) for l in out_context5]),
            set([3, 5]),  # NB: One of the subsets is at the end of the chapter
        )
        self.assertEqual(
            set([len(only_word(l[2])) for l in out_context5]),
            set([5]),
        )

    def test_emptychapter(self):
        """Can fetch subset=all, even if a chapter is empty"""
        cdb = ClicDb()

        # 60 is missing from alli, since it's empty
        rv = [x for x in subset(cdb, corpora=['alli'])]
        self.assertEqual([x[1][1] for x in rv[1:]], range(1,60) + [61])

        # We can also fetch nonquote subsets without falling over the empty chapter
        rv = [x for x in subset(cdb, corpora=['alli'], subset=['nonquote'])]
        self.assertEqual(len(rv), 2950)
        rv = [x for x in subset(cdb, corpora=['alli'], subset=['quote'])]
        self.assertEqual(len(rv), 5223)

    def test_subset(self):
        """Can choose what to return"""
        cdb = ClicDb()

        # The defaults are all/0
        self.assertEqual(
            [x for x in subset(cdb, corpora=['AgnesG'])],
            [x for x in subset(cdb, corpora=['AgnesG'], subset=['all'], contextsize=[0])],
        )

        # Agnes grey is returned in chunks of chapter
        self.assertEqual(
            len([x for x in subset(cdb,corpora=['AgnesG'])]),
            26,
        )

        # There's more long suspension though
        self.assertEqual(
            len([x for x in subset(cdb,corpora=['AgnesG'], subset=['longsus'])]),
            30,
        )

    def test_bookmetadata(self):
        """We can request book titles"""
        cdb = ClicDb()

        out = [x for x in subset(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['longsus'],
            contextsize=[0],
            metadata=['book_titles'],
        )]
        self.assertEqual(out[-1], ('footer', dict(book_titles=dict(
            AgnesG=(u'Agnes Grey', u'Anne Bront\xeb'),
            TTC=(u'A Tale of Two Cities', u'Charles Dickens'),
        ))))

    def test_querybyauthor(self):
        cdb = ClicDb()

        out = [x for x in subset(
            cdb,
            corpora=['author:Jane Austen'],
            subset=['quote'],
            contextsize=[0],
        )]
        self.assertEqual(
            set([x[1][0] for x in out[1:]]),
            set([u'emma', u'ladysusan', u'mansfield', u'northanger', u'persuasion', u'pride', u'sense']),
        )
