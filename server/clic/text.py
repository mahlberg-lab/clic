"""
Return the full text for a given book/chapter number
"""
class NullParser():
    """
    A no-op parser to avoid the LXML parsing hit
    """
    def process_document(self, session, doc):
        return doc
np = NullParser()


def text(cdb, corpora=[]):
    (where, params) = cdb.corpora_list_to_query(corpora, db='rdb')
    chapter_ids = cdb.rdb_query("SELECT book_id, chapter_num, chapter_id FROM chapter c WHERE " + where + " ORDER BY book_id, chapter_num", params)

    recStore = cdb.db.get_object(cdb.session, 'recordStore')
    try:
        yield {} # Return empty header
        for book_id, chapter_num, chapter_id in chapter_ids:
            rec = recStore.fetch_record(recStore.session, chapter_id, parser=np)
            yield [book_id, chapter_num, rec.get_raw(recStore.session)]
    finally:
        # Release DBD file handles, unfortunately the only public way to do this
        # is "commit_storing", which we don't want to do
        recStore._closeAll(recStore.session)
