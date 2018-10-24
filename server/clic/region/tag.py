from .metadata import tagger_metadata
from .chapter import tagger_chapter
from .quote import tagger_quote


def tagger(book):
    """
    Add any missing tags to (book).
    This is just a wrapper for each of the metadata/chapter/quote tagging
    modules. For more information, look at the documentation for each.
    """
    tagger_metadata(book)
    tagger_chapter(book)
    tagger_quote(book)
