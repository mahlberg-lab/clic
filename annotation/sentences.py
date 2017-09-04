import sys
import re
from lxml import etree


class SentenceTokenizer(object):

    def __init__(self, text):
        """
        :param text: a string that one wants to analyze
        """

        self.text = text  #TODO unicode(text)?
        self.tree = etree.fromstring(self.text)

        # Regexes
        # (?:[\.!?:]|--) changed to (?:[\.!?:]|--|$) by Cat 11/10/08
        # - any second sentence not with final punctuation was getting lost and not printed
        # - text not good enough to trust the punctuation to be there!
        # 18/02/11 Cat removed -- from (?:[\.!?:]|--|$) as -- does not seem to indicate the end of a sentence
        # in the majority of cases and it doesn't seem to mean end of sentence in punctuation literature
        # may need to be put back in depending on Michaela's thoughts
        # regex = '.+?(?<!\.\.)(?:[\.!?:]|--)["\'\)]{0,2}(?=\s+|$)(?!\s*[a-z])'
        self.sentence_regex = re.compile("""
                                         .+?                           #
                                         (?<!\.\.)                     # disregard comments?
                                         (?:[\.!?:]|$)                 #
                                         ["\'\)]{0,2}                  #
                                         (?=\s+|$)                     #
                                         (?!\s*[a-z])                  #
                                         """, re.VERBOSE)              #
        self.abbreviation_regex = re.compile(
            '(^|\s|["\'-])([^\s]+?\.[a-zA-Z]+|Prof|Dr|Sr|Mr|Mrs|Ms|Jr|Capt|Gen|Col|Sgt|No|[ivxjCcl]+|[A-HJ-Z])\.(\s|$)')
        self.paragraph_regex = re.compile('\n\n+')

    def split_paragraph_into_sentences(self, text):
        """
        Output looks like:
        [['<div0 id="bh" type="book" filename="bh.txt">'], ['<stru>BLEAK HOUSE'], ['by Charles Dickens</stru>'], ...]
        """
        paragraphs = self.paragraph_regex.split(text)
        paragraph_list = []
        for paragraph in paragraphs:
            sentences = []
            s = self.abbreviation_regex.sub('\\1\\2&#46;\\3', paragraph)
            sl = self.sentence_regex.findall(s)
            if not sl:
                # s += '.'
                # sl = self.sentence_regex.findall(s)
                sl = [s]
            sentences.extend(sl)
            new_sentences = []
            for s in sentences:
                new_sentences.append(s.replace("&#46;", '.'))
            paragraph_list.append(new_sentences)
        return paragraph_list

    def add_tags(self, text):
        """
        Output looks like:
        <s><div0 id="bh" type="book" filename="bh.txt"></s> <s><stru>BLEAK HOUSE</s> <s>by Charles Dickens</stru></s>
        <s><cont>CONTENTS</s> <s>Preface</s> <s>I.</s> <s>In Chancery</s> <s>II.</s> <s>In Fashion</s> <s>III.</s>
        <s>A Progress</s> <s></cont></s> <s><stru>PREFACE</s>
        <s>Something.</stru></s> <s><title>CHAPTER I In Chancery</title></s>
        """
        a_str = ''
        paragraph_list = self.split_paragraph_into_sentences(text)
        for paragraph in paragraph_list:
            for sentence in paragraph:
                a_str += '<s>%s</s> ' % sentence.strip()
        return a_str

    def update_tree(self):
        """
        This updates the original self.tree.
        """
        for p in self.tree.xpath('//p'):
            paragraph_text = p.text
            tokenized = self.add_tags(paragraph_text)
            # uncomment the following line to get pure examples of sentence tokenization
            # print tokenized
            if not (tokenized.find('&amp;') == -1):
                tokenized = tokenized.replace('&amp;', '&#38;')
            else:
                if not (tokenized.find('&') == -1):
                    regex = re.compile('&(?!#[0-9]+;)')
                    tokenized = regex.sub('&#38;', tokenized)
            tokenized = tokenized.lstrip()

            nodetree = etree.fromstring('<foo>%s</foo>' % tokenized)
            p.text = None
            for n in nodetree:
                p.append(n)

    def add_sentence_ids(self):
        """
        """
        for chapter in self.tree.xpath('//div'):
            book = chapter.get('book')
            num = chapter.get('num')
            scount = 1
            for s in chapter.xpath('p/s'):
                s.set('sid', str(scount))
                s.set('id', book + '.c' + num + '.s' + str(scount))
                scount += 1

    def tokenize(self):
        """
        Printing the output because the bash scripts uses the printed output.
        """
        self.update_tree()
        self.add_sentence_ids()
        printable_tree = etree.tostring(self.tree)
        print printable_tree
        return printable_tree

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as a_file:
        a_text = a_file.read()
    tokenizer = SentenceTokenizer(a_text)
    tokenizer.tokenize()
