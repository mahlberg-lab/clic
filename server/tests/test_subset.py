import unittest

from clic.clicdb import ClicDb
from clic.subset import subset

class TestSubset(unittest.TestCase):
    def test_subset(self):
        cdb = ClicDb()
        out = [x for x in subset(cdb, ['AgnesG'], ['quote'])]
        self.assertTrue(len(out) > 0)
        # TODO: Actual tests
