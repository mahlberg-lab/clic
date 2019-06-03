import unittest

from clic.subset import subset

from .requires_postgresql import RequiresPostgresql
from .test_concordance import simplify


class TestSubset(RequiresPostgresql, unittest.TestCase):
    # NB: The main tests for Subset are doctests in the module
    maxDiff = None

    def test_subset(self):
        cur = self.pg_cur()
        self.put_books(ut_subs_emptyregion="""
            "What do you have to say to that then?", I asked. ". . ."
        """)

        # We can fetch regions without any tokens in
        out = simplify(subset(cur, ['ut_subs_emptyregion'], subset=['quote']))
        self.assertEqual(out, [
            ['ut_subs_emptyregion', 13, 'What', 'do', 'you', 'have', 'to', 'say', 'to', 'that', 'then'],
            # NB: Empty quote not included
        ])

        out = simplify(subset(cur, ['ut_subs_emptyregion'], subset=['quote'], contextsize=[1]))
        self.assertEqual(out, [
            ['ut_subs_emptyregion', 13, '**', 'What', 'do', 'you', 'have', 'to', 'say', 'to', 'that', 'then', '**', 'I', 'asked'],
            # NB: Empty quote not included
        ])
