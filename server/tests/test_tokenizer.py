import unittest

from clic.tokenizer import types_from_string, parse_query


class TestTypesFromString(unittest.TestCase):
    # NB: The main tests for tokenizer are doctests in the module

    def test_main(self):
        # Empty string has no types in it
        self.assertEqual([x[0] for x in types_from_string("")], [])

        # A single token without whitespace is found
        self.assertEqual([x[0] for x in types_from_string("toot")], ["toot"])

    def test_offsets(self):
        # Crange returned
        self.assertEqual(list(types_from_string('I am a "cat"')), [
            ('i', 0, 1),
            ('am', 2, 4),
            ('a', 5, 6),
            ('cat', 8, 11)
        ])

        # Can add  an offset to all values
        self.assertEqual(list(types_from_string('I am a "cat"', offset=1000)), [
            ('i', 1000, 1001),
            ('am', 1002, 1004),
            ('a', 1005, 1006),
            ('cat', 1008, 1011)
        ])


class TestParseQuery(unittest.TestCase):
    # NB: The main tests for tokenizer are doctests in the module

    def test_main(self):
        # Underscores are escaped as well as asterisks being converted
        self.assertEqual(parse_query("""
            Moo* * oi*-nk b_th
        """), [
            "moo%", "%", "oi%", "nk", "b\\_th"
        ])
