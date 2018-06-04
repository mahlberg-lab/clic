"""
Return the XML for a given book/chapter number
"""
from clic.errors import UserError

class NullParser():
    """
    A no-op parser to avoid the LXML parsing hit
    """
    def process_document(self, session, doc):
        return doc
np = NullParser()

def chapter(cdb, book=[], chapter_num=[], chapter_id=[]):
    if len(chapter_id) > 0:
        chapter_id = chapter_id[0]
    elif len(book) == 1 and len(chapter_num) == 1:
        chapter_id = cdb.rdb_query("SELECT chapter_id FROM chapter WHERE book_id = ? AND chapter_num = ?", (
            book[0],
            int(chapter_num[0]),
        )).fetchone()
        if chapter_id is None:
            raise UserError('This book/chapter combination doesn\'t seem to exist', 'error')
        else:
            chapter_id = chapter_id[0]
    else:
        raise UserError('book/chapter not provided', 'error')

    # Get document and return it directly
    recStore = cdb.db.get_object(cdb.session, 'recordStore')
    try:
        rec = recStore.fetch_record(recStore.session, chapter_id, parser=np)
        return rec.get_raw(recStore.session)
    finally:
        # Release DBD file handles, unfortunately the only public way to do this
        # is "commit_storing", which we don't want to do
        recStore._closeAll(recStore.session)
