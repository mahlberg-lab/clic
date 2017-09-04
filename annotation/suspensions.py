import sys
import re

from lxml import etree

# regular expression looks for quotation tags
regex = re.compile('(<q[es]/>)')
tree = etree.parse(sys.argv[1])

# find the middle bit of the qe qs and split on space - count each entry in
# list that contains at least one alpha char if more than 4 long 4 or less short
for p in tree.xpath('//p[s/qe]'):

    # Why is this repeated here:
    p.set('type', 'speech')

    # a. get paragraph paragraph_string
    paragraph_string = etree.tostring(p)

    # b. split by regular expression defined above
    wlist = re.split(regex, paragraph_string)

    # c. run index over listed items in each paragraph
    for i in range(0, len(wlist)):

        # CONDITION: suspensions occur latest two positions before final list
        # item
        # (final list item is </s> </p> and second last item is potentially
        # qs/qe)
        # <qe/>, xxxxxxxxxxxxxxxx, <qs/> : xxx is either a suspension or
        # a non-suspension
        if i + 2 < len(wlist):
            # CONDITION: i is a 'qe' tag and there is only one extra list
            # item between i and 'qs'
            # (there might or might not be a suspension)
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

                    # CONDITION: if the current <qe/> + 1 has an end sentence tag,
                    # means i+1 is a sentence (not a suspension).
                    if re.findall('</?s>', w):
                        # if so don't do anything
                        pass
                        # set tag to True if condition is met as only False ones will be labelled
                        # uncommented in Rein's version:
                        tag = True
                        break

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

#    e = etree.fromstring(''.join(wlist))
#    p.getparent().replace(p, e)

    # d. glue list of words
    para_new = ''.join(wlist)

    # print new paragraph to appropriate place in XML tree
    nodetree = etree.fromstring('%s' % para_new)
    # replace old paragraph nodes with new ones
    for c in p.getchildren():
        p.remove(c)
    for n in nodetree:
        p.append(n)

new_tree = etree.tostring(tree)
print new_tree

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
