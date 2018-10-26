import csv
import os
import os.path

CORPORA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'corpora')


def export_book(book, dir=None, write_regions=False):
    output_file = os.path.abspath(os.path.join(
        CORPORA_DIR,
        dir or '',
        book['name']))
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file + '.txt', 'w') as f:
        f.write(book['content'])

    if write_regions:
        # Make flat list of regions
        regions = []
        for k in book.keys():
            if '.' not in k:
                continue
            for r in book[k]:
                regions.append((k,) + tuple(r))
        regions.sort(key=lambda r:(r[1], -r[2], r[0]))

        with open(output_file + '.regions.csv', 'w') as f:
            writer = csv.writer(f)
            for r in regions:
                writer.writerow(r)
    return output_file + '.txt'
