# -*- coding: utf-8 -*-
import unittest

from clic.metadata import corpora, corpora_headlines

from .requires_postgresql import RequiresPostgresql


class Test_corpora(RequiresPostgresql, unittest.TestCase):
    def test_call(self):
        """
        corpora should return a sorted deep structure
        """
        self.put_books(
            ut_corpora_1="""
The book ut_corpora_1
Bob Book

A man walked into a bar.
            """.strip(),
            ut_corpora_2="""
The book ut_corpora_2
Bob Book

"Ouch!", he said.
            """.strip(),
            ut_corpora_3="""
The book ut_corpora_3
Jane Journal

It was an iron bar
            """.strip(),
        )
        self.put_corpora(
            dict(name="zcorp", contents=['ut_corpora_3', 'ut_corpora_2']),
            dict(name="acorp", contents=['ut_corpora_1']),
        )
        out = corpora(self.pg_cur())
        self.assertEqual(out, dict(corpora=[
            {
                "id": "corpus:zcorp",  # NB: This comes first since they are in ordering order
                "title": "UT corpus zcorp",
                "children": [
                    {
                        "id": "ut_corpora_2",
                        "title": "The book ut_corpora_2",
                        "author": "Bob Book"
                    },
                    {
                        "id": "ut_corpora_3",
                        "title": "The book ut_corpora_3",
                        "author": "Jane Journal"
                    },
                ]
            },
            {
                "id": "corpus:acorp",
                "title": "UT corpus acorp",
                "children": [
                    {
                        "id": "ut_corpora_1",
                        "title": "The book ut_corpora_1",
                        "author": "Bob Book"
                    },
                ]
            },
            {  # NB: We also group by author, and give total counts
                "id": None,
                "title": "All books by author",
                "children": [
                    {
                        "id": "author:Bob Book",
                        "title": "Bob Book",
                        "author": "2 books"
                    },
                    {
                        "id": "author:Jane Journal",
                        "title": "Jane Journal",
                        "author": "1 books"
                    },
                ]
            },
        ]))


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
