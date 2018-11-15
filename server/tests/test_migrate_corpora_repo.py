import csv
import os.path
import tempfile
import unittest

from clic.migrate.corpora_repo import parse_corpora_bib, import_book, export_book


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
            'corpora.bib': """
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
                title="Children's Literature",
                description='',
                ordering=3,
                carousel_image_path=os.path.join(corpora_dir, 'images', 'ChiLit_0.4.jpg'),
                contents=['brass', 'toadylion'],
            ), dict(
                name='ArTs',
                title='Additional Requested Texts',
                description='',
                ordering=4,
                carousel_image_path=None,
                contents=['gulliver', 'toadylion'],
            ),
        ])
