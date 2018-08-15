# -*- coding: utf-8 -*-
import unittest

from clic.clicdb import ClicDb
from clic.metadata import get_corpus_structure

class Test_get_corpus_structure(unittest.TestCase):
    def test_call(self):
        """
        get_corpus_structure should return a sorted deep structure
        """
        out = get_corpus_structure(ClicDb())
        # Corpora in corpus_order order
        self.assertEqual([(x['id'], x['title']) for x in out], [
            (u'dickens', u'Dickens\u2019s Novels'),
            (u'ntc', u'19\u1d57\u02b0 Century Reference Corpus'),
            (u'ChiLit', u"19\u1d57\u02b0 Century Children\u2019s Literature"),
            (u'Other', u'Other'),
            (None, 'All books by author'),
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
