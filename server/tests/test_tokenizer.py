import unittest

from clic.tokenizer import parse_query


class Test_parse_query(unittest.TestCase):
    def test_call(self):
        self.assertEqual(
            parse_query(""),
            [])

        self.assertEqual(
            parse_query("the cat sat on the mat"),
            ["the", "cat", "sat", "on", "the", "mat"])

        self.assertEqual(
            parse_query('I don’t know. 90%pc of the time, "the cat* s*t on the *"'),
            ['i', 'don\'t', 'know', '90\\%pc', 'of', 'the', 'time', 'the', 'cat%', 's%t', 'on', 'the', '%'])
