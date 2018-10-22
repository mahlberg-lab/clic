import unittest

from clic.subset import subset


def only_word(l):
    """Use final word-position-index to filter array"""
    return [l[i] for i in l[-1]]


# TODO: Skip old API tests
class SkipSubset(unittest.TestCase):
    def skip_subset(self):
        cdb = "ClicDB()"
        out = [x for x in subset(cdb, ['AgnesG'], ['quote'])]
        self.assertTrue(len(out) > 0)
        # TODO: Actual tests

    def skip_contextsize(self):
        """Contextsize should be configurable"""
        cdb = "ClicDB()"

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

    def skip_emptychapter(self):
        """Can fetch subset=all, even if a chapter is empty"""
        cdb = "ClicDB()"

        # 60 is missing from alli, since it's empty
        rv = [x for x in subset(cdb, corpora=['alli'])]
        self.assertEqual([x[1][1] for x in rv[1:]], range(1, 60) + [61])

        # We can also fetch nonquote subsets without falling over the empty chapter
        rv = [x for x in subset(cdb, corpora=['alli'], subset=['nonquote'])]
        self.assertEqual(len(rv), 2950)
        rv = [x for x in subset(cdb, corpora=['alli'], subset=['quote'])]
        self.assertEqual(len(rv), 5223)

    def skip_subsetcontext(self):
        """Can choose what to return"""
        cdb = "ClicDB()"

        # The defaults are all/0
        self.assertEqual(
            [x for x in subset(cdb, corpora=['AgnesG'])],
            [x for x in subset(cdb, corpora=['AgnesG'], subset=['all'], contextsize=[0])],
        )

        # Agnes grey is returned in chunks of chapter
        self.assertEqual(
            len([x for x in subset(cdb, corpora=['AgnesG'])]),
            26,
        )

        # There's more long suspension though
        self.assertEqual(
            len([x for x in subset(cdb, corpora=['AgnesG'], subset=['longsus'])]),
            30,
        )

    def skip_bookmetadata(self):
        """We can request book titles"""
        cdb = "ClicDB()"

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
