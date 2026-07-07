import csv
import os
import os.path
import tempfile
import unittest
from unittest import mock

from clic.migrate import corpora_repo
from clic.migrate.corpora_repo import (
    export_book,
    get_corpora_for,
    import_book,
    parse_corpora_bib,
    to_region_file,
)

from .requires_postgresql import RequiresPostgresql
from .requires_run_script import RequiresRunScript


class RequiresCorporaDir():
    def tearDown(self):
        for dir in getattr(self, '_cd_dirs', []):
            dir.cleanup()

        super(RequiresCorporaDir, self).tearDown()

    def corpora_dir(self, contents):
        """Create a corpora directory with given contents"""
        if not hasattr(self, '_cd_dirs'):
            self._cd_dirs = []

        td = tempfile.TemporaryDirectory()
        self._cd_dirs.append(td)
        for file_path, content in contents.items():
            path = os.path.join(td.name, file_path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                if path.endswith('.csv'):
                    # Lists are written out as CSVs
                    writer = csv.writer(f)
                    for r in content:
                        writer.writerow(r)
                else:
                    f.write(content)
        return td.name


class Test_import_book(unittest.TestCase, RequiresCorporaDir):
    def test_call(self):
        """Read book file and generate dict"""
        corpora_dir = self.corpora_dir({
            'book1.txt': "Moo, said the cow.\n",
            'book2.txt': "Oink, said the pig. Oink.\n",
            'book2.regions.csv': [
                ('animal.noise', 0, 4, None, 'Oink'),
                ('animal.name', 0, 4, None, 'pig'),
                ('chapter.text', 0, 19, 1, "Oink, said the pig."),
                ('chapter.text', 20, 25, 2, "Oink."),
            ],
        })

        # Book without extra regions
        self.assertEqual(import_book(os.path.join(corpora_dir, 'book1.txt')), dict(
            name='book1',
            content='Moo, said the cow.\n',
        ))

        # Book with extra regions
        self.assertEqual(import_book(os.path.join(corpora_dir, 'book2.txt')), {
            'name': 'book2',
            'content': 'Oink, said the pig. Oink.\n',
            'animal.name': [(0, 4)],
            'animal.noise': [(0, 4)],
            'chapter.text': [(0, 19, 1), (20, 25, 2)],
        })


class Test_export_book(unittest.TestCase, RequiresCorporaDir):
    def test_call(self):
        corpora_dir = self.corpora_dir({
            'book1.txt': "Moo, said the cow.\n",
        })

        book_a = {'name': 'book_a', 'content': "I'm a book.\n", 'chapter.text': [(0, 12, None, "I'm a book.\n")]}

        # Export a book without regions, can re-read it
        export_book(book_a, dir=os.path.join(corpora_dir, 'noregions'), write_regions=False)
        self.assertEqual(import_book(os.path.join(corpora_dir, 'noregions/book_a.txt')), {
            'name': 'book_a',
            'content': "I'm a book.\n",
        })

        # Export a book with regions, can re-read it
        export_book(book_a, dir=os.path.join(corpora_dir, 'noregions'), write_regions=True)
        self.assertEqual(import_book(os.path.join(corpora_dir, 'noregions/book_a.txt')), {
            'name': 'book_a',
            'content': "I'm a book.\n",
            'chapter.text': [(0, 12)],
        })

        # The newline got filtered from the CSV output
        with open(os.path.join(corpora_dir, 'noregions/book_a.regions.csv')) as f:
            self.assertEqual(f.read().split("\n"), [
                "chapter.text,0,12,,I'm a book. ",
                "",
            ])


class Test_parse_corpora_bib(unittest.TestCase, RequiresCorporaDir):
    maxDiff = None

    def test_call(self):
        corpora_dir = self.corpora_dir({
            'images/ChiLit_0.4.jpg': "JPEG!",
            'corpora.bib': r"""
@book{swift_gullivers_1726,
        title = {Gulliver's Travels into Several Remote Nations of the World},
        url = {https://www.gutenberg.org/ebooks/829},
        shorttitle = {gulliver},
        author = {Swift, Jonathan},
        editor = {Price, David},
        urldate = {2017-06-28},
        date = {1726},
        keywords = {{ArTs}}
}

@book{cermakova_childrens_2017,
        location = {University of Birmingham, {UK}},
        title = {Children's Literature},
        series = {{CCR} Corpus},
        shorttitle = {{ChiLit}},
        number = {3},
        publisher = {Centre for Corpus Research},
        author = {Čermáková, A. and Mahlberg, M. and Wiegand, V.},
        date = {2017},
        example_url = {https://clic-fiction.com/toot?leap\&peep},
        keywords = {corpus}
}

@book{anstey_brass_1900,
        title = {The Brass Bottle},
        url = {https://www.gutenberg.org/ebooks/30689},
        shorttitle = {brass},
        author = {Anstey, F.},
        urldate = {2017-09-10},
        date = {1900},
        keywords = {{ChiLit}}
}

@book{mahlberg_additional_2017,
        location = {University of Birmingham, {UK}},
        title = {Additional Requested Texts},
        series = {{CCR} Corpus},
        shorttitle = {{ArTs}},
        number = {4},
        publisher = {Centre for Corpus Research},
        author = {Mahlberg, M. and Wiegand, V. and Čermáková, A.},
        date = {2017},
        keywords = {corpus}
}

@book{crockett_surprising_1897,
        title = {The Surprising Adventures of Sir Toady Lion with Those of General Napoleon Smith},
        url = {https://www.gutenberg.org/ebooks/39340},
        shorttitle = {toadylion},
        author = {Crockett, S. R.},
        urldate = {2017-09-10},
        date = {1897},
        keywords = {{ArTs},{ChiLit}}
}
            """.strip(),
        })
        out = sorted(parse_corpora_bib(corpora_dir), key=lambda c: c['ordering'])
        self.assertEqual(out, [
            dict(
                name='ChiLit',
                title="ChiLit - Children's Literature",
                description='',
                ordering=3,
                carousel_image_path=os.path.join(corpora_dir, 'images', 'ChiLit_0.4.jpg'),
                # NB: Unescaped
                example_url="https://clic-fiction.com/toot?leap&peep",
                contents=['brass', 'toadylion'],
            ), dict(
                name='ArTs',
                title='ArTs - Additional Requested Texts',
                description='',
                ordering=4,
                carousel_image_path=None,
                example_url=None,
                contents=['gulliver', 'toadylion'],
            ),
        ])


class Test_to_region_file(unittest.TestCase):
    def test_call(self):
        """to_region_file swaps the book extension for .regions.csv"""
        self.assertEqual(
            to_region_file('/some/dir/book1.txt'),
            '/some/dir/book1.regions.csv',
        )
        # Works with relative paths too
        self.assertEqual(
            to_region_file('book2.txt'),
            'book2.regions.csv',
        )
        # Only the final extension is replaced
        self.assertEqual(
            to_region_file('/a/b.c/book3.txt'),
            '/a/b.c/book3.regions.csv',
        )


CORPORA_BIB = """
@book{anstey_brass_1900,
        title = {The Brass Bottle},
        shorttitle = {brass},
        author = {Anstey, F.},
        date = {1900},
        keywords = {{ChiLit}}
}

@book{crockett_surprising_1897,
        title = {Sir Toady Lion},
        shorttitle = {toadylion},
        author = {Crockett, S. R.},
        date = {1897},
        keywords = {{ChiLit}}
}

@book{swift_gullivers_1726,
        title = {Gulliver's Travels},
        shorttitle = {gulliver},
        author = {Swift, Jonathan},
        date = {1726},
        keywords = {{ArTs}}
}

@book{cermakova_childrens_2017,
        title = {Children's Literature},
        shorttitle = {{ChiLit}},
        number = {3},
        author = {Čermáková, A.},
        date = {2017},
        keywords = {corpus}
}

@book{mahlberg_additional_2017,
        title = {Additional Requested Texts},
        shorttitle = {{ArTs}},
        number = {4},
        author = {Mahlberg, M.},
        date = {2017},
        keywords = {corpus}
}
""".strip()


class Test_get_corpora_for(unittest.TestCase, RequiresCorporaDir):
    maxDiff = None

    def test_call(self):
        """
        get_corpora_for returns a {book_path: corpus_dict} mapping,
        looking up the corpus by the book's parent-directory name.
        """
        corpora_dir = self.corpora_dir({
            'corpora.bib': CORPORA_BIB,
            'ChiLit/brass.txt': "Moo.",
            'ChiLit/toadylion.txt': "Oink.",
            'ArTs/gulliver.txt': "Baa.",
        })
        brass_path = os.path.join(corpora_dir, 'ChiLit', 'brass.txt')
        toady_path = os.path.join(corpora_dir, 'ChiLit', 'toadylion.txt')
        gulliver_path = os.path.join(corpora_dir, 'ArTs', 'gulliver.txt')

        out = get_corpora_for([brass_path, toady_path, gulliver_path])

        # ChiLit books share the same corpus dict; ArTs has its own
        self.assertEqual(set(out.keys()), {brass_path, toady_path, gulliver_path})
        self.assertIs(out[brass_path], out[toady_path])
        self.assertIsNot(out[brass_path], out[gulliver_path])
        self.assertEqual(out[brass_path]['name'], 'ChiLit')
        self.assertEqual(out[gulliver_path]['name'], 'ArTs')

    def test_subset(self):
        """Only requested books appear in the output, but corpora are fully populated"""
        corpora_dir = self.corpora_dir({
            'corpora.bib': CORPORA_BIB,
            'ChiLit/brass.txt': "Moo.",
            'ChiLit/toadylion.txt': "Oink.",
            'ArTs/gulliver.txt': "Baa.",
        })
        brass_path = os.path.join(corpora_dir, 'ChiLit', 'brass.txt')

        out = get_corpora_for([brass_path])
        self.assertEqual(list(out.keys()), [brass_path])
        # The corpus's contents list still reflects everything in the .bib,
        # not just the requested subset
        self.assertEqual(sorted(out[brass_path]['contents']), ['brass', 'toadylion'])


class Test_script_import_corpora_repo(
    RequiresPostgresql, RequiresRunScript, RequiresCorporaDir, unittest.TestCase,
):
    maxDiff = None

    def setUp(self):
        super().setUp()
        # Tests assert on the full content of the book / corpus tables,
        # so start from an empty DB each time.
        cur = self.pg_cur()
        cur.execute("TRUNCATE book, corpus RESTART IDENTITY CASCADE")
        cur.connection.commit()

        # update_version shells out to `git rev-parse` against a directory
        # that isn't a git repo in our temp fixtures, so stub it out.
        p = mock.patch('clic.db.version.update_version')
        p.start()
        self.addCleanup(p.stop)

    def _all_book_names(self):
        cur = self.pg_cur()
        cur.execute("SELECT name FROM book ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def _books_in_corpus(self, corpus_name):
        cur = self.pg_cur()
        cur.execute("""
            SELECT b.name
              FROM corpus c
              JOIN corpus_book cb ON cb.corpus_id = c.corpus_id
              JOIN book b ON b.book_id = cb.book_id
             WHERE c.name = %s
          ORDER BY b.name
        """, (corpus_name,))
        return [r[0] for r in cur.fetchall()]

    def test_basic(self):
        """Each book is inserted and added to the corpus matching its parent dir"""
        corpora_dir = self.corpora_dir({
            'corpora.bib': CORPORA_BIB,
            'ChiLit/brass.txt': "Brass Bottle\nF Anstey\n\nMoo, said the cow.",
            'ChiLit/toadylion.txt': "Toady Lion\nS R Crockett\n\nOink, said the pig.",
            'ArTs/gulliver.txt': "Gulliver\nJ Swift\n\nBaa, said the sheep.",
        })

        self.run_script(
            corpora_repo.script_import_corpora_repo,
            os.path.join(corpora_dir, 'ChiLit', 'brass.txt'),
            os.path.join(corpora_dir, 'ChiLit', 'toadylion.txt'),
            os.path.join(corpora_dir, 'ArTs', 'gulliver.txt'),
        )

        self.assertEqual(self._all_book_names(), ['brass', 'gulliver', 'toadylion'])
        self.assertEqual(self._books_in_corpus('ChiLit'), ['brass', 'toadylion'])
        self.assertEqual(self._books_in_corpus('ArTs'), ['gulliver'])

    def test_directory_argument(self):
        """A single directory argument is expanded to its *.txt files"""
        corpora_dir = self.corpora_dir({
            'corpora.bib': CORPORA_BIB,
            'ChiLit/brass.txt': "Brass Bottle\nF Anstey\n\nMoo, said the cow.",
            'ChiLit/toadylion.txt': "Toady Lion\nS R Crockett\n\nOink, said the pig.",
        })

        self.run_script(
            corpora_repo.script_import_corpora_repo,
            os.path.join(corpora_dir, 'ChiLit'),
        )

        self.assertEqual(self._all_book_names(), ['brass', 'toadylion'])
        self.assertEqual(self._books_in_corpus('ChiLit'), ['brass', 'toadylion'])

    def test_symlink_in_two_corpora(self):
        """
        A book symlinked into a second corpus directory is ingested once,
        but linked to both corpora.
        """
        corpora_dir = self.corpora_dir({
            'corpora.bib': CORPORA_BIB,
            'ChiLit/brass.txt': "Brass Bottle\nF Anstey\n\nMoo, said the cow.",
        })
        os.makedirs(os.path.join(corpora_dir, 'ArTs'))
        os.symlink(
            os.path.join(corpora_dir, 'ChiLit', 'brass.txt'),
            os.path.join(corpora_dir, 'ArTs', 'brass.txt'),
        )

        self.run_script(
            corpora_repo.script_import_corpora_repo,
            os.path.join(corpora_dir, 'ChiLit', 'brass.txt'),
            os.path.join(corpora_dir, 'ArTs', 'brass.txt'),
        )

        # Single row in book table (not duplicated)...
        self.assertEqual(self._all_book_names(), ['brass'])
        # ...but appears in both corpora
        self.assertEqual(self._books_in_corpus('ChiLit'), ['brass'])
        self.assertEqual(self._books_in_corpus('ArTs'), ['brass'])
