import unittest

from clic import c3

class Test_get_corpus_structure(unittest.TestCase):
    def test_call(self):
        """
        get_corpus_structure should return a sorted deep structure
        """
        out = c3.get_corpus_structure()
        # Corpora in alphabetical order
        self.assertEqual([(x['id'], x['title']) for x in out], [
            (u'ntc', u'19th Century Novels'),
            (u'dickens', u'Novels by Charles Dickens'),
        ])
        # Each corpora has some books
        for c in out:
            self.assertTrue(len(c['children']) > 0)
            if c['id'] == 'ntc':
                self.assertEqual(c['children'][0], dict(
                    id='AgnesG',
                    title='Agnes Grey',
                ))
                self.assertEqual(c['children'][-1], dict(
                    id='wh',
                    title='Wuthering Heights',
                ))
            if c['id'] == 'dickens':
                self.assertEqual(c['children'][0], dict(
                    id='TTC',
                    title='A Tale of Two Cities',
                ))
                self.assertEqual(c['children'][-1], dict(
                    id='OCS',
                    title='The Old Curiosity Shop',
                ))
