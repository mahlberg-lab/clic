import re
import unittest

from clic.clicdb import ClicDb
from clic.concordance import concordance

class TestConcordance(unittest.TestCase):
    def test_concordance(self):
        cdb = ClicDb()

        # Varying node size isn't supported
        with self.assertRaisesRegexp(ValueError, 'varying'):
            out = [x for x in concordance(
                cdb,
                corpora=['AgnesG'],
                subset=['quote'],
                q=['she was','hand'],
            )]

        # If they both match then words in the node match query
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was', 'she said'],
            contextsize=[5],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was', 'she:said']),
        )
        nodes = [":".join(x for x in line[1] if re.match(r'\w', x)) for line in out[1:]]
