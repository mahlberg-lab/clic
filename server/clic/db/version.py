import os


def clic_version(cur):
    """
    Get current version of CLiC code & corpora
    """
    # Fetch versions from DB
    cur.execute("""
        SELECT repository_id, version FROM repository
    """)
    out = dict(cur)

    # CLiC might have been upgraded since import
    out['clic'] = os.environ.get('PROJECT_REV', 'development')

    return out
