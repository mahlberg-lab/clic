'''
clic.db.version: Get/set corpora version in DB
**********************************************
'''
import os
import subprocess

import appconfig


def clic_version(cur):
    """
    Get current version of CLiC code & corpora
    """
    # Fetch versions from DB
    cur.execute("""
        SELECT name, version FROM repository
    """)
    out = dict(cur)

    # CLiC might have been upgraded since import
    out['clic'] = os.environ.get('PROJECT_REV', appconfig.PROJECT_REV)

    return out


def update_version(cur, name, version_dir=None):
    """
    Update version (name) to (version)
    - name: Name of version to send back to client, e.g. "clic:import", "corpora"
    - version_dir: Get a git SHA for version_dir, or use the current clic revision
    """
    if version_dir:
        version = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=version_dir
        ).decode('utf8').strip()
    else:
        version = os.environ.get('PROJECT_REV', appconfig.PROJECT_REV)

    cur.execute("""
        INSERT INTO repository (name, version)
             VALUES (%(name)s, %(version)s)
        ON CONFLICT (name) DO UPDATE SET version=EXCLUDED.version
    """, dict(
        name=name,
        version=version,
    ))
