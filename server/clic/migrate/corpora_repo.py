import csv
import json
import os
import os.path


def get_corpora_for(book_paths):
    """
    Return all corpora objects that contain the books in book_paths
    """
    if len(book_paths) == 0:
        return []

    # Assume all books sit in the same root
    corpora_dir = os.path.dirname(os.path.dirname(book_paths[0]))
    with open(os.path.join(corpora_dir, 'corpora.json'), 'r') as f:
        corpora_doc = json.load(f)

    # Make lookup of corpora names to details
    corpora_lookup = {}
    for i, c in enumerate(corpora_doc['corpora']):
        carousel_image_path = os.path.join(corpora_dir, 'images', "%s_0.4.jpg" % c['id'])

        corpora_lookup[c['id']] = dict(
            name=c['id'],
            title=c['title'],
            description=c['description'],
            contents=[b['shorttitle'] for b in corpora_doc['content'][c['id']]],
            carousel_image_path=carousel_image_path if os.path.exists(carousel_image_path) else None,
            ordering=i,
        )

    # For each book we want, find the relevant corpora entry
    wanted_books = set(os.path.relpath(p, corpora_dir) for p in book_paths)
    out = {}
    for corpora_name, books in corpora_doc['content'].items():
        for b in books:
            if b['path'] in wanted_books:
                out[corpora_name] = corpora_lookup[corpora_name]
    return out.values()


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
        # Make flat list of regions
        regions = []
        for k in book.keys():
            if '.' not in k:
                continue
            for r in book[k]:
                regions.append((k,) + tuple(r))
        regions.sort(key=lambda r: (r[1], -r[2], r[0]))

        with open(to_region_file(book_path), 'w') as f:
            writer = csv.writer(f)
            for r in regions:
                writer.writerow(r)
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
            for r in csv.reader(f):
                if r[0] not in book:
                    book[r[0]] = []
                book[r[0]].append(tuple(int(x) for x in r[1:]))

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
