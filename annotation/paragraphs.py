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
import os.path
import sys
import re

PART_BREAK = re.compile(r'^PART ([0-9IVXLC]+)\.(.*)')
CHAPTER_BREAK = re.compile(r'^(?:CHAPTER|BOOK) ([0-9IVXLC]+)\.(.*)|^MORAL.(.*)')

filename = sys.argv[1]
lines = open(filename).readlines()
book_abbreviation = os.path.basename(filename).replace('.txt', '')
subcorpus = os.path.basename(os.path.dirname(os.path.abspath(filename)))

print "<div0 id=\"%s\" type=\"book\" subcorpus=\"%s\" filename=\"%s\">\n\n" % (book_abbreviation, subcorpus, filename)

part_prefix = ""
current_chapter = 0
current_paragraph = 1
paragraph_text = ""
book_title = ""

# TODO: Read title and author lines, put them in their own tags?

for index, line in enumerate(lines):
    # Title
    if index == 0 and line.strip() != '':
        book_title = line.strip()
        print '<title>%s</title>' % cgi.escape(line.strip())
        continue

    # Author
    if index == 1 and line.strip() != '':
        print '<author>%s</author>' % cgi.escape(line.strip())
        continue

    m = PART_BREAK.match(line)
    if m:
        part_prefix = line.strip() + ' '
        continue

    m = CHAPTER_BREAK.match(line)
    if m:
        if current_chapter > 0:
            print '</div>'
        current_chapter += 1
        current_paragraph = 1
        paragraph_text = "" # TODO: What if there's remaining paragraph?
        print '<div id="%s.%d" subcorpus="%s" booktitle="%s" book="%s" type="chapter" num="%d">' % (
            cgi.escape(book_abbreviation, quote=True), current_chapter,
            cgi.escape(subcorpus, quote=True), cgi.escape(book_title, quote=True),
            cgi.escape(book_abbreviation, quote=True), current_chapter,
        )
        print '<title>%s%s</title>' % (
            cgi.escape(part_prefix),
            cgi.escape(line.strip()),
        )
        continue

    if line.strip() == '' and paragraph_text != '':
        # TODO: What about chapter 0 content? We're not wrapping that.
        print '<p pid="%d" id="%s.c%d.p%d">\n%s</p>\n' % (
            current_paragraph,
            cgi.escape(book_abbreviation, quote=True),
            current_chapter,
            current_paragraph,
            cgi.escape(paragraph_text[1:]), # NB: Remove initial space
        )
        current_paragraph += 1
        paragraph_text = ""
        continue

    if line.strip() != '':
        paragraph_text += ' ' + line.strip()

if current_chapter > 0:
    print '</div>'
print "\n\n</div0>"
