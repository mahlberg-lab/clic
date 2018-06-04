from lxml import etree
import StringIO
import unittest

from clic.clicdb import ClicDb
from clic.chapter import chapter
from clic.errors import UserError

class TestChapter(unittest.TestCase):
    def test_fetch_by_chapter_id(self):
        """
        Legacy interface we ought preserve
        """
        cdb = ClicDb()
        tree = etree.parse(StringIO.StringIO(chapter(cdb, chapter_id=[1])))

        # Fetch some details, proving we've parsed something useful
        self.assertEqual(tree.xpath('/div')[0].get('book'), 'BH')
        self.assertEqual(tree.xpath('/div')[0].get('num'), '2')

    def test_fetch_by_bookchapter(self):
        """
        Fetch by book/chapter
        """
        cdb = ClicDb()
        tree = etree.parse(StringIO.StringIO(chapter(cdb, book=['AgnesG'], chapter_num=['3'])))

        # Fetch some details, proving we've parsed something useful
        self.assertEqual(tree.xpath('/div')[0].get('book'), 'AgnesG')
        self.assertEqual(tree.xpath('/div')[0].get('num'), '3')

        with self.assertRaisesRegexp(UserError, "exist"):
            tree = etree.parse(StringIO.StringIO(chapter(cdb, book=['AgnesG'], chapter_num=['999999'])))
