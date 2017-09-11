import unittest

from clic.clicdb import ClicDb
from clic.cluster import cluster

class TestCluster(unittest.TestCase):
    def test_cluster(self):
        cdb = ClicDb()
        out = [x for x in cluster(
                cdb,
                clusterlength=[1],
                subset=['quote'], corpora=['AgnesG'],
        )]
        self.assertTrue(len(out) > 0)
        # TODO: Actual tests
