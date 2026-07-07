import os
import tempfile
import unittest

from clic.db.corpus import add_book_to_corpus, put_corpus

from .requires_postgresql import RequiresPostgresql


class Test_put_corpus(RequiresPostgresql, unittest.TestCase):
    def _corpus_id(self, cur, name):
        cur.execute("SELECT corpus_id FROM corpus WHERE name = %s", (name,))
        (corpus_id,) = cur.fetchone()
        return corpus_id

    def test_insert(self):
        """put_corpus inserts a new row"""
        cur = self.pg_cur()
        put_corpus(cur, dict(
            name="ut_corp_insert",
            title="UT corpus insert",
            ordering=3,
        ))

        cur.execute("""
            SELECT name, title, ordering, carousel_image
              FROM corpus WHERE name = %s
        """, ("ut_corp_insert",))
        self.assertEqual(cur.fetchone(), (
            "ut_corp_insert", "UT corpus insert", 3, None,
        ))

    def test_update_existing(self):
        """Re-inserting with same name updates title/ordering, keeps corpus_id"""
        cur = self.pg_cur()
        put_corpus(cur, dict(
            name="ut_corp_update",
            title="initial title",
            ordering=1,
        ))
        first_id = self._corpus_id(cur, "ut_corp_update")
        put_corpus(cur, dict(
            name="ut_corp_update",
            title="updated title",
            ordering=9,
        ))
        second_id = self._corpus_id(cur, "ut_corp_update")
        self.assertEqual(first_id, second_id)

        cur.execute("""
            SELECT title, ordering FROM corpus WHERE corpus_id = %s
        """, (first_id,))
        self.assertEqual(cur.fetchone(), ("updated title", 9))

    def test_carousel_image_from_path(self):
        """carousel_image_path is read in as carousel_image bytes"""
        cur = self.pg_cur()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"\x89PNG\r\nfake-image-bytes")
            image_path = f.name
        try:
            put_corpus(cur, dict(
                name="ut_corp_image",
                title="UT corpus image",
                ordering=0,
                carousel_image_path=image_path,
            ))
        finally:
            os.unlink(image_path)

        cur.execute("""
            SELECT carousel_image FROM corpus WHERE name = %s
        """, ("ut_corp_image",))
        (image,) = cur.fetchone()
        self.assertEqual(bytes(image), b"\x89PNG\r\nfake-image-bytes")

    def test_no_carousel_image(self):
        """An absent / falsy carousel_image_path results in NULL"""
        cur = self.pg_cur()

        # Key missing entirely
        put_corpus(cur, dict(
            name="ut_corp_noimg_a",
            title="UT corpus no image a",
            ordering=0,
        ))
        cur.execute("SELECT carousel_image FROM corpus WHERE name = %s", ("ut_corp_noimg_a",))
        self.assertEqual(cur.fetchone(), (None,))

        # Key present but None
        put_corpus(cur, dict(
            name="ut_corp_noimg_b",
            title="UT corpus no image b",
            ordering=0,
            carousel_image_path=None,
        ))
        cur.execute("SELECT carousel_image FROM corpus WHERE name = %s", ("ut_corp_noimg_b",))
        self.assertEqual(cur.fetchone(), (None,))

    def test_example_url(self):
        """example_url is stored, and clic-fiction.com hostname stripped"""
        cur = self.pg_cur()

        # Full clic-fiction.com URL is rewritten to a relative path
        put_corpus(cur, dict(
            name="ut_corp_url_full",
            title="UT corpus url full",
            ordering=0,
            example_url="https://clic-fiction.com/concordance?corpora=dickens",
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_full",))
        self.assertEqual(cur.fetchone(), ("/concordance?corpora=dickens",))

        # A URL to another host is left alone
        put_corpus(cur, dict(
            name="ut_corp_url_other",
            title="UT corpus url other",
            ordering=0,
            example_url="https://example.com/somewhere",
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_other",))
        self.assertEqual(cur.fetchone(), ("https://example.com/somewhere",))

        # An already-relative URL is left alone
        put_corpus(cur, dict(
            name="ut_corp_url_rel",
            title="UT corpus url rel",
            ordering=0,
            example_url="/concordance?corpora=other",
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_rel",))
        self.assertEqual(cur.fetchone(), ("/concordance?corpora=other",))

    def test_no_example_url(self):
        """An absent / falsy example_url results in NULL"""
        cur = self.pg_cur()

        # Key missing entirely
        put_corpus(cur, dict(
            name="ut_corp_nourl_a",
            title="UT corpus no url a",
            ordering=0,
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_nourl_a",))
        self.assertEqual(cur.fetchone(), (None,))

        # Key present but None
        put_corpus(cur, dict(
            name="ut_corp_nourl_b",
            title="UT corpus no url b",
            ordering=0,
            example_url=None,
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_nourl_b",))
        self.assertEqual(cur.fetchone(), (None,))

    def test_update_example_url(self):
        """Re-inserting overwrites example_url, including clearing to NULL"""
        cur = self.pg_cur()
        put_corpus(cur, dict(
            name="ut_corp_url_upd",
            title="UT corpus url upd",
            ordering=0,
            example_url="https://clic-fiction.com/first",
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_upd",))
        self.assertEqual(cur.fetchone(), ("/first",))

        put_corpus(cur, dict(
            name="ut_corp_url_upd",
            title="UT corpus url upd",
            ordering=0,
            example_url="https://clic-fiction.com/second",
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_upd",))
        self.assertEqual(cur.fetchone(), ("/second",))

        # Dropping the key back to nothing NULLs the column again
        put_corpus(cur, dict(
            name="ut_corp_url_upd",
            title="UT corpus url upd",
            ordering=0,
        ))
        cur.execute("SELECT example_url FROM corpus WHERE name = %s", ("ut_corp_url_upd",))
        self.assertEqual(cur.fetchone(), (None,))


class Test_add_book_to_corpus(RequiresPostgresql, unittest.TestCase):
    def _book_ids_in(self, cur, corpus_name):
        cur.execute("""
            SELECT b.name
              FROM corpus c
              JOIN corpus_book cb ON cb.corpus_id = c.corpus_id
              JOIN book b ON b.book_id = cb.book_id
             WHERE c.name = %s
          ORDER BY b.name
        """, (corpus_name,))
        return [r[0] for r in cur.fetchall()]

    def test_add(self):
        """add_book_to_corpus links a book to a corpus"""
        cur = self.pg_cur()
        self.put_books(
            ut_a2c_one="Book one\nA Author\n\nHello.",
            ut_a2c_two="Book two\nA Author\n\nWorld.",
        )
        self.put_corpora(dict(name="ut_a2c_corp"))

        add_book_to_corpus(cur, dict(name="ut_a2c_corp"), dict(name="ut_a2c_one"))
        self.assertEqual(self._book_ids_in(cur, "ut_a2c_corp"), ["ut_a2c_one"])

        add_book_to_corpus(cur, dict(name="ut_a2c_corp"), dict(name="ut_a2c_two"))
        self.assertEqual(self._book_ids_in(cur, "ut_a2c_corp"), ["ut_a2c_one", "ut_a2c_two"])

    def test_idempotent(self):
        """Re-adding the same book is a no-op (no error, no duplicate row)"""
        cur = self.pg_cur()
        self.put_books(ut_a2c_idem="Book\nA Author\n\nHello.")
        self.put_corpora(dict(name="ut_a2c_idem_corp"))

        add_book_to_corpus(cur, dict(name="ut_a2c_idem_corp"), dict(name="ut_a2c_idem"))
        add_book_to_corpus(cur, dict(name="ut_a2c_idem_corp"), dict(name="ut_a2c_idem"))
        self.assertEqual(self._book_ids_in(cur, "ut_a2c_idem_corp"), ["ut_a2c_idem"])
