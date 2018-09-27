import json
import re

XML_TAG_REGEX = re.compile(r'<([^>]+)>')


def from_cheshire_json(f):
    doc = json.load(f)

    book = dict(regions=[], content="")
    for book_id, chapter_num, xml_string in doc['data']:
        book['name'], new_string, new_regions = xml_to_plaintext(xml_string, len(book['content']))
        book['content'] += new_string
        book['regions'].extend(new_regions)
    return book


def xml_to_plaintext(xml_string, offset):
    """Converts cheshire XML back to plain text, along with a list of regions"""
    book_name = None
    out_string = ""
    out_regions = []
    unclosed_regions = {}

    def open_region(rclass, rvalue=None):
        if rclass in unclosed_regions:
            close_region(rclass)
            print("*** Warning: Unclosed %s" % rclass)
        unclosed_regions[rclass] = [rclass, rvalue, len(out_string) + offset]

    def close_region(rclass):
        if rclass not in unclosed_regions:
            print("*** Warning: Ignoring closure of unopen %s" % rclass)
            return
        out_regions.append(unclosed_regions[rclass] + [len(out_string) + offset])
        del unclosed_regions[rclass]

    for i, part in enumerate(re.split(XML_TAG_REGEX, xml_string)):
        if i % 2 == 0:
            # Text part, add to string
            if 'chapter.title' in unclosed_regions:
                # Parsing the title, reformat it
                out_string = out_string + "CHAPTER %s." % part
            elif 'ignore.text' in unclosed_regions:
                pass  # Ignore plain-text version
            elif 'token.word' in unclosed_regions:
                # rvalue for a word should be it's type
                unclosed_regions['token.word'][1] = re.sub(r'\W+', '', part).lower()
                out_string = out_string + part
            else:
                out_string = out_string + part

        elif part.startswith('/span'):
            if 'token.word' in unclosed_regions:
                close_region('token.word')
            elif 'chapter.sentence' in unclosed_regions:
                close_region('chapter.sentence')
        elif part.startswith('span class="w"'):
            open_region('token.word')
        elif part.startswith('span class="s"'):
            open_region('chapter.sentence', 1)  # TODO: paragraph count

        elif part == '/w':
            close_region('token.word')
        elif part.startswith('w o='):
            open_region('token.word')

        elif part == '/s':
            close_region('chapter.sentence')
        elif part.startswith('s sid='):
            open_region('chapter.sentence', 1)  # TODO: paragraph count

        elif part == '/txt':
            close_region('ignore.text')
        elif part == 'txt':
            open_region('ignore.text')
        elif part == '/toks':
            pass
        elif part == 'toks':
            pass

        elif part.startswith('qs '):
            if 'wordOffset=' in part:  # i.e. ignore fake quote-start at end
                open_region('quote.quote')
        elif part.startswith('qe '):
            if 'wordOffset=' in part:  # i.e. ignore fake quote-end
                close_region('quote.quote')

        elif part.startswith('sss '):
            open_region('quote.suspension.short')
        elif part.startswith('sse '):
            close_region('quote.suspension.short')
        elif part.startswith('sls '):
            open_region('quote.suspension.long')
        elif part.startswith('sle '):
            close_region('quote.suspension.long')

        elif part.startswith('alt-qs '):
            open_region('quote.embedded')
        elif part.startswith('alt-qe '):
            close_region('quote.embedded')

        elif part.startswith('p '):
            open_region('chapter.paragraph', 1)  # TODO: paragraph count
        elif part == '/p':
            close_region('chapter.paragraph')

        elif part == 'title':
            open_region('chapter.title')
        elif part == '/title':
            close_region('chapter.title')
            out_string = out_string + "\n\n"

        elif re.match(r'div id="\w+.\d+" book="\w+" type="chapter" num="\d+"', part):
            # Top of chapter, note book name
            book_name = re.search(r'book="(\w+)"', part).group(1)
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

    if 'quote.quote' in unclosed_regions:
        # Close up a final quote
        close_region('quote.quote')
    if 'quote.nonquote' in unclosed_regions:
        close_region('quote.nonquote')
    if len(unclosed_regions) > 0:
        raise ValueError("Still have open regions!")
    # TODO: non-quote regions
    # TODO: Boundaries
    return book_name, out_string, [x for x in out_regions if x[0] != 'ignore.text']


def script_import_cheshire_json():
    import sys
    from clic.db.book import put_book
    from clic.db.cursor import get_script_cursor

    file_path = sys.argv[1]

    with open(file_path, 'r') as f:
        book = from_cheshire_json(f)
    with get_script_cursor() as cur:
        put_book(cur, book)
