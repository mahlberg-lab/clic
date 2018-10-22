import unittest

from clic.text import text

from .requires_postgresql import RequiresPostgresql


class TestText(RequiresPostgresql, unittest.TestCase):
    def test_fetch_by_book(self):
        """
        Fetch by book
        """
        cur = self.pg_cur()
        book_1 = self.put_book("""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)

        out = list(text(cur, [book_1], ['chapter.text']))
        self.assertEqual(out, [
            ('header', dict(content="""
            A man walked into a bar. "Ouch!", he said. It was an iron bar.
        """)),
            ['chapter.text', 0, 84, 1],
        ])
