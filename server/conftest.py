import unittest
import pytest


rpg = None

def test_database(**books):
    """
    Create a test database, adding each book in the (books) dict
    """
    from tests.requires_postgresql import RequiresPostgresql

    class RPGWrapper(RequiresPostgresql, unittest.TestCase):
        """A fake unit test to use for creating databases in doctests"""
        pass

    global rpg

    RPGWrapper.setUpClass()
    rpg = RPGWrapper()

    rpg.put_books(**books)
    return rpg.pg_cur()


def format_conc(conc_results):
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


def just_metadata(conc_results):
    """Find the book metadata and return that"""
    import pprint

    for r in conc_results:
        # ('footer', footer)
        if isinstance(r, tuple) and r[0] == 'footer':
            # NB: pprint will sort dicts for us
            return pprint.pprint(r[1])
    raise ValueError("No footer")


def format_cluster(cluster_results):
    """Drop footer, just include results"""
    return [x for x in cluster_results if x[0] != 'footer']


def run_tagger(content, *fns):
    """Run a tagger function, return region tags that got applied"""
    def short_string(s):
        return s if len(s) < 40 else s[0:20] + '...' + s[-20:]

    book = dict(content=content)
    for fn in fns:
        fn(book)
    out = []
    for rclass in book.keys():
        if rclass == 'content':
            continue
        for r in book[rclass]:
            out.append((rclass,) + r + (short_string(content[r[0]:r[1]]),) )
    # Sort by start ascending, then end descending
    return sorted(out, key=lambda x: (x[1], -x[2], x[0]))


@pytest.fixture(autouse=True)
def doctest_extras(doctest_namespace):
    global rpg

    # Add extras to the namespace
    doctest_namespace['test_database'] = test_database
    doctest_namespace['format_conc'] = format_conc
    doctest_namespace['just_metadata'] = just_metadata
    doctest_namespace['format_cluster'] = format_cluster
    doctest_namespace['run_tagger'] = run_tagger
    yield doctest_namespace

    if rpg:
        rpg.tearDown()
        rpg.__class__.tearDownClass()
        rpg = None
