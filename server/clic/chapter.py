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
    rec = cdb.recStore.fetch_record(cdb.session, chapter_id, parser=np)
    return rec.get_raw(cdb.session)
