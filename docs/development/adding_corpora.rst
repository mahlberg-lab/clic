Uploading new texts
===================

The raw texts for CLiC to process are assumed to be in the corpora repository.
If not already, add the texts to the repository here:
    https://github.com/birmingham-ccr/corpora

Next you need to have CLiC installed on a separate server. Running the import
process on the live server will stop live CLiC working. Install as per the
README, including all current data.

The first stage of the process is in the ``annotation`` directory, which
contains scripts that turn copies of the texts from the corpora repository into
XML.  For example, to convert the ChiLit texts::

    git clone git@github.com:birmingham-ccr/corpora.git corpora
    git clone git@github.com:birmingham-ccr/annotationOutput.git annotationOutput
    # Edit server/cheshire3-server/dbs/dickens/extra_data.json to include any new corpus
    # titles
    cd annotation
    virtualenv .
    ./bin/pip install -r requirements.txt
    ./annotate.sh ../corpora/ChiLit ./annotationOutput/ChiLit

This process will take some time, but eventually will create XML output for
each file, as well as intermediate output for investigation. You can start a
web server to look at the output texts:

    python -m SimpleHTTPServer

...and go to http://localhost:8000/annotationOutput/ There is a ``styles.css``
that the web browser will use to format the output.

Once you have pushed the changes to annotation output, you can view changes here:
https://birmingham-ccr.github.io/annotationOutput/

Once this has finished and you have confirmed the process worked, you can
ingest the XML output into CLiC. Stop any running CLiC processes and run the
following script::

    ./server/bin/store_documents annotationOutput/ChiLit/final/

Restart CLiC, and you should find the new corpora available. Follow the
instructions to upload the cheshire3 content to the live server.
