Uploading new texts
===================

First you need to turn copies of the texts from the corpora repository into XML. For example::

    (cd annotation && ./annotate.sh ../corpora/ChiLit ./ChiLit_out)

Once this has finished and you have confirmed the process worked, you can ingest the XML output into CLiC::

    ./server/bin/store_documents annotation/ChiLit_out/final/
