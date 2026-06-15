import contextlib
import sys
from unittest import mock


class RequiresRunScript():
    """
    Mixin (combine with RequiresPostgresql) to drive a clic CLI script
    entry point against the test database.
    """
    def run_script(self, script_fn, *argv):
        """
        Invoke (script_fn) with sys.argv set to [name, *argv], routing any
        get_script_cursor() it opens to the test PG cursor.
        """
        cur = self.pg_cur()

        @contextlib.contextmanager
        def fake_cursor(for_write=False):
            yield cur

        fake_argv = [script_fn.__name__] + list(argv)
        with mock.patch.object(sys, 'argv', fake_argv), \
             mock.patch('clic.db.cursor.get_script_cursor', fake_cursor):
            script_fn()
