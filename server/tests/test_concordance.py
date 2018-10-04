# -*- coding: utf-8 -*-
import re
import unittest

from clic.clicdb import ClicDb
from clic.concordance import concordance


class TestConcordance(unittest.TestCase):
    def test_concordance(self):
        cdb = ClicDb()

        # If they both match then words in the node match query
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was', u'she said'],
            contextsize=[5],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was', 'she:said']),
        )

    def test_contextsize(self):
        """Contextsize should be configurable"""
        cdb = ClicDb()

        # No context, we skip those columns
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
        )]
        # NB: Node now in first row
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was']),
        )

        # Context adds columns either side
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[3],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['yes:replied:she', 'she:i:saw', 'detestable:i:wish', 'in:their:houses', 'can:well:believe', 'williamson:brown:said', 'her:how:mistaken']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['artful:too:but', 'sure:no:gentleman', 'in:her:fears', "sure:she:didn't", 'dead:she:then', 'giddy:and:vain', 'at:paris:when']),
        )

        # Can vary size
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[1],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['said', 'wish', 'mistaken', 'houses', 'she', 'believe', 'saw'])
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['giddy', 'sure', 'artful', 'at', 'in', 'dead'])
        )

        # Can even vary query length
        she_was_out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[1],
        )]
        hand_out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'hand'],
            contextsize=[1],
        )]
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=[u'she was', u'hand'],
            contextsize=[1],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in she_was_out[1:]] +
                [":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in hand_out[1:]])
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in she_was_out[1:]] +
                [":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in hand_out[1:]])
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in she_was_out[1:]] +
                [":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in hand_out[1:]])
        )

    def test_unidecode(self):
        """We mush down quotes in queries to ascii characters"""
        cdb = ClicDb()

        out_fancy = [x for x in concordance(
            cdb,
            corpora=['BH'],
            subset=['quote'],
            q=[u'I don’t know'],
        )]
        out_ascii = [x for x in concordance(
            cdb,
            corpora=['BH'],
            subset=['quote'],
            q=[u"I don't know"],
        )]
        # Queries both produce results and are equivalent
        self.assertTrue(len(out_ascii) > 0)
        self.assertEqual(out_fancy, out_ascii)

    def test_escaping(self):
        """We escape double quotes into something that at least doesn't cause errors"""
        cdb = ClicDb()

        out = [x for x in concordance(
            cdb,
            corpora=['BH'],
            subset=['quote'],
            q=[u'"girls are"'],
        )]
        self.assertEqual(
            ["".join(x[0][:-1]) for x in out[1:]],
            [u' girls are', u' girls are.'],
        )

    def test_bookmetadata(self):
        """We can request book titles"""
        cdb = ClicDb()

        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['book_titles'],
        )]
        self.assertEqual(out[-1], ('footer', dict(book_titles=dict(
            AgnesG=(u'Agnes Grey', u'Anne Bront\xeb'),
            TTC=(u'A Tale of Two Cities', u'Charles Dickens'),
        ))))

        # chapter_start can also be got
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['book_titles', 'chapter_start'],
        )]
        self.assertEqual(out[-1], ('footer', dict(book_titles=dict(
            AgnesG=(u'Agnes Grey', u'Anne Bront\xeb'),
            TTC=(u'A Tale of Two Cities', u'Charles Dickens'),
        ), chapter_start=dict(
            AgnesG={
                1: 0, 2: 4424, 3: 7130, 4: 11363, 5: 14529, 6: 16855, 7: 18933, 8: 24573, 9: 25458, 10: 26959,
                11: 28722, 12: 34349, 13: 35799, 14: 38319, 15: 43312, 16: 45815, 17: 47159, 18: 50967, 19: 54240,
                20: 55417, 21: 57388, 22: 59672, 23: 62600, 24: 64042, 25: 66188,
                '_end': 68197,
            },
            TTC={
                1: 0, 2: 1005, 3: 3023, 4: 4643, 5: 9055, 6: 13228, 7: 17372, 8: 19771, 9: 22159,
                10: 27022, 11: 29272, 12: 31407, 13: 35983, 14: 39315, 15: 41164, 16: 45238, 17: 48204, 18: 49600, 19: 52171,
                20: 54012, 21: 57905, 22: 62130, 23: 66001, 24: 67910, 25: 70325, 26: 73113, 27: 74462, 28: 78726, 29: 80762,
                30: 83390, 31: 87821, 32: 92057, 33: 94547, 34: 96274, 35: 98413, 36: 100694, 37: 103196, 38: 105044, 39: 109720,
                40: 114373, 41: 120167, 42: 121625, 43: 124833, 44: 129234, 45: 133871,
                '_end': 136100,
            }
        ))))

        # word_count
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG', 'TTC'],
            subset=['quote'],
            q=[u'she was'],
            contextsize=[0],
            metadata=['word_count_all', 'word_count_quote'],
        )]
        self.assertEqual(out[-1], ('footer', dict(
            word_count_all=dict(AgnesG=68197, TTC=136100),
            word_count_quote=dict(AgnesG=21986, TTC=48557),
        )))

    def test_querybyauthor(self):
        cdb = ClicDb()

        out = [x for x in concordance(
            cdb,
            corpora=['author:Jane Austen'],
            subset=['quote'],
            q=[u'she was', u'she said'],
            contextsize=[0],
        )]
        self.assertEqual(
            set([x[1][0] for x in out[1:]]),
            set([u'emma', u'ladysusan', u'mansfield', u'northanger', u'persuasion', u'pride', u'sense']),
        )
