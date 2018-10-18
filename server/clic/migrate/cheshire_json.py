import json
import re

XML_TAG_REGEX = re.compile(r'<([^>]+)>([^<]*)', re.MULTILINE)


def from_cheshire_json(f, book_meta):
    """Interprets a /text response from a CLiC 1.6 instance into a 1.7 book format"""
    doc = json.load(f)
    book = dict(regions=[], content="")

    # First line should be book title
    book['regions'].append(['metadata.title', None, len(book['content'])])
    book['content'] += book_meta[doc['data'][0][0]]['title']
    book['regions'][-1].append(len(book['content']))
    book['content'] += "\n"

    # Second book author
    book['regions'].append(['metadata.author', None, len(book['content'])])
    book['content'] += book_meta[doc['data'][0][0]]['author']
    book['regions'][-1].append(len(book['content']))

    for book_id, chapter_num, xml_string in doc['data']:
        book['name'], new_string, new_regions = xml_to_plaintext(xml_string, len(book['content']))
        book['content'] += new_string
        book['regions'].extend(new_regions)
    return book


def xml_to_plaintext(xml_string, offset):
    """Converts cheshire XML back to plain text, along with a list of regions"""
    book_name = None
    chapter_num = None
    out_string = ""
    out_regions = []
    unclosed_regions = {}
    count_sentence = 1
    count_paragraph = 1

    def open_region(rclass, rvalue=None):
        if rclass in unclosed_regions:
            close_region(rclass)
            print("*** Warning: Unclosed %s" % rclass)
        unclosed_regions[rclass] = [rclass, rvalue, len(out_string) + offset]

    def close_region(rclass):
        if rclass not in unclosed_regions:
            print("*** Warning: Ignoring closure of unopen %s" % rclass)
            return
        if unclosed_regions[rclass][2] < len(out_string) + offset:
            # Region has content in, so store it
            out_regions.append(unclosed_regions[rclass] + [len(out_string) + offset])
        del unclosed_regions[rclass]

    for i, m in enumerate(re.finditer(XML_TAG_REGEX, xml_string)):
        part = m.group(1)
        text_part = m.group(2)

        if part.startswith('/span'):
            if 'chapter.sentence' in unclosed_regions:
                close_region('chapter.sentence')
        elif part.startswith('span class="s"'):
            open_region('chapter.sentence', count_sentence)
            count_sentence += 1

        # Ignore cheshire3's tokenisation
        elif part == '/w':
            pass
        elif part.startswith('w o='):
            pass

        elif part == '/s':
            close_region('chapter.sentence')
            out_string = out_string + " "
        elif part.startswith('s sid='):
            open_region('chapter.sentence', count_paragraph)
            count_paragraph += 1

        elif part == 'txt' or part == '/txt':
            continue  # Ignore, don't add txt to document
        elif part == '/toks':
            pass
        elif part == 'toks':
            pass

        elif part.startswith('qs '):
            if 'wordOffset=' in part:  # i.e. ignore fake quote-start at end
                close_region('quote.nonquote')
                open_region('quote.quote')
        elif part.startswith('qe '):
            if 'wordOffset=' in part:  # i.e. ignore fake quote-end
                close_region('quote.quote')
                open_region('quote.nonquote')

        # NB: Cheshire didn't differentiate between embedded suspensions and regular ones, work it out now
        elif part.startswith('sss '):
            open_region('quote.embedded.suspension.short' if 'quote.quote' in unclosed_regions else 'quote.suspension.short')
        elif part.startswith('sse '):
            close_region('quote.embedded.suspension.short' if 'quote.embedded.suspension.short' in unclosed_regions else 'quote.suspension.short')
        elif part.startswith('sls '):
            open_region('quote.embedded.suspension.long' if 'quote.quote' in unclosed_regions else 'quote.suspension.long')
        elif part.startswith('sle '):
            close_region('quote.embedded.suspension.long' if 'quote.embedded.suspension.long' in unclosed_regions else 'quote.suspension.long')

        elif part.startswith('alt-qs '):
            open_region('quote.embedded')
        elif part.startswith('alt-qe '):
            close_region('quote.embedded')

        elif part.startswith('p '):
            open_region('chapter.paragraph', count_paragraph)
            count_paragraph += 1
        elif part == '/p':
            close_region('chapter.paragraph')

        elif part == 'title':
            out_string = out_string + "\n\n\n"
            open_region('chapter.title', chapter_num)
            # Reformat the text part before it gets added
            text_part = re.sub(
                r'^(APPENDIX|INTRODUCTION|PREFACE|CHAPTER|CONCLUSION|PROLOGUE|PRELUDE|MORAL)?\s?([0-9IVXLC]*)\.*\s*',
                lambda m: (m.group(1) or 'CHAPTER').upper() + (' ' + m.group(2) if m.group(2) else '') + '. ',
                text_part,
                flags=re.IGNORECASE
            )
        elif part == '/title':
            close_region('chapter.title')
            open_region('chapter.text', chapter_num)
            open_region('quote.nonquote')

        elif re.match(r'div id="\w+.\d+" book="\w+" type="chapter" num="\d+"', part):
            # Top of chapter, note book name
            book_name = re.search(r'book="(\w+)"', part).group(1)
            chapter_num = re.search(r'num="(\d+)"', part).group(1)
            pass
        elif part == '/div':
            pass

        elif part == 'stru' or part == '/stru':
            # No idea.
            pass

        elif part.startswith('corr ') or part == '/corr':
            # Corrections? Bah.
            pass

        else:
            # Dunno
            raise ValueError("Unknown tag %s" % part)

        # Add any text to main string
        out_string = out_string + text_part

    close_region('chapter.text')
    if 'quote.quote' in unclosed_regions:
        # Close up a final quote
        close_region('quote.quote')
    if 'quote.nonquote' in unclosed_regions:
        close_region('quote.nonquote')
    if len(unclosed_regions) > 0:
        raise ValueError("Still have open regions: " + ",".join(unclosed_regions.keys()))
    # TODO: Boundaries
    return book_name, out_string, out_regions


def script_import_cheshire_json():
    import sys
    import timeit
    from clic.db.book import put_book
    from clic.db.cursor import get_script_cursor

    corpora_path = sys.argv[1]

    with open(corpora_path, 'r') as f:
        corpora = json.load(f)
    book_meta = {}
    for c in corpora['corpora']:
        for b in c['children']:
            book_meta[b['id']] = b

    with get_script_cursor(for_write=True) as cur:
        for file_path in sys.argv[2:]:
            print("=== %s" % file_path)

            print(" * Parsing...", end=" ", flush=True)
            start_time = timeit.default_timer()
            with open(file_path, 'r') as f:
                book = from_cheshire_json(f, book_meta)
            print("%.2f secs" % (timeit.default_timer() - start_time))

            print(" * Adding to DB...", end=" ", flush=True)
            start_time = timeit.default_timer()
            put_book(cur, book)
            print("%.2f secs" % (timeit.default_timer() - start_time))

            print(" * Committing...", end=" ", flush=True)
            start_time = timeit.default_timer()
            cur.connection.commit()
            print("%.2f secs" % (timeit.default_timer() - start_time))
    print("=== Updating materialised views...")
