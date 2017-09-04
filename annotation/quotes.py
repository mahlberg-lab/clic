import sys
import re

from lxml import etree


class QuoteTokenizer:

    """
    Extracts quotes from literary texts and annotates the text
    with XML milestones to indicate where quotes start.

    The QuoteTokenizer can either be imported and used as such
    or this file can be run with as an argument on the commandline
    the text file you want to tokenize:

        python quotes.py bh_sentence_tagged.xml > bh_quote_tagged.xml

    Rein's notes:
    -------------
    PROCEDURE:
    1) Use pre-defined regular expressions to identify quotation pairs
        (single and double)
    2) Books with single and double quotations are currently distinguished in
        hard-coding - TO IMPROVE?
    3) Write function to insert quote tags in text string. Only deals with
        within-paragraph quote pairs (for cross-paragraph quote tagging, see 6))
    4) Apply function in 3) to each paragraph, read as text string
        a) Each paragraph is processed as text string
        b) process paragraph as xml and insert new tagged paragraph content
    5) If paragraph contains qs tag, insert attribute type="speech" to current
        paragraph
    6) Extended cross-paragraph quotes: Two for loops sort out these

    NEW IN V3:
    - #1: Modified 6d) - COND A.2a. Dealing with extended paragraphs which begin
        with one type of quote (e.g. double) and end in another (single)
        (problem for Frankenstein - see e.g. frank.c15.p36)

    To fix/improve:
    - I don't yet understand the process of assigning "beginning" attributes
    - Make definition of pid in 6d.1 more readable?
    """

    def __init__(self, text):

        # 1) Define quotations
        # Uses double quotation marks (")
        self.quote_regex_double = re.compile(
            "(^| |--|<s[^>]+>|\(|,)((&quot;)(?:<s[^>]+>|.(?!quot;))+(?:\\3(?= --)|\\3(?=--)|[,?.!-;_]\\3))( |--|</s>|$|[\w]|\))")
        self.quote_regex_single = re.compile(
            "(^| |--|<s[^>]+>|\(|,)((['])(?:(?<![,?.!])'[ edstvyrlamoEDSTVYRLAMO]|[^'])+(?:\\3(?= --)|\\3(?=--)|[,?.!-;_]\\3))( |--|</s>|$|[\w]|\))")
        self.text = text
        # This tree is modified by the tokenizer.
        self.tree = etree.fromstring(self.text)

        # print self.text[0:100]
        # print self.tree
        # print self.tree.xpath('//p')[0:10]

        # 2) hard-code books with double quotations:
        # NOTE - Look into Frankenstein: Normally double, but single when inside written texts
        # any new books with double quotation marks must be added to this list
        self.double = [
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
            'alli']

    def compute_quote_consistence(self):
        """
        Shows a number of examples where quotes might have been
        opened, but not closed, or vice versa.
        """
        raise NotImplementedError

    def single_or_double(self):
        """
        Look up whether the book uses single or double quotation marks
        """

        for paragraph in self.tree.xpath('(//p)[1]'):
            id = paragraph.get('id')
            # get id name until first '.' - find() looks for matching string
            # position
            book = id[:id.find('.')]
            if book.lower() in self.double:
                quote_style = 'double'
            else:
                quote_style = 'single'
        self.quote_style = quote_style
        return quote_style

    def annotate_quotes(self, text, quote_style):
        # 3) function for tagging quotes
        # deals only with quote pairs within paragraphs
        # quotes that extend across paragraphs are dealt with in
        self.single_or_double()
        if self.quote_style == 'single':
            # replace location following the first matched group with <qs/>,
            # etc.
            return re.sub(self.quote_regex_single, '\\1<qs/>\\2<qe/>\\4', text)
        else:
            # deal with the problem of xml attributes containing " in double
            # quoted books
            # replace each in-text " with '&quot'. Regular expression says that if " precedes < before the occurrence of any >
            # then label '&quot'. This excludes any " in attributes.
            s = re.sub('"(?=[^>]*<)', '&quot;', text)
            t = re.sub(self.quote_regex_double, '\\1<qs/>\\2<qe/>\\4', s)
            return t.replace('&quot;', '"')

            # FIXME does this add <qs/> to open quotes (paragraphs that only have an opening quote)?

            # Rein goes about it as follows:

            # NEW: we can disregard paragraph if there is only one &quot; label (these are dealt with below)
            # if len(re.findall('&quot;', s)) != 1:
            #    t = re.sub(quoteD,'\\1<qs/>\\2<qe/>\\4', s)
            #    return t.replace('&quot;', '"')
            # else:
            # return s.replace('&quot;', '"') # return string with quotation
            # tags, and " re-inserted

    def first_run(self):
        # print "starting the first run"
        # FIXME weird to call it here:
        self.single_or_double()
        # print self.quote_style
        # 4) Apply function in 3) to each paragraph
        # a) Each paragraph is processed as text string
        for paragraph in self.tree.xpath('//p'):
            text = etree.tostring(paragraph)
            # print text
            # process only text following first > (paragraph element) and
            # preceding final <
            text = text[text.find('>') + 1:text.rfind('<')]
            # print text
            # Tag text string according to function 3)
            tagged = self.annotate_quotes(text, self.quote_style)
            # print tagged

            # b) process paragraph as xml and insert new tagged paragraph content
            # replace beginning and end of tagged string with <foo>
            # (representing parent element)
            nodetree = etree.fromstring('<foo>%s</foo>' % tagged)
            # run loop over each sub-element of <p> (each sentence)...
            for c in paragraph.getchildren():
                paragraph.remove(c)
            # ... and insert new sentence (n) to current paragraph instead
            for n in nodetree:
                paragraph.append(n)

        # 5) If paragraph contains qs tag, insert attribute type="speech" to
        # current paragraph
        for paragraph in self.tree.xpath('//p[s/qs]'):
            paragraph.set('type', 'speech')

        # print self.tree

    def second_run(self):
        """
        6) Work on quotes that extend multiple paragraphs
        6.1 We are interested in paragraphs that start and end with quotes: These are potentially
        the last paragraph in extended quotes (e.g. Frankenstein, id=frank.c6.p13)
        (except for Emma, where end quote paragraphs only end with quotes)
        We'll call this paragraph group 'ends' (6b).
        Two for loops sort out extended cross paragraph quotes
        """
        # print "starting the second run"
        # a) Regular expressions for paragraphs that begin (regex2)
        # and end (regex3) with quote tags
        # find paragraphs that start with <qs/>
        regex2 = re.compile('(<p[^>]+>(\s+?)?<s[^>]+>(\s+?)?<qs/>)')
        # find paragraphs that end with <qe/>
        regex3 = re.compile('(<qe/>(\s+?)?</s>(\s+?)?</p>)')

        # b) prepare list of paragraph ids for (potential) end paragraphs
        ends = []

        # c) Loop identifies paragraphs that begin and end with quote tags
        # find all the paragraphs which exist of a whole quotation and nothing else
        # next two for loops sort out extended cross paragraph quotes

        # count 1 qs tag within each paragraph
        for paragraph in self.tree.xpath('//p[count(.//qs)="1"]'):
            # find all the paragraphs which exist of a whole quotation and
            # nothing else
            string = etree.tostring(paragraph)

            # (we only search in paragraphs with 1 qs tag,
            # so we'll only find one of each)
            if re.search(regex2, string) and re.search(regex3, string):
                tmp = paragraph.get('id')
                # get book + chapter name (rfind looks for final matching item
                # in string)
                cid = tmp[:tmp.rfind('.')]
                pid = paragraph.xpath('./@pid')  # get paragraph id
                ends.append((cid, pid))  # send ids to ends list
                # these paragraphs haven't already been given speech attribute
                paragraph.set(
                    'type',
                    'speech')

        # d) loop through the potential end paragraphs collected above
        for e in ends:
            cid = e[0]  # get chapter id for current end-paragraph
            pid = int(e[1][0])  # get paragraph id as integer
            # as we'll be playing with previous paragraphs, define reference pid
            # (pid will be redefined as pid-1 in d.1)
            origpid = int(e[1][0])
            # d.1) We first work with end-paragraphs that are not the final one
            # in a chain of end-paragraphs
            end = False
            # COND.A: set up a while loop which looks backwards, until
            # it either meets following if condition, or pid = 1 (i.e. first
            # paragraph in current chapter, in which case pid-1 = 0)
            while pid > 0 and not end:
                # pid is now defined as preceding paragraph (MAKE MORE READABLE)
                pid = pid - 1
                # COND.A1a: if paragraph is not the first in the chapter (i.e.
                # pid is not 0)
                if len(self.tree.xpath('//p[@id="%s.p%s"]' % (cid, pid))) > 0:
                    for paragraph in self.tree.xpath('//p[@id="%s.p%s"]' % (cid, pid)):
                        # get content of paragraph (as list)
                        # print "trying to get text()"
                        l = paragraph.xpath('.//text()')
                        # print l

                        string = ' '.join(l)  # join string list
                        string = string.strip()  # strip no characters (??)

                        # If there are no quotation tags in paragraph, but
                        # COND.A2a: there are quotations at beginning (string[0])
                        # AND end (string[-1]) for string,
                        # add attributes saying the paragraph is in the middle
                        # of extended quotations
                        # at this stage all non-tagged paragraphs are given the
                        # 'middle' attribute (whether or not they initiate or
                        # end extended quotes)
                        # NOTE: A paragraph may begin with double quotes but end
                        # with single quotes - these have been fixed in this
                        # version, by dealing with single and double quotes
                        # separately below (NEW#1)
                        if not paragraph.xpath('.//qs'):
                            #if (string[0] == '\'' or string[0] == '"') and (string[-1] != '\'' and string[-1] != '"'):
                            # Rein's version:
                            if ((string[0] == '\'' and string[-1] != '\'') or (string[0] == '"' and string[-1] != '"')) :
                                paragraph.set('type', 'speech')
                                paragraph.set('form', 'extended')
                                paragraph.set('position', 'middle')

                            # COND.A2b: if there are no quotations beginning or
                            # ending non-quote-tagged paragraph
                            # mark start of paragraphs with a qs tag (regardless:
                            # all conditions which are not met in COND.A2b will
                            # be qs tagged
                            # This means that at this stage there are multiple
                            # qs tags where they shouldn't be,
                            # and there are "beginning" attributes where they
                            # oughtn't be
                            # it seems to identify potential "beginning"
                            # paragraphs
                            else:
                                # if current pid (pid+1) is not the same as
                                # original pid
                                if not pid + 1 == origpid:
                                    # move the qs to the start of pid+1 (the
                                    # previous loop round)
                                    qstart = self.tree.xpath(
                                        '//p[@id="%s.p%s"]' %
                                        (cid, pid + 1))[0]
                                    st = etree.tostring(qstart)
                                    # insert qs tag at beginning of paragraph
                                    st2 = re.sub(
                                        '<p( .+?)>(?:\s+?)?<s( .+?)>(\s+?)?',
                                        '<p \\1><s \\2><qs/>',
                                        st)
                                    new = etree.fromstring(st2)
                                    # J: this overwrites the earlier given middle tag!
                                    # or is that in the next condition?
                                    new.set('type', 'speech')
                                    new.set('form', 'extended')
                                    new.set('position', 'beginning')
                                    qstart.getparent().replace(qstart, new)
                                end = True

                        # if there are quote tags in current paragraph
                        # remove faulty "beginning" attributes and additions qs tags
                        # If this operation is done without the condition above,
                        # the "beginnings" won't have been identified, only
                        # "middle"
                        else:
                            if not pid + 1 == origpid:
                                # move the qs to the start of pid+1 (the
                                # previous loop round)
                                qstart = self.tree.xpath(
                                    '//p[@id="%s.p%s"]' %
                                    (cid, pid + 1))[0]
                                st = etree.tostring(qstart)
                                st2 = re.sub(
                                    '<p( .+?)>(?:\s+?)?<s( .+?)>(\s+?)?',
                                    '<p \\1><s \\2><qs/>',
                                    st)
                                new = etree.fromstring(st2)
                                new.set('type', 'speech')
                                new.set('form', 'extended')
                                new.set('position', 'beginning')
                                qstart.getparent().replace(qstart, new)
                            end = True

                # COND.A1b: if previous paragraph is in a preceding chapter
                # Seems to change "middle" to "beginning" at Chapter beginnings
                else:
                    if not pid + 1 == origpid:
                        # move the qs to the start of pid+1 (the previous loop
                        # round)
                        qstart = self.tree.xpath(
                            '//p[@id="%s.p%s"]' %
                            (cid, pid + 1))[0]
                        st = etree.tostring(qstart)
                        st2 = re.sub(
                            '<p( .+?)>(?:\s+?)?<s( .+?)>(\s+?)?',
                            '<p \\1><s \\2><qs/>',
                            st)
                        new = etree.fromstring(st2)
                        new.set('type', 'speech')
                        new.set('form', 'extended')
                        new.set('position', 'beginning')
                        qstart.getparent().replace(qstart, new)
                    end = True

            # if paragraph is the last with quotation - insert attribute "end"
            if end:
                if not pid + 1 == origpid:
                    # take the qs out of the current paragraph
                    current = self.tree.xpath(
                        '//p[@id="%s.p%s"]' %
                        (cid, origpid))[0]
                    st = etree.tostring(current)
                    st2 = re.sub('<qs/>', '', st)
                    new = etree.fromstring(st2)
                    new.set('type', 'speech')
                    new.set('form', 'extended')
                    new.set('position', 'end')
                    current.getparent().replace(current, new)

    def tokenize(self):
        self.first_run()
        self.second_run()
        return etree.tostring(self.tree)

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as a_file:
        text = a_file.read()
    tokenizer = QuoteTokenizer(text)
    print tokenizer.tokenize()
