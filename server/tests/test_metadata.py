import unittest

from clic.clicdb import ClicDb
from clic.metadata import get_corpus_structure, get_corpus_details

class Test_get_corpus_structure(unittest.TestCase):
    def test_call(self):
        """
        get_corpus_structure should return a sorted deep structure
        """
        out = get_corpus_structure(ClicDb())
        # Corpora in alphabetical order
        self.assertEqual([(x['id'], x['title']) for x in out], [
            (u'ntc', u'19th century reference corpus'),
            (u'ChiLit', u"Children's Literature"),  # NB: Alphabetical by title
            (u'dickens', u'Novels by Charles Dickens'),
            (u'Other', u'Other'),
        ])
        # Each corpora has some books
        for c in out:
            self.assertTrue(len(c['children']) > 0)
            if c['id'] == 'ntc':
                self.assertEqual(c['children'][0], dict(
                    id='AgnesG',
                    title='Agnes Grey',
                    author=u'Anne Bront\xeb',
                ))
                self.assertEqual(c['children'][-1], dict(
                    id='wh',
                    title='Wuthering Heights',
                    author=u'Emily Bront\xeb',
                ))
            if c['id'] == 'dickens':
                self.assertEqual(c['children'][0], dict(
                    id='TTC',
                    title='A Tale of Two Cities',
                    author=u'Charles Dickens',
                ))
                self.assertEqual(c['children'][-1], dict(
                    id='OCS',
                    title='The Old Curiosity Shop',
                    author=u'Charles Dickens',
                ))

class Test_get_corpus_details(unittest.TestCase):
    def test_call(self):
        """
        get_corpus_details should return a sorted deep structure
        """
        out = get_corpus_details(ClicDb())

        for c in out:
            self.assertTrue(len(c['children']) > 0)
        import pdb ; pdb.set_trace()
