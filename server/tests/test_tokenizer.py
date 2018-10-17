import unittest

from clic.tokenizer import types_from_string, parse_query


class TestTypesFromString(unittest.TestCase):
    def test_main(self):
        # A type is lower-case, and "fancy" apostrophe's are normalised
        self.assertEqual([x[0] for x in types_from_string("""
            I am a café cat, don’t you k'now.
        """)], [
            "i", "am", "a", "cafe", "cat", "don't", "you", "k'now",
        ])

        # Numbers are types too
        self.assertEqual([x[0] for x in types_from_string("""
            Just my $0.02, but we're 12 minutes late.
        """)], [
            "just", "my", "0.02", "but", "we're", "12", "minutes", "late",
        ])

        # All punctuation is filtered out
        self.assertEqual([x[0] for x in types_from_string("""
            "I am a cat", they said, "hear me **roar**!".

            "...or at least mew".
        """)], [
            "i", "am", "a", "cat", "they", "said",
            "hear", "me", "roar",
            "or", "at", "least", "mew"
        ])

        # Unicode word-splitting doesn't combine hypenated words
        self.assertEqual([x[0] for x in types_from_string("""
            It had been a close and sultry day--one of the hottest of the
            dog-days--even out in the open country
        """)], [
            'it', 'had', 'been', 'a', 'close', 'and', 'sultry', 'day',
            'one', 'of', 'the', 'hottest', 'of', 'the', 'dog', 'days',
            'even', 'out', 'in', 'the', 'open', 'country',
        ])
        self.assertEqual([x[0] for x in types_from_string("""
            so many out-of-the-way things had happened lately
        """)], [
            'so', 'many', 'out', 'of', 'the', 'way',
            'things', 'had', 'happened', 'lately',
        ])

        # We strip underscores, which are considered part of a word in the unicode standard
        self.assertEqual([x[0] for x in types_from_string("""
            had some reputation as a _connoisseur_.
        """)], [
            "had", "some", "reputation", "as", "a", "connoisseur",
        ])

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
    def test_main(self):
        # We keep stars, but they get parsed into LIKE percent-marks. Underscores get escaped
        self.assertEqual(parse_query("""
            Moo* * oi*-nk b_th
        """), [
            "moo%", "%", "oi%", "nk", "b\\_th"
        ])
