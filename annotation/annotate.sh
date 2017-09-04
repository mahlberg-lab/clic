#!/bin/bash

# __author__ = "Catherine Smith, Matthew Brook O'Donnell, J. de Joode" (in arbirary order)

# runs the paragraphs and find_extra_chapter_title scripts of a directory of text file
# the file needs to be run as
#     ./annotate.sh input output
#
# where input and output are the names of a directory (without a backslash at the end)

STARTTIME=$(date +%s)

SCRIPT_DIR=$( pwd )

PYTHON="$(pwd)/bin/python"

# Convert the relatives path into absolute ones by moving in the dir and running pwd
INPUT_DIR=$1
cd $INPUT_DIR && INPUT_DIR=$( pwd ) && cd $SCRIPT_DIR

OUTPUT_DIR=$2
cd $OUTPUT_DIR && OUTPUT_DIR=$( pwd ) && cd $SCRIPT_DIR

# Run the scripts for each file in the INPUT_DIR
cd $INPUT_DIR

for i in $( ls | grep ".txt" ); do
	echo '--------------------------------------------------'
	echo 'Creating Base XML: ' $i

	nf=$i
	nf=${nf/.txt/.xml}

	echo 'Stage 1a -- basic paragraph extraction'
	${PYTHON} $SCRIPT_DIR/paragraphs.py $i > $SCRIPT_DIR/tmp-paragraphs-1.xml

	echo 'Stage 1b -- numbering paragraphs and finding parts of the title'
	${PYTHON} $SCRIPT_DIR/paragraphs_find_extra_chapter_titles.py $SCRIPT_DIR/tmp-paragraphs-1.xml > $SCRIPT_DIR/tmp-paragraphs-2.xml
	cp $SCRIPT_DIR/tmp-paragraphs-2.xml $OUTPUT_DIR/paragraphs/$nf

	echo 'Stage 2 -- extracting sentences'

	${PYTHON} $SCRIPT_DIR/sentences.py $SCRIPT_DIR/tmp-paragraphs-2.xml > $SCRIPT_DIR/tmp-sentences.xml
	cp $SCRIPT_DIR/tmp-sentences.xml $OUTPUT_DIR/sentences/$nf

	echo 'Stage 3 -- adding milestones for quotes'

	${PYTHON} $SCRIPT_DIR/quotes.py $SCRIPT_DIR/tmp-sentences.xml > $SCRIPT_DIR/tmp-quotes.xml
	cp $SCRIPT_DIR/tmp-quotes.xml $OUTPUT_DIR/quotes/$nf

	echo 'Stage 4 -- adding milestones for suspensions'

	${PYTHON} $SCRIPT_DIR/suspensions.py $SCRIPT_DIR/tmp-quotes.xml > $SCRIPT_DIR/tmp-suspensions.xml
	cp $SCRIPT_DIR/tmp-suspensions.xml $OUTPUT_DIR/suspensions/$nf

	echo 'Stage 5 -- adding milestones for alternative quotes'

	${PYTHON} $SCRIPT_DIR/alternativequotes.py $SCRIPT_DIR/tmp-suspensions.xml > $SCRIPT_DIR/tmp-alternativequotes.xml
	cp $SCRIPT_DIR/tmp-alternativequotes.xml $OUTPUT_DIR/alternativequotes/$nf

	echo 'Stage 6 -- adding milestones for alternative suspensions'

	${PYTHON} $SCRIPT_DIR/alternativesuspensions.py $SCRIPT_DIR/tmp-alternativequotes.xml > $SCRIPT_DIR/tmp-alternativesuspensions.xml
	cp $SCRIPT_DIR/tmp-alternativesuspensions.xml $OUTPUT_DIR/alternativesuspensions/$nf

	echo 'Writing the resuls to final, with stylesheet declaration'
	echo '<?xml-stylesheet href="/styles.css"?>' | cat - $SCRIPT_DIR/tmp-alternativesuspensions.xml > $OUTPUT_DIR/final/$nf
done

echo 'Finished and now cleaning up. Find your results in the directory `final` in your output directory.'
cd $SCRIPT_DIR && rm tmp*.xml

ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds to complete this annotation."
