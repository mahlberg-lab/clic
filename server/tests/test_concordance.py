import unittest

from psycopg2._range import NumericRange

from clic.concordance import concordance, to_conc

from .requires_postgresql import RequiresPostgresql


class TestConcordance(RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_queries(self):
        """We can ask for nodes with many words, or many words separately"""
        cur = self.pg_cur()
        book_1 = self.put_book("""
‘Well!’ thought Alice to herself, ‘after such a fall as this, I shall
think nothing of tumbling down stairs! How brave they’ll all think me at
home! Why, I wouldn’t say anything about it, even if I fell off the top
of the house!’ (Which was very likely true.)
        """)

        # "f*ll *" matches fall or fell, and selects the word next to it
        out = simplify(concordance(cur, [book_1], q=['f*ll *']))
        self.assertEqual(out, [
            [book_1, 49, 'fall', 'as'],
            [book_1, 199, 'fell', 'off'],
        ])

        # We select the word before fall, and the word after fell
        out = simplify(concordance(cur, [book_1], q=['* fall', 'fell *']))
        self.assertEqual(out, [
            [book_1, 47, 'a', 'fall'],
            [book_1, 199, 'fell', 'off'],
        ])

        # Since we tokenise, punctuation in queries has no affect
        out = simplify(concordance(cur, [book_1], q=['"i--FELL--off!"']))
        self.assertEqual(out, [
            [book_1, 197, 'I', 'fell', 'off'],  # NB: I is capitalised since we return the token from the text, not the type
        ])

        # The type of quote (don’t vs don't) works, and get's normalised in output too
        out = simplify(concordance(cur, [book_1], q=["wouldn't"], contextsize=[1]))
        self.assertEqual(out, [
            [book_1, 157, 'I', '**', "wouldn't", '**', 'say'],
        ])

    def test_contextsize(self):
        """We can ask for different length contexts"""
        cur = self.pg_cur()
        book_1 = self.put_book("""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)

        # Fetch without concordance
        out = simplify(concordance(cur, [book_1], q=['bar']))
        self.assertEqual(out, [
            [book_1, 33, 'bar'],
            [book_1, 71, 'bar'],
        ])

        out = simplify(concordance(cur, [book_1], q=['bar'], contextsize=[2]))
        self.assertEqual(out, [
            [book_1, 33, 'into', 'a', '**', 'bar', '**', 'Ouch', 'he'],
            [book_1, 71, 'an', 'iron', '**', 'bar', '**'],  # NB: We have all 3 parts still, even though it's at the end
        ])


FULL_TEXT = 'A man walked into a bar. "Ouch!", he said. It was an iron bar.'
R_A = NumericRange(0, 1)
R_MAN = NumericRange(2, 5)
R_WALKED = NumericRange(6, 12)
R_INTO = NumericRange(13, 17)
R_A2 = NumericRange(18, 19)
R_BAR = NumericRange(20, 23)
R_OUCH = NumericRange(26, 31)
R_HE = NumericRange(34, 36)
R_SAID = NumericRange(37, 41)
R_IT = NumericRange(43, 45)
R_WAS = NumericRange(46, 49)
R_AN = NumericRange(50, 52)
R_IRON = NumericRange(53, 57)
R_BAR2 = NumericRange(58, 61)


class Test_to_conc(unittest.TestCase):
    def test_emptycontextsize(self):
        """0 context means we don't return the window lists"""
        self.assertEqual(to_conc(
            FULL_TEXT,
            [R_MAN, R_WALKED, R_INTO],
            [R_MAN, R_WALKED, R_INTO],
            0
        ), [
            ['man', ' ', 'walked', ' ', 'into', [0, 2, 4]],
        ])

    def test_windowsplit(self):
        """We split windows on nearest space"""
        self.assertEqual(to_conc(
            FULL_TEXT,
            [R_A, R_MAN, R_WALKED, R_INTO, R_A2, R_BAR],
            [R_MAN, R_WALKED, R_INTO],
            2
        ), [
            ['A', ' ', [0]],
            ['man', ' ', 'walked', ' ', 'into', [0, 2, 4]],
            [' ', 'a', ' ', 'bar', [1, 3]]
        ])
        self.assertEqual(to_conc(
            FULL_TEXT,
            [R_A2, R_BAR, R_OUCH, R_HE, R_SAID],
            [R_OUCH],
            2
        ), [
            ['a', ' ', 'bar', '.', ' ', [0, 2]],
            ['"', 'Ouch!', '",', [1]],
            [' ', 'he', ' ', 'said', [1, 3]],
        ])


def simplify(conc_results):
    """Turn concordance output into something slightly more human-readable"""
    out = []
    for r in conc_results:
        if len(r) == 3:
            out.append(
                [r[1][0], r[1][1]] +
                [r[0][i] for i in r[0][-1]]
            )
        else:  # Have context and node
            out.append(
                [r[3][0], r[3][1]] +
                [r[0][i] for i in r[0][-1]] + ['**'] +
                [r[1][i] for i in r[1][-1]] + ['**'] +
                [r[2][i] for i in r[2][-1]]
            )
    out.sort()
    return out
