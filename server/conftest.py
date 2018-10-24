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

    for book_name, content in books.items():
        rpg.put_book(content, book_name=book_name)
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


def format_cluster(cluster_results):
    """Drop footer, just include results"""
    return [x for x in cluster_results if x[0] != 'footer']

@pytest.fixture(autouse=True)
def doctest_extras(doctest_namespace):
    global rpg

    # Add extras to the namespace
    doctest_namespace['test_database'] = test_database
    doctest_namespace['format_conc'] = format_conc
    doctest_namespace['format_cluster'] = format_cluster
    yield doctest_namespace

    if rpg:
        rpg.tearDown()
        rpg.__class__.tearDownClass()
        rpg = None
