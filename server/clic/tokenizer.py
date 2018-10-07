import re
import unidecode

RE_NON_WORD_EXTREMITIES = re.compile(r'^[\W_]+|[\W_]+$')
RE_QUERY_NON_WORD_EXTREMITIES = re.compile(r'^([^\w*]|_)+|([^\w*]|_)+$')


def word_split(s):
    """
    Split a string into a list of word parts
    """
    # TODO: This should be pyicu and fancy
    if not s:
        return []
    return re.split('\s+', s)


def word_to_type(s, query=False):
    """
    Take a word string and extract a corpus-linguistics type.
    * Lower-case
    * Remove any non-word characters from either end
    * Normalise unicode chars to ASCII. e.g. "don't"

    If query is TRUE, then allow *
    """
    s = s.lower()
    s = re.sub(RE_QUERY_NON_WORD_EXTREMITIES if query else RE_NON_WORD_EXTREMITIES, '', s)
    s = unidecode.unidecode(s)
    return s


def parse_query(q):
    """
    Turn a query string into a list of LIKE expressions
    """
    def term_to_like(t):
        """Escape any literal LIKE terms, convert * to %"""
        return (t.replace('\\', '\\\\')
                 .replace('%', '\\%')
                 .replace('_', '\\_')
                 .replace('*', '%'))

    return [term_to_like(word_to_type(w, query=True)) for w in word_split(q)]
