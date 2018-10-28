import csv
import json
import os
import os.path


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
