# -*- coding: utf-8 -*-
import unittest

from clic.metadata import OLD_ALIASES, corpora, corpora_headlines

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
        self.assertEqual(out['corpora'], [
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
        ])
        self.assertEqual(out['aliases'], OLD_ALIASES)


class Test_corpora_headlines(RequiresPostgresql, unittest.TestCase):
    maxDiff = None

    def test_call(self):
        """
        corpora/headlines should return counts for all corpuses
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
        out = corpora_headlines(self.pg_cur())
        self.assertEqual(out, dict(data=[
            {
                "id": "corpus:zcorp",
                "title": "UT corpus zcorp",
                "book_count": 2,
                "word_count": 8,
            },
            {
                "id": "corpus:acorp",
                "title": "UT corpus acorp",
                "book_count": 1,
                "word_count": 6,
            },
        ]))
