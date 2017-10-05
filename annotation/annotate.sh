#!/bin/bash

# __author__ = "Catherine Smith, Matthew Brook O'Donnell, J. de Joode" (in arbirary order)

# runs the paragraphs and find_extra_chapter_title scripts of a directory of text file
# the file needs to be run as
#     ./annotate.sh input output
#
# where input and output are the names of a directory (without a backslash at the end)
# 
# The input directory should have the same name as the subcorpus you are importing, e.g.
# ntc / dickens / ChiLit

STARTTIME=$(date +%s)

SCRIPT_DIR=$( pwd )

PYTHON="$(pwd)/bin/python"

# Convert the relatives path into absolute ones, dereference globs, input directories
INPUT=$([ -d "$1" ] && readlink -f "$1/*.txt" || readlink -f "$1")
OUTPUT_DIR=$(readlink -f "$2")

# Make sure all output dirs exist
mkdir -p $OUTPUT_DIR/{ascii,paragraphs,sentences,quotes,suspensions,alternativequotes,alternativesuspensions,final}

for i in ${INPUT}; do
	nf="$(basename $i .txt).xml"

	echo '--------------------------------------------------'
	echo "Input -- $i"

	echo "Stage 1 -- ascii7: $OUTPUT_DIR/ascii/$nf"
	perl -C -MText::Unidecode -n -e'print unidecode($_)' $i > $OUTPUT_DIR/ascii/$(basename $i)

	echo "Stage 1 -- paragraph extraction: $OUTPUT_DIR/paragraphs/$nf"
	${PYTHON} $SCRIPT_DIR/paragraphs.py $OUTPUT_DIR/ascii/$(basename $i) $OUTPUT_DIR/paragraphs/$nf

	echo "Stage 2 -- extracting sentences: $OUTPUT_DIR/sentences/$nf"
	${PYTHON} $SCRIPT_DIR/sentences.py $OUTPUT_DIR/paragraphs/$nf $OUTPUT_DIR/sentences/$nf

	echo "Stage 3 -- adding milestones for quotes: $OUTPUT_DIR/quotes/$nf"
	${PYTHON} $SCRIPT_DIR/quotes.py $OUTPUT_DIR/sentences/$nf $OUTPUT_DIR/quotes/$nf

	echo "Stage 4 -- adding milestones for suspensions: $OUTPUT_DIR/suspensions/$nf"
	${PYTHON} $SCRIPT_DIR/suspensions.py $OUTPUT_DIR/quotes/$nf $OUTPUT_DIR/suspensions/$nf

	echo "Stage 5 -- adding milestones for alternative quotes: $OUTPUT_DIR/alternativequotes/$nf"
	${PYTHON} $SCRIPT_DIR/alternativequotes.py $OUTPUT_DIR/suspensions/$nf $OUTPUT_DIR/alternativequotes/$nf

	echo "Stage 6 -- adding milestones for alternative suspensions: $OUTPUT_DIR/alternativesuspensions/$nf"
	${PYTHON} $SCRIPT_DIR/alternativesuspensions.py $OUTPUT_DIR/alternativequotes/$nf $OUTPUT_DIR/alternativesuspensions/$nf

	echo "Final -- adding stylesheet declaration: $OUTPUT_DIR/final/$nf"
	echo '<?xml-stylesheet href="/styles.css"?>' | cat - $OUTPUT_DIR/alternativesuspensions/$nf > $OUTPUT_DIR/final/$nf
done

echo 'Finished and now cleaning up. Find your results in the directory `final` in your output directory.'

ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete this annotation."
