import re
import unittest

from clic.clicdb import ClicDb
from clic.word_count import word_count

class TestWordCount(unittest.TestCase):
    def test_word_count(self):
        cdb = ClicDb()

        out = [x for x in word_count(cdb, ['AgnesG'], ['quote'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 21986],
        ])

        out = [x for x in word_count(cdb, ['AgnesG'], ['quote', 'longsus'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 21986, 397],
        ])

        # Order of output matches input
        out = [x for x in word_count(cdb, ['AgnesG'], ['longsus', 'quote'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 397, 21986],
        ])

        # All isn't affected by what other values you fetch
        out = [x for x in word_count(cdb, ['AgnesG'], ['longsus', 'quote', 'all'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 397, 21986, 68197],
        ])
        out = [x for x in word_count(cdb, ['AgnesG'], ['all', 'longsus'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 68197, 397],
        ])

        # Multiple books, in same and different corpora
        out = [x for x in word_count(cdb, ['AgnesG', 'alli', 'BH'], ['all', 'longsus'])]
        self.assertEqual(out[1:], [
            [u'AgnesG', 68197, 397],
            [u'BH', 354362, 7911],
            [u'alli', 257184, 1091],
        ])

