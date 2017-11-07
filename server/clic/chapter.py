"""
Return the XML for a given (chapter_id)
"""

class NullParser():
    """
    A no-op parser to avoid the LXML parsing hit
    """
    def process_document(self, session, doc):
        return doc
np = NullParser()

def chapter(cdb, chapter_id):
    chapter_id = chapter_id[0]

    # Get document and return it directly
    recStore = cdb.db.get_object(cdb.session, 'recordStore')
    try:
        rec = recStore.fetch_record(recStore.session, chapter_id, parser=np)
        return rec.get_raw(recStore.session)
    finally:
        # Release DBD file handles, unfortunately the only public way to do this
        # is "commit_storing", which we don't want to do
        recStore._closeAll(recStore.session)
