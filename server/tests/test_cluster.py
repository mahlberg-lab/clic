import unittest

from clic.clicdb import ClicDb
from clic.cluster import cluster
from clic.errors import UserError

class TestCluster(unittest.TestCase):
    def test_cluster(self):
        cdb = ClicDb()
        out = []
        try:
            for x in cluster(cdb, clusterlength=[1], subset=['shortsus'], corpora=['AgnesG'], cutoff=[3]):
                out.append(x)
        except UserError as e:
            self.assertIn("frequency less than 3", e.message)
        self.assertEqual(len(out), 11)
