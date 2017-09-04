###################################################
# """find_extra_chapter_titles.py: Checks for any paragraphs that should actually be titles of chapters"""
#
# NB: the conditions in line 24 are abitrary and designed specifically for Dickens books
# also results of the chapter still need hand checking anyway
#
# __author__ = "Catherine Smith, Matthew Brook O'Donnell, Rein Sikveland"
# __email__ = catherine.smith@nottingham.ac.uk
#
# usage: python find_extra_chapter_titles.py a_file_processed_through_step1
#
###################################################

import sys

from lxml import etree


tree = etree.parse(sys.argv[1])

PUNCTUATION = ['.', ',', ':', '!', '\'', ';', '?', '(', ')', '"']

# 1) Loop through each start paragraph in each chapter
# We are looking for sub-titles (e.g. in Dickens - NN and BH - others?) that have been labeled paragraph in Chapter annotation
# These will be put into chapter title instead
for paragraph in tree.xpath('//p[preceding-sibling::*[1][self::title]]'):
    text = paragraph.text.strip()
    # Move start paragraphs not ending in punctuation and that are less than x words long (arbitrary)
    if (text[-1] not in PUNCTUATION) or (text[-1] in ['?', '!'] and len(text.split(' ')) < 8) or (
            text[-1] in ['\''] and len(text.split(' ')) < 11):
        title = paragraph.xpath('./preceding-sibling::title')[0]
        title.text = '%s %s' % (title.text, text)
        paragraph.getparent().remove(paragraph)

# 2) create paragraph ids by counting paragraphs in each chapter
# paragraph ids
for chapter in tree.xpath('//div'):
    book = chapter.get('book')
    num = chapter.get('num')
    paragraphcount = 1
    for paragraph in chapter.xpath('p'):
        paragraph.set('pid', str(paragraphcount))
        paragraph.set('id', book + '.c' + num + '.p' + str(paragraphcount))
        paragraphcount += 1

print etree.tostring(tree)
