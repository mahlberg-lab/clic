import sys
import re

from lxml import etree

def suspensions(tree):
    # regular expression looks for quotation tags
    regex = re.compile('(<q[es]/>)')

    # find the middle bit of the qe qs and split on space - count each entry in
    # list that contains at least one alpha char if more than 4 long 4 or less short
    for p in tree.xpath('//p[s/qe]'):

        # Why is this repeated here:
        p.set('type', 'speech')

        # a. get paragraph paragraph_string
        paragraph_string = etree.tostring(p)

        # b. break up paragraph into list of...
        #    - "<qs/>"
        #    - "... stuff ..."
        #    - "<qe/>"
        #    - "... stuff ..."
        #    - "<qs/>"
        wlist = re.split(regex, paragraph_string)

        # c. run index over listed items in each paragraph
        for i in range(0, len(wlist)):

            # We look ahead 2 items, don't overflow
            if i + 2 < len(wlist):
                # Only consider ["<qe/>", (content), "<qs/>"] triples
                if wlist[i] == '<qe/>' and wlist[i + 2] == '<qs/>':

                    # count words in string: For deciding whether to label short
                    # or long suspension
                    wordCount = 0
                    tag = False  # operator for whether or not a tag is present

                    # NOTE: There are <s> tags within some i+1 list items, preceding <qs>
                    # We want to get rid of these with a regular expression
                    # split into <sX> items of letters preceding white-space (i.e.
                    # 'words')
                    for w in re.split('(<.+?>|\s)', wlist[i + 1]):

                        ## uncommented in Rein's version:
                        ## CONDITION: if the current <qe/> + 1 has an end sentence tag,
                        ## means i+1 is a sentence (not a suspension). Ignore it
                        #if re.findall('</?s>', w):
                        #    tag = True
                        #    break

                        # search for lettered words only
                        # means i+1 is a suspension
                        if re.findall('[a-zA-Z]', w) and w.find('<') == -1:
                            # if we've arrived at an actual word, continue to next word
                            # and add to word count
                            wordCount += 1

                    # if there are more than 4 words (and no tag), label sls
                    if wordCount > 4 and tag == False:

                        # add sls to <qe> tag
                        # sls following qe, sle preceding qs
                        wlist[i] = '<qe/><sls/>'
                        wlist[i + 2] = '<sle/><qs/>'

                    elif wordCount > 0 and tag == False:
                        wlist[i] = '<qe/><sss/>'
                        wlist[i + 2] = '<sse/><qs/>'

        # e = etree.fromstring(''.join(wlist))
        # p.getparent().replace(p, e)

        # d. glue list of words
        para_new = ''.join(wlist)

        # print new paragraph to appropriate place in XML tree
        nodetree = etree.fromstring('%s' % para_new)
        # replace old paragraph nodes with new ones
        for c in p.getchildren():
            p.remove(c)
        for n in nodetree:
            p.append(n)

    return tree

if __name__ == '__main__':
    tree = etree.parse(sys.argv[1])
    tree = suspensions(tree)
    tree.write(sys.argv[2])

#==============================================================================
      # Rein's alternative:
      # d. glue list of words
#     para_new = ''.join(wlist)
#
# print new paragraph to appropriate place in XML tree
#     nodetree = etree.fromstring('%s' % para_new)
# replace old paragraph nodes with new ones
#     for c in para.getchildren():
#         para.remove(c)
#     for n in nodetree:
#         para.append(n)
#
# new_tree = etree.tostring(tree)
# susp_tag.write(new_tree)
# break
#==============================================================================

# print etree.tostring(tree)