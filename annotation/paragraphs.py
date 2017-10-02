'''
Parse plain text into initial XML format, divided into chapters and paragraphs.

We expect the following format:
(Book title)
(Book author)

  . . .

[PART I. (title of the part)]

(CHAPTER|BOOK|MORAL) (I|1). (title of the chapter)

 . . .

(CHAPTER|BOOK|MORAL) (II|2). (title of the chapter)

 . . .

Chapter numbering in CLiC is based on order of chapters in the text file, any
chapter number in the text is only visible in the chapter.

A book divided into parts has the part title appended to each chapter title.
Parts will be ignored when it comes to chapter numbering in CLiC.
'''
import cgi
import io
import os.path
import sys
import re
from lxml import etree

PART_BREAK = re.compile(r'^PART ([0-9IVXLC]+)\.(.*)')
CHAPTER_BREAK = re.compile(r'^(?:CHAPTER|BOOK) ([0-9IVXLC]+)\.(.*)|^MORAL.(.*)')

def paragraphs(lines, filename):
    xml_out = io.StringIO()
    book_abbreviation = os.path.basename(filename).replace('.txt', '')
    subcorpus = os.path.basename(os.path.dirname(os.path.abspath(filename)))

    xml_out.write(u"<div0 id=\"%s\" type=\"book\" subcorpus=\"%s\" filename=\"%s\">\n\n\n" % (book_abbreviation, subcorpus, os.path.basename(filename)))

    part_prefix = ""
    current_chapter = 0
    current_paragraph = 1
    paragraph_text = ""
    book_title = ""

    for index, line in enumerate(lines):
        # Title
        if index == 0 and line.strip() != '':
            book_title = line.strip()
            xml_out.write(u'<title>%s</title>\n' % cgi.escape(line.strip()))
            continue

        # Author
        if index == 1 and line.strip() != '':
            xml_out.write(u'<author>%s</author>\n' % cgi.escape(line.strip()))
            continue

        m = PART_BREAK.match(line)
        if m:
            part_prefix = line.strip() + ' '
            continue

        m = CHAPTER_BREAK.match(line)
        if m:
            if current_chapter > 0:
                xml_out.write(u'</div>\n')
            current_chapter += 1
            current_paragraph = 1
            paragraph_text = "" # TODO: What if there's remaining paragraph?
            xml_out.write(u'<div id="%s.%d" subcorpus="%s" booktitle="%s" book="%s" type="chapter" num="%d">\n' % (
                cgi.escape(book_abbreviation, quote=True), current_chapter,
                cgi.escape(subcorpus, quote=True), cgi.escape(book_title, quote=True),
                cgi.escape(book_abbreviation, quote=True), current_chapter,
            ))
            xml_out.write(u'<title>%s%s</title>\n' % (
                cgi.escape(part_prefix),
                cgi.escape(line.strip()),
            ))
            continue

        if line.strip() == '' and paragraph_text != '':
            # TODO: What about chapter 0 content? We're not wrapping that.
            xml_out.write(u'<p pid="%d" id="%s.c%d.p%d">\n%s</p>\n\n' % (
                current_paragraph,
                cgi.escape(book_abbreviation, quote=True),
                current_chapter,
                current_paragraph,
                cgi.escape(paragraph_text[1:]), # NB: Remove initial space
            ))
            current_paragraph += 1
            paragraph_text = ""
            continue

        if line.strip() != '':
            paragraph_text += ' ' + line.strip()

    if paragraph_text != '':
        xml_out.write(u'<p pid="%d" id="%s.c%d.p%d">\n%s</p>\n\n' % (
            current_paragraph,
            cgi.escape(book_abbreviation, quote=True),
            current_chapter,
            current_paragraph,
            cgi.escape(paragraph_text[1:]), # NB: Remove initial space
        ))
        current_paragraph += 1
        paragraph_text = ""
    if current_chapter > 0:
        xml_out.write(u'</div>\n')
    xml_out.write(u"\n\n</div0>\n")

    # Return a parsed tree of the output
    xml_out.seek(0)
    return etree.parse(xml_out)


if __name__ == "__main__":
    filename = sys.argv[1]
    tree = paragraphs(open(filename).readlines(), filename)
    tree.write(sys.argv[2])
