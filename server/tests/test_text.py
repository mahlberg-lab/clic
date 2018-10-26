import unittest

from clic.text import text

from .requires_postgresql import RequiresPostgresql


class TestText(RequiresPostgresql, unittest.TestCase):
    def test_fetch_by_book(self):
        """
        Fetch by book
        """
        cur = self.pg_cur()
        self.put_books(ut_text_fetch="""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)

        out = list(text(cur, ["ut_text_fetch"], ['chapter.text']))
        self.assertEqual(out, [
            ('header', dict(content="""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)),
            ['chapter.text', 13, 75, 0],
        ])
