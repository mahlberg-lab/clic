import unittest

from psycopg2._range import NumericRange

from clic.concordance import concordance, to_conc, parse_query

from .requires_postgresql import RequiresPostgresql


class TestConcordance(RequiresPostgresql, unittest.TestCase):
    # NB: The main tests for Concordance are doctests in the module
    maxDiff = None

    def test_contextsize(self):
        """We can ask for different length contexts"""
        cur = self.pg_cur()
        self.put_books(ut_conc_contextsize_1="""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)

        # Fetch without concordance
        out = simplify(concordance(cur, ['ut_conc_contextsize_1'], q=['bar']))
        self.assertEqual(out, [
            ['ut_conc_contextsize_1', 33, 'bar'],
            ['ut_conc_contextsize_1', 71, 'bar'],
        ])

        out = simplify(concordance(cur, ['ut_conc_contextsize_1'], q=['bar'], contextsize=[2]))
        self.assertEqual(out, [
            ['ut_conc_contextsize_1', 33, 'into', 'a', '**', 'bar', '**', 'Ouch', 'he'],
            ['ut_conc_contextsize_1', 71, 'an', 'iron', '**', 'bar', '**'],  # NB: We have all 3 parts still, even though it's at the end
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

    def test_nonode(self):
        """Nothing sensible to do without a node atm"""
        with self.assertRaises(NotImplementedError):
            to_conc(
                FULL_TEXT,
                [R_A, R_MAN, R_WALKED, R_INTO, R_A2, R_BAR],
                [],
                2
            )

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


class TestParseQuery(unittest.TestCase):
    # NB: The main tests for tokenizer are doctests in the module

    def test_main(self):
        # Underscores are escaped as well as asterisks being converted
        self.assertEqual(parse_query("""
            Moo* * oi*-nk b_th
        """), [
            "moo%", "%", "oi%-nk", "b\\_th"
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
