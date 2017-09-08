# 2) hard-code books with double quotations:
# NOTE - Look into Frankenstein: Normally double, but single when inside written texts
# any new books with double quotation marks must be added to this list
DOUBLE_QUOTEMARKS = [
    'bh',
    'cc',
    'ge',
    'hm',
    'ttc',
    'na',
    'ss',
    'per',
    'prpr',
    'mp',
    'emma',
    'wwhite',
    'viviang',
    'vanity',
    'tess',
    'sybil',
    'prof',
    'pride',
    'persuasion',
    'native',
    'mill',
    'mary',
    'ladyaud',
    'jude',
    'jekyll',
    'jane',
    'frank',
    'dracula',
    'dorian',
    'deronda',
    'cran',
    'basker',
    'arma',
    'alli',
]

# Chillit corpus books
DOUBLE_QUOTEMARKS += [
    'bunny',
    'coral',
    'duke',
    'five',
    'flopsy',
    'forest',
    'gulliver',
    'holiday',
    'jemima',
    'jungle',
    'mice',
    'pan',
    'prince',
    'princess',
    'railway',
    'secret',
    'squirrel',
    'stiria',
    'treasure',
    'vice',
    'water',
    'wind',
]

def single_or_double(book):
    """
    Look up whether the book uses single or double quotation marks
    """
    return 'double' if book.lower() in DOUBLE_QUOTEMARKS else 'single'
