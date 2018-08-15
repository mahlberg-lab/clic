from lxml import etree
import StringIO
import unittest

from clic.clicdb import ClicDb
from clic.text import text
from clic.errors import UserError

class TestText(unittest.TestCase):
    def test_fetch_by_book(self):
        """
        Fetch by book
        """
        cdb = ClicDb()
        out = [x for x in text(cdb, corpora=['AgnesG'])][1:]

        self.assertEqual(out[0][0], 'AgnesG')
        self.assertEqual(out[0][1], 1)

        # Fetch some details, proving we've parsed something useful
        tree = etree.parse(StringIO.StringIO(out[2][2]))
        self.assertEqual(tree.xpath('/div')[0].get('book'), 'AgnesG')
        self.assertEqual(tree.xpath('/div')[0].get('num'), '3')
