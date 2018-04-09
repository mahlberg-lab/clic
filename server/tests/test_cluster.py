import unittest

from clic.clicdb import ClicDb
from clic.cluster import cluster
from clic.errors import UserError

def cluster_catch_usererror(*args, **kwargs):
    out = []
    try:
        for x in cluster(*args, **kwargs):
            out.append(x)
    except UserError as e:
        out.append("UserError: %s" % e.message)
    return out

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

        # The default subset is all
        self.assertEqual(
            cluster_catch_usererror(cdb, corpora=['AgnesG']),
            cluster_catch_usererror(cdb, corpora=['AgnesG'], subset=['all']),
        )

    def test_shortsus5gram(self):
        cdb = ClicDb()

        with self.assertRaisesRegexp(UserError, "5gram"):
            out = []
            for x in cluster(cdb, clusterlength=[5], subset=['shortsus'], corpora=['AgnesG'], cutoff=[3]):
                out.append(x)

    def test_defaultcutoff(self):
        cdb = ClicDb()

        def cutoff(corpora, expected_min):
            try:
                min_freq = 9999999
                for x in cluster(cdb, clusterlength=[1], subset=['longsus'], corpora=corpora):
                    if isinstance(x, tuple) and x[1] < min_freq:
                        min_freq = x[1]
            except UserError as e:
                self.assertIn("frequency less than %d" % expected_min, e.message)
            self.assertEqual(min_freq, expected_min)

        cutoff(['AgnesG'], 1) # AgnesG is a book, and only one of them
        cutoff(['AgnesG', 'TTC'], 5) # 2 books has a higher frequency
        cutoff(['ntc'], 5) # a corpus has a higher frequency
