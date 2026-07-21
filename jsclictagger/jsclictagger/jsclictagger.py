"""
jsclictagger: Pyodide-friendly wrapper around clictagger.

Exposes a :py:class:`ClicTagger` instance whose methods can be invoked from
JavaScript via a web worker (see ``jsclictaggerWorker.js``).  Each method
mirrors the chained call ``TaggedText.from_file(file).table(highlight=...)``
so the JS layer can stay declarative.
"""
import os
import tempfile

from clictagger.taggedtext import TaggedText, DEFAULT_HIGHLIGHT_REGIONS


def _to_py(x):
    return x.to_py() if hasattr(x, "to_py") else x


def regionsFromContent(content, highlight=DEFAULT_HIGHLIGHT_REGIONS):
    return TaggedText(_to_py(content)).table(highlight=highlight).iter()
