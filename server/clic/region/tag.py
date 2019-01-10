"""
clic.region.tag: Tag a book with all region taggers
***************************************************

Applies all the tagging modules on a book in turn
"""
from .metadata import tagger_metadata
from .chapter import tagger_chapter
from .quote import tagger_quote
from .suspension import tagger_quote_suspension


def tagger(book):
    """
    Add any missing tags to (book).
    This is just a wrapper for each of the metadata/chapter/quote tagging
    modules. For more information, look at the documentation for each.
    """
    tagger_metadata(book)
    tagger_chapter(book)
    tagger_quote(book)
    tagger_quote_suspension(book)
