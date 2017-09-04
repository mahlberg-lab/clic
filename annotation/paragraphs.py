import sys
import re

lines = open(sys.argv[1]).readlines()
filename = sys.argv[1]
book_abbreviation = filename.split('/')[-1].replace('.txt', '')

p = []
chapter_text = []
stru_text = []
title_text = []

last_line = 0
cnum = 1

headings = True
in_chapter = False
in_contents = False
in_stru = False

PUNCTUATION = ['.', ',', ':', ';', '!', '?']
# 'POSTSCRIPT' in: omf, an, mc (dickens), native, arma, wwhite (19c)
GEN_ChapHeadings = ['POSTSCRIPT']
BR_ChapHeadings = ['Chapter the Last']
# Most are in Jekyll and Sketches:
JEKYLL_ChapHeadings = ['STORY OF THE DOOR', 'SEARCH FOR MR. HYDE',  'DR. JEKYLL WAS QUITE AT EASE', 'THE CAREW MURDER CASE',
                               'INCIDENT OF THE LETTER','REMARKABLE INCIDENT OF DR. LANYON', 'INCIDENT AT THE WINDOW', 'THE LAST NIGHT',
                               'DR. LANYON\'S NARRATIVE', 'HENRY JEKYLL\'S FULL STATEMENT OF THE CASE']
SB_ChapHeadings = ['TO THE YOUNG LADIES', 'THE BASHFUL YOUNG GENTLEMAN', 'THE OUT-AND-OUT YOUNG GENTLEMAN', 'THE VERY FRIENDLY YOUNG GENTLEMAN', 'THE MILITARY YOUNG GENTLEMAN',
                           'THE POLITICAL YOUNG GENTLEMAN', 'THE DOMESTIC YOUNG GENTLEMAN', 'THE CENSORIOUS YOUNG GENTLEMAN', 'THE FUNNY YOUNG GENTLEMAN',
                           'THE THEATRICAL YOUNG GENTLEMAN', 'THE POETICAL YOUNG GENTLEMAN', 'THE \'THROWING-OFF\' YOUNG GENTLEMAN', 'THE YOUNG LADIES\' YOUNG GENTLEMAN',
                           'CONCLUSION', 'AN URGENT REMONSTRANCE, &c', 'THE YOUNG COUPLE', 'THE FORMAL COUPLE', 'THE LOVING COUPLE', 'THE CONTRADICTORY COUPLE',
                           'THE COUPLE WHO DOTE UPON THEIR CHILDREN', 'THE COOL COUPLE', 'THE PLAUSIBLE COUPLE', 'THE NICE LITTLE COUPLE', 'THE EGOTISTICAL COUPLE',
                           'THE COUPLE WHO CODDLE THEMSELVES', 'THE OLD COUPLE', 'PUBLIC LIFE OF MR. TULRUMBLE--ONCE MAYOR OF MUDFOG',
                           'FULL REPORT OF THE FIRST MEETING OF THE MUDFOG ASSOCIATION FOR THE', 'FULL REPORT OF THE SECOND MEETING OF THE MUDFOG ASSOCIATION FOR THE',
                           'THE PANTOMIME OF LIFE', 'SOME PARTICULARS CONCERNING A LION', 'MR. ROBERT BOLTON:  THE \'GENTLEMAN CONNECTED WITH THE PRESS\'',
                           'FAMILIAR EPISTLE FROM A PARENT TO A CHILD AGED TWO YEARS AND TWO']
## Combine all specific chapter headings
SPECIFIC_HEADINGS = GEN_ChapHeadings + BR_ChapHeadings + JEKYLL_ChapHeadings + SB_ChapHeadings

# first line of XML: book id
print "<div0 id=\"%s\" type=\"book\" filename=\"%s\">\n\n" % (book_abbreviation, filename)

# read line by line through the text
for index, line in enumerate(lines):

    # fix known issues in the xml we inherit
    line = re.sub('"resp=', '" resp=', line)
    # ampersand creates trouble for regular expressions
    line = re.sub('&', '&amp;', line)

    # if we are in contents or not switch the value and while in it print the line
    if re.search('</?cont>', line):  # matches <cont> and </cont>
        in_contents = not in_contents
        print line

    # TODO DRY
    elif filename.endswith('mary.txt') and re.match(
            '^(C(HAPTER|hapter) ([LVIX0-9]+|[A-Z]+)|[IXVL]+\s*$|Book [LVIX0-9]+ Chapter [LVIX0-9]+\s*$|STAVE [IVLX]+:)|[IXVL]+\.\s+\S',
            line) and not in_contents or line.strip() in SPECIFIC_HEADINGS:
        if in_chapter:
            print "\n\n<div id=\"%s.%i\" book=\"%s\" type=\"chapter\" num=\"%i\">\n<title>%s</title>\n\n%s</div>" % (
            book_abbreviation, cnum, book_abbreviation, cnum, ' '.join(title_text),
            '\n\n'.join(chapter_text))  # NB printed at the start of the next chapter
            title_text = []
            chapter_text = []  # reset the chapter lines array
            cnum += 1  # increment chapter number
        title_text.append(line.strip())
        last_line = index
        # ready to run next loop below and write chapter xml when on next line (index + 1)
        in_chapter = True

    # match chapter opening
    # [IXVL]+\.\s+\S| taken out of regex because breaks with I. occurs at beginning of line in running text and is not
    # needed in Dickens books!
    # FIXME [IXVL]+\.\s+\S| only needed for mary - annotated in separate script
    # ADDED TO REGEX FOR FRANKENSTEIN: Letter [0-9]
    elif re.match(
            '^(C(HAPTER|hapter) ([IVXL0-9]+|[A-Z]+)|[IVXL]+\s*$|Book [LVIX0-9]+ Chapter [LVIX0-9]+\s*$|STAVE [IVLX]+:)|Letter [0-9]',
            line) and not in_contents or line.strip() in SPECIFIC_HEADINGS:
        if in_chapter:
            print "\n\n<div id=\"%s.%i\" book=\"%s\" type=\"chapter\" num=\"%i\">\n<title>%s</title>\n\n%s</div>" % (
            book_abbreviation, cnum, book_abbreviation, cnum, ' '.join(title_text),
            '\n\n'.join(chapter_text))  # NB printed at the start of the next chapter
            title_text = []
            chapter_text = []  # reset the chapter lines array
            cnum += 1  # increment chapter number
        title_text.append(line.strip())
        last_line = index
        # ready to run next loop below and write chapter xml when on next line (index + 1)
        in_chapter = True

    elif in_chapter:
        if index == last_line + 1 and re.search('\S', line) and not re.search('[a-z]', line) and not line.strip()[
            -1] in PUNCTUATION and len(title_text):
            title_text.append(line.strip())
            last_line = index
        elif re.search('<stru>', line) and re.search('</stru>', line):
            chapter_text.append(line)
        elif re.search('</?stru>', line):
            in_stru = not in_stru
            chapter_text.append(line)
        elif in_stru:
            chapter_text.append(line)
        elif (line == '\n' or line == '\r\n') and len(p) > 0:
            chapter_text.append('<p>%s</p>' % ' '.join(p))
            p = []
        else:
            if len(line.strip()) > 0 and re.search('[a-zA-z]', line):
                p.append(line.strip())
            else:
                last_line = last_line + 1
    else:
        print line

print "\n\n<div id=\"%s.%i\" book=\"%s\" type=\"chapter\" num=\"%i\">\n<title>%s</title>\n\n%s</div>" % (
book_abbreviation, cnum, book_abbreviation, cnum, ' '.join(title_text), '\n\n'.join(chapter_text))
print "\n\n</div0>"
