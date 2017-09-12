from lxml import etree
import StringIO
import unittest

from clic.clicdb import ClicDb
from clic.chapter import chapter

class TestChapter(unittest.TestCase):
    def test_chapter(self):
        cdb = ClicDb()
        tree = etree.parse(StringIO.StringIO(chapter(cdb, [1])))

        # Fetch some details, proving we've parsed something useful
        self.assertEqual(tree.xpath('/div')[0].get('book'), 'BH')
        self.assertEqual(tree.xpath('/div')[0].get('num'), '2')
