import re
import unittest

from clic.clicdb import ClicDb
from clic.concordance import concordance
from clic.errors import UserError

class TestConcordance(unittest.TestCase):
    def test_concordance(self):
        cdb = ClicDb()

        # If they both match then words in the node match query
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was', 'she said'],
            contextsize=[5],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was', 'she:said']),
        )
        nodes = [":".join(x for x in line[1][:-1] if re.match(r'\w', x)) for line in out[1:]]

    def test_contextsize(self):
        """Contextsize should be configurable"""
        cdb = ClicDb()

        # No context, we skip those columns
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was'],
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
            q=['she was'],
            contextsize=[3],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['yes:replied:she','she:i:saw','detestable:i:wish','in:their:houses','can:well:believe','williamson:brown:said','her:how:mistaken']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['artful:too:but','sure:no:gentleman','in:her:fears',"sure:she:didn't",'dead:she:then','giddy:and:vain','at:paris:when']),
        )

        # Can vary size
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was'],
            contextsize=[1],
        )]
        self.assertEqual(
            set([":".join([x.lower() for x in line[0][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['said','wish','mistaken','houses','she','believe','saw'])
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[1][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['she:was']),
        )
        self.assertEqual(
            set([":".join([x.lower() for x in line[2][:-1] if re.match(r'\w', x)]) for line in out[1:]]),
            set(['giddy','sure','artful','at','in','dead'])
        )

        # Can even vary query length
        she_was_out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was'],
            contextsize=[1],
        )]
        hand_out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['hand'],
            contextsize=[1],
        )]
        out = [x for x in concordance(
            cdb,
            corpora=['AgnesG'],
            subset=['quote'],
            q=['she was', 'hand'],
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
