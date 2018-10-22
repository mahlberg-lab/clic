# -*- coding: utf-8 -*-
import unittest

from clic.metadata import corpora, corpora_headlines


# TODO: Skip the lot
class Skip_corpora(unittest.TestCase):
    def skip_call(self):
        """
        corpora should return a sorted deep structure
        """
        out = corpora("ClicDb()")
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


# TODO: Skip the lot
class Skip_corpora_headlines(unittest.TestCase):
    def skip_call(self):
        """
        get_corpus_structure should return just corpus level detail
        """
        out = corpora_headlines("ClicDb()")
        self.assertEqual(
            [x['id'] for x in out],
            [u'dickens', u'ntc', u'ChiLit', u'Other'],
        )
        for x in out:
            self.assertEqual(x.keys(), ['title', 'id', 'word_count', 'book_count'])
