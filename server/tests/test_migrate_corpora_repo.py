import csv
import os.path
import tempfile
import unittest

from clic.migrate.corpora_repo import import_book, export_book

class RequiresCorporaDir():
    def tearDown(self):
        for dir in getattr(self, '_cd_dirs', []):
            dir.cleanup()

        super(RequiresMockCorporaDir, self).tearDown()

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
