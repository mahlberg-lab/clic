'''
clic.migrate.corpora_repo: Import books from the CCR corpora repository
***********************************************************************
'''
import collections
import csv
import os
import os.path
import pybtex.database
from pylatexenc.latex2text import LatexNodes2Text

from clic.region.utils import regions_flatten, regions_unflatten


def parse_corpora_bib(corpora_dir, bib_name='corpora.bib'):
    """Read in a corpora.bib, output a list of corpora dicts"""
    pb = pybtex.database.parse_file(os.path.join(corpora_dir, bib_name))
    lt2txt = LatexNodes2Text()

    corpora = collections.defaultdict(lambda: dict(contents=[]))
    for _, entry in pb.entries.items():
        keywords = [lt2txt.latex_to_text(x) for x in entry.fields['keywords'].split(',')]
        if 'corpus' in keywords:
            c_id = lt2txt.latex_to_text(entry.fields['shorttitle'])

            carousel_image_path = os.path.join(corpora_dir, 'images', "%s_0.4.jpg" % c_id)
            if not os.path.exists(carousel_image_path):
                carousel_image_path = None

            corpora[c_id]['name'] = c_id
            corpora[c_id]['title'] = "%s - %s" % (c_id, lt2txt.latex_to_text(entry.fields['title']))
            corpora[c_id]['description'] = lt2txt.latex_to_text(entry.fields.get('abstract', ''))
            corpora[c_id]['carousel_image_path'] = carousel_image_path
            corpora[c_id]['ordering'] = int(lt2txt.latex_to_text(entry.fields['number']))
        else:
            for kw in keywords:
                corpora[kw]['contents'].append(lt2txt.latex_to_text(entry.fields['shorttitle']))

    return list(corpora.values())


def get_corpora_for(book_paths):
    """
    Return all corpora objects that contain the books in book_paths
    """
    wanted_books = set(os.path.splitext(os.path.basename(p))[0] for p in book_paths)

    # Assume all books sit in the same root
    corpora_dir = os.path.dirname(os.path.dirname(book_paths[0]))
    corpora = parse_corpora_bib(corpora_dir)

    # For each corpora, return it if it's contents are part of wanted_books
    for c in corpora:
        if not wanted_books.isdisjoint(c['contents']):
            yield c


def to_region_file(book_path):
    """Path of relevant region file for book_path"""
    return os.path.splitext(book_path)[0] + '.regions.csv'


def export_book(book, dir='.', write_regions=False):
    """
    Export book object (book) to "(dir)/(book['name']).txt"

    If write_regions is true, write a book.regions.csv next to the book
    containing all regions.
    """
    book_path = os.path.join(dir, book['name'] + '.txt')
    os.makedirs(os.path.dirname(book_path), exist_ok=True)

    with open(book_path, 'w') as f:
        f.write(book['content'])

    if write_regions:
        # Write out regions as a flattened list
        with open(to_region_file(book_path), 'w') as f:
            writer = csv.writer(f)
            for r in regions_flatten(book):
                writer.writerow((r[0], r[1], r[2], r[3], r[4].replace('\n', ' ')))
    return book_path


def import_book(book_path):
    """
    Read book at (book_path)
    """
    book = dict(name=os.path.basename(os.path.splitext(book_path)[0]))

    with open(book_path, 'r') as f:
        book['content'] = f.read()

    region_file = to_region_file(book_path)
    if os.path.exists(region_file):
        with open(region_file) as f:
            book.update(regions_unflatten(csv.reader(f)))

    return book


def script_import_corpora_repo():
    """Import corpora book file(s) into DB"""
    import sys
    import timeit
    from ..db.book import put_book
    from ..db.corpus import put_corpus
    from ..db.cursor import get_script_cursor
    from ..db.version import update_version
    from ..region.tag import tagger

    # Every argument is a book path, so e.g. "*/*.txt" works
    book_paths = sys.argv[1:]

    with get_script_cursor(for_write=True) as cur:
        for p in book_paths:
            print("* %s" % p, end=" ", flush=True)
            start_time = timeit.default_timer()
            book = import_book(p)  # Read book and/or regions file
            tagger(book)  # Fill in any remaining regions
            put_book(cur, book)  # Write to DB
            print("%.2f secs" % (timeit.default_timer() - start_time))
            cur.connection.commit()

        for c in get_corpora_for(book_paths):
            print("* corpora:%s" % c['name'], end=" ", flush=True)
            start_time = timeit.default_timer()
            put_corpus(cur, c)
            print("%.2f secs" % (timeit.default_timer() - start_time))

        if len(book_paths) > 0:
            # Update DB versions to match current CLiC & corpora repo.
            # NB: This is a bit broken, since we might not have imported the whole
            # repo, however insisting that you import the whole repo isn't feasible
            # and not much else to do currently.
            update_version(cur, 'clic-import')
            update_version(cur, 'corpora', os.path.dirname(book_paths[0]))


def script_region_export():
    """Calculate regions and re-export them as CSV"""
    import sys
    import timeit
    from ..region.tag import tagger

    # Every argument is a book path, so e.g. "*/*.txt" works
    book_paths = sys.argv[1:]

    for p in book_paths:
        print("* %s" % p, end=" ", flush=True)
        start_time = timeit.default_timer()
        book = import_book(p)  # Read book and/or regions file
        tagger(book)  # Fill in any remaining regions
        export_book(book, os.path.dirname(p), write_regions=True)  # Write it back again
        print("%.2f secs" % (timeit.default_timer() - start_time))
