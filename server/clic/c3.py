# -*- coding: utf-8 -*-
import json
import os

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

from cheshire3.baseObjects import Session
from cheshire3.server import SimpleServer

session = Session()
session.database = 'db_dickens'

server = SimpleServer(
    session,
    os.path.join(CLIC_DIR, 'cheshire3-server', 'configs', 'serverConfig.xml')
)
db = server.get_object(session, session.database)
qf = db.get_object(session, 'defaultQueryFactory')
recStore = db.get_object(session, 'recordStore')
idxStore = db.get_object(session, 'indexStore')
#logger = db.get_object(session, 'concordanceLogger')

def get_corpus_names():
    """Return a list of valid corpus names"""
    return [
        x.queryTerm
        for x
        in idxStore.get_object(idxStore.session, 'subCorpus-idx')
    ]


#### LOAD METADATA ####
# load the metadata about chapters, word counts, etc.
# from each individual book in the corpus
# 1. get the directory of the present file (stored in __file__)
# 2. open the 'booklist.json' file which contains the data we want
# 3. convert it to json
#
# For each book in the corpus there is the following information listed in booklist:
#
#     book id - e.g. "BH"
#     book title - "Bleak House"
#     number of chapters in book
#     total number of paragraphs
#     total number of sentences
#     total number of words
#
# Then for each chapter within the book booklist:
#
#     number of paragraphs
#     number of sentences
#     number of words

with open(os.path.join(CLIC_DIR, 'booklist.json'), 'r') as raw_booklist:
    booklist = {}
    for b in json.load(raw_booklist):
        booklist[b[0][0]] = b

def get_chapter_stats(book, chapter):
    ## count paragraph, sentence and word in whole book
    if book not in booklist:
        raise ValueError("Cannot find book stats")

    b = booklist[book]
    out = dict(
        count_word=0,
        book_title=b[0][1],
        total_word=b[1][0][2],
    )
    for j, c in enumerate(b[2]):
        while j+1 < int(chapter):
            out['count_word'] += int(c[2])
            j += 1
            break
    return out
