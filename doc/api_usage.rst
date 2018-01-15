CLiC API
========

.. contents::
    :local:

Overview
--------

Any data available through the `CLiC web interface <http://clic.bham.ac.uk/>`_ is also available by directly calling the *CLiC API*.
The CLiC API returns a JSON representation of the CLiC data, which means that the data can be retrieved directly using any programming language.
To get you started we have written some example code for both Python and R.

The sample code is for the *corpora* and *subset* endpoints.
The corpora endpoint is used to retrieve the list of resources available in CLiC.
This can then be used by your code to filter or select the resources you want to fetch (see the example usage).
In the example code the corpora endpoint is called using the ``get_lookup()`` function which returns content something like::

    > lookup
         corpus                      author     id               title
      1: ChiLit            Agnes Strickland  rival   The Rival Crusoes
      2: ChiLit                 Andrew Lang prigio       Prince Prigio
      3: ChiLit           Ann Fraser Tytler  leila       Leila at Home
     ---                                                              
    136:    ntc              Wilkie Collins   arma            Armadale
    137:    ntc              Wilkie Collins wwhite  The Woman in White
    138:    ntc William Makepeace Thackeray vanity         Vanity Fair

The subset endpoint is used to retrieve tokenized text for all or parts of one or more of the corpora.
This endpoint is called 'subset' because you can restrict the retrieved tokens to a specific subset of the whole text, these subsets are: quoted text, non-quoted text, long suspensions or short suspensions.
In the example code the subset endpoint is called using the ``get_tokens()`` function.
The subset endpoint is documented at `server/clic/subset.py <../server/clic/subset.py>`_.

The *cluster* endpoint is used to retrieve n-grams and their counts.
In the example code the clusters endpoint is called using the ``get_clusters()`` function.
The cluster endpoint is documented at `server/clic/cluster.py <../server/clic/cluster.py>`_.

We would be interested to hear about how you use the CLiC API and are always happy to consider CLiC related guest posts for the `CLiC blog <https://blog.bham.ac.uk/clic-dickens/>`_.
To let us know how you are using the CLiC API, to give us feedback, or if you need any help that you cannot find here or through the `CLiC homepage <https://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic/>`_ you can contact us at `clic@contacts.bham.ac.uk <clic@contacts.bham.ac.uk>`_.

To help us understand who is using the API, when writing code to access the API please set the "User-Agent" header to something that identifies you or your application.

The CLiC API uses the legacy names for the CLiC corpora. The following table gives the correspondence between the corpora names as seen in the CLiC web interface and those used by the CLiC API.

+--------------+--------------+-------------------------------------------+
| CLiC Web     | CLiC API     | Description                               |
+==============+==============+===========================================+
| ``DNov``     | ``dickens``  | Dickens's Novels                          |
+--------------+--------------+-------------------------------------------+
| ``19C``      | ``ntc``      | 19th Century Reference Corpus             |
+--------------+--------------+-------------------------------------------+
| ``ChiLit``   | ``ChiLit``   | 19th Century Children's Literature Corpus |
+--------------+--------------+-------------------------------------------+
| ``ArTs``     | ``Other``    | Additional Requested Texts                |
+--------------+--------------+-------------------------------------------+

Example code
------------

Python 3
^^^^^^^^

.. code-block:: python

    import json
    from operator import itemgetter
    from collections import OrderedDict
    import requests
    import pandas as pd

    UA = "CLiC API Example Python3 Code"  # user agent !! CHANGE ME !!
    HOSTNAME = "clic.bham.ac.uk"

    def api_request(endpoint, query=None):
        """
        Makes the API requests.
        Returns the endpoint specific data structure as a python structure.

        - endpoint: see the inline docs in /server/clic
        - query: endpoint specific parameters as a querystring
        """
        if query is None:
            uri = 'http://%s/api/%s' % (HOSTNAME, endpoint)
        else:
            uri = 'http://%s/api/%s?%s' % (HOSTNAME, endpoint, query)
        resp = requests.get(uri, headers={'User-agent': UA, 'Accept': 'application/json'})
        try:
            rv = resp.json()
        except json.decoder.JSONDecodeError:
            print("API request did not return valid JSON")
        return rv

    def get_lookup():
        """
        Returns a pandas DataFrame listing the texts for each of the available corpora.
        """
        rv = api_request(endpoint="corpora")
        d = []
        for corpus in rv['corpora']:
            corpus_id = corpus['id']
            for book in corpus['children']:
                d.append({'corpus' : corpus_id, 'author' : book['author'], \
                          'shortname' : book['id'], 'title': book['title']})
        df = pd.DataFrame(d, columns=['corpus', 'author', 'shortname', 'title'])
        df.sort_values(['corpus', 'author', 'title'], inplace=True, ascending=True)
        df.reset_index(inplace=True, drop=True)
        return df

    def get_tokens(shortname, subset=None, lowercase=True, punctuation=False):
        """
        Fetches tokens using the 'subset' endpoint.
        Returns a list of tokens.

        - shortname: can be any value from the 'corpus' or 'shortname' columns returned
              by get_lookup() can be a string or a list of strings
        - subset: any one of "shortsus", "longsus", "nonquote", "quote"
        - lowercase: boolean indicating if the tokens should be transformed to lower case
        - punctuation: boolean indicating if punctuation tokens should be included
        """
        if isinstance(shortname, str):
            shortname = [shortname]
        query = '&'.join(["corpora=%s" % sn for sn in shortname])
        if subset is not None:
            if subset not in ["shortsus", "longsus", "nonquote", "quote"]:
                raise ValueError('bad subset parameter: "%s"' % subset)
            query = query + "&subset=%s" % subset
        rv = api_request(endpoint="subset", query=query)
        if punctuation:
            tokens = [j for i in rv['data'] for j in i[0][:-1]]
        else:
            tokens = [j for i in rv['data'] for j in [i[0][:-1][k] for k in i[0][-1]]]
        if lowercase:
            return [i.lower() for i in tokens]
        return tokens

    def get_clusters(shortname, length, cutoff=5, subset=None):
        """
        Fetches n-grams using the 'cluster' endpoint.
        Returns a OrderedDict of clusters to counts.

        - shortname: can be any value from the 'corpus' or 'shortname' columns returned
              by get_lookup() can be a string or a list of strings
        - length: cluster length to search for, one of 1/3/4/5 (NB: There is no 2)
        - cutoff: [default: 5] the cutoff frequency, if a cluster occurs less times
              than this it is not returned
        - subset: [optional] any one of "shortsus", "longsus", "nonquote", "quote"
        """
        if isinstance(shortname, str):
            shortname = [shortname]
        query = '&'.join(["corpora=%s" % sn for sn in shortname])
        if subset is not None:
            if subset not in ["shortsus", "longsus", "nonquote", "quote"]:
                raise ValueError('bad subset parameter: "%s"' % subset)
            query = query + "&subset=%s" % subset
        query = query + "&clusterlength=%d&cutoff=%d" % (length, cutoff)
        rv = api_request(endpoint="cluster", query=query)
        clusters = OrderedDict(sorted(rv['data'], key=itemgetter(1), reverse=True))
        return clusters


Find out what texts are available::

    >>> lookup = get_lookup()
    >>> lookup.head()
       corpus             author shortname                       title
    0  ChiLit   Agnes Strickland     rival           The Rival Crusoes
    1  ChiLit        Andrew Lang    prigio               Prince Prigio
    2  ChiLit  Ann Fraser Tytler     leila               Leila at Home
    3  ChiLit        Anna Sewell    beauty                Black Beauty
    4  ChiLit     Beatrix Potter     bunny  The Tale Of Benjamin Bunny
    >>> lookup.tail()
        corpus                       author shortname                          title
    133    ntc                 Thomas Hardy    native       The Return of the Native
    134    ntc               Wilkie Collins    Antoni  Antonina, or the Fall of Rome
    135    ntc               Wilkie Collins      arma                       Armadale
    136    ntc               Wilkie Collins    wwhite             The Woman in White
    137    ntc  William Makepeace Thackeray    vanity                    Vanity Fair

Filter what is available::

    >>> lookup[lookup['author'] == "Thomas Hardy"]
        corpus        author shortname                      title
    131    ntc  Thomas Hardy      Jude           Jude the Obscure
    132    ntc  Thomas Hardy      Tess  Tess of the D'Urbervilles
    133    ntc  Thomas Hardy    native   The Return of the Native

Fetch the tokens for a specific text::

    >>> tokens = get_tokens(shortname='leila')
    >>> len(tokens)
    63026
    >>> tokens[0:9]
    ['it', 'was', 'the', 'intention', 'of', 'the', 'writer', 'of', 'the']

Fetch the tokens for all quotes text in novels by Jane Austen::

    >>> wanted = [sn for sn in lookup[lookup['author'] == "Jane Austen"]['shortname']]
    >>> wanted
    ['ladysusan', 'mansfield', 'northanger', 'sense', 'emma', 'persuasion', 'pride']

    >>> austen_quotes = get_tokens(shortname=wanted, subset="quote")
    >>> len(austen_quotes)
    307445
    >>> austen_quotes[0:9]
    ['poor', 'miss', 'taylor', 'i', 'wish', 'she', 'were', 'here', 'again']

Keep each text separate::

    >>> austen_quotes = {}
    >>> for sn in wanted:
    ...     austen_quotes[sn] = get_tokens(shortname=sn, subset="quote")
    ...
    >>> {key:len(value) for key,value in austen_quotes.items()}
    >>> print(json.dumps({key:len(value) for key,value in austen_quotes.items()}))
    {
      "ladysusan": 2791,
      "mansfield": 62013,
      "northanger": 28937,
      "sense": 51744,
      "emma": 80319,
      "persuasion": 28653,
      "pride": 52988
    }
    >>> austen_quotes['emma'][0:9]
    ['poor', 'miss', 'taylor', 'i', 'wish', 'she', 'were', 'here', 'again']

An now lets get some clusters for the Jane Austen novels::

    >>> austen_clusters = get_clusters(shortname=wanted, length=5, cutoff=5, subset="quote")
    >>> print(json.dumps(austen_clusters, indent=2))
    {
      "i do not know what": 26,
      "i am sure you will": 16,
      "i do not know that": 16,
      "i do not mean to": 16,
      "and i am sure i": 16,
      "i have no doubt of": 14,
      "i do not think i": 14,
      "i am sure i should": 13,
      "i am sure i do": 11,
      "i do not pretend to": 11,
      ...


R
^

.. code-block:: R

    library(httr)
    library(jsonlite)
    library(data.table)

    UA <- "CLiC API Example R Code"  # user agent !! CHANGE ME !!
    HOSTNAME <- "clic.bham.ac.uk"

    # Makes the API requests.
    # Returns the endpoint specific data structure.
    #
    # - endpoint: see the inline docs in /server/clic
    # - query: endpoint specific parameters as a querystring
    #
    api_request <- function(
        endpoint = c("subset", "corpora", "cluster"),
        query = NULL
    ) {
        endpoint <- match.arg(endpoint)
        uri <- modify_url("",
            scheme = "http",
            hostname = HOSTNAME,
            path = sprintf("/api/%s", endpoint),
            query = ifelse(is.null(query), "", query)
        )
        req <- GET(uri, add_headers('User-Agent' = UA, 'Accept' = "application/json"))
        if (http_error(req)) {
            stop(sprintf("Request failed: status %s - URL '%s'", status_code(req), uri))
        }
        # can ignore header so check response
        # https://tools.ietf.org/html/rfc7231#section-5.3.2
        if (http_type(req) != "application/json") {
            stop("API did not return JSON")
        }
        fromJSON( content(req, as = "text", encoding = "UTF-8") )
    }

    # Returns a data.frame listing the texts for each of the available corpora.
    #
    get_lookup <- function() {
        rv <- api_request(endpoint = "corpora")
        DT <- rbindlist(
            rv$corpora$children, fill = TRUE,
            idcol = 'corpus'
        )[ , corpus := rv$corpora$id[corpus]]
        setkeyv(DT, cols = c('corpus', 'author', 'title'))
        return(DT[])
    }

    # Fetches tokens using the 'subset' endpoint.
    # Returns a vector of tokens.
    #
    # - shortname: can be any value from the 'corpus' or 'shortname' columns returned by get_lookup()
    #              can be a string or a list of strings
    # - subset: any one of "shortsus", "longsus", "nonquote", "quote"
    # - lowercase: boolean indicating if the tokens should be transformed to lower case
    # - punctuation: boolean indicating if punctuation tokens should be included
    #
    get_tokens <- function(
        shortname,
        subset = NULL,
        lowercase = TRUE,
        punctuation = FALSE  # includes whitespace
    ) {
        query <- paste(sprintf("corpora=%s", shortname), collapse = "&")
        if(! is.null(subset)) {
            subset <- match.arg(subset, c("shortsus", "longsus", "nonquote", "quote"))
            query <- sprintf("%s&subset=%s", query, subset)
        }
        rv <- api_request(endpoint = "subset", query = query)
        if(punctuation) {
            tokens <- unlist( sapply(rv$data, function(x) {
                head(x[[1]], -1)
            }) )
        } else {
            tokens <- unlist( sapply(rv$data, function(x) {
                head(x[[1]], -1)[as.integer(tail(x[[1]], 1)[[1]])+1]
            }) )
        }
        if(lowercase) {
            tokens <- tolower(tokens)
        }
        return(tokens)
    }

    # Fetches n-grams using the 'cluster' endpoint.
    # Returns a data.frame of clusters to counts.
    #
    # - shortname: can be any value from the 'corpus' or 'shortname' columns returned
    #       by get_lookup() can be a string or a list of strings
    # - length: cluster length to search for, one of 1/3/4/5 (NB: There is no 2)
    # - cutoff: [default: 5] the cutoff frequency, if a cluster occurs less times
    #       than this it is not returned
    # - subset: [optional] any one of "shortsus", "longsus", "nonquote", "quote"
    #
    get_clusters <- function(
        shortname,
        length,
        cutoff = 5,
        subset = NULL
    ) {
        if(! length %in% c(1, 3, 4, 5)) {
            stop(paste0("bad length parameter: '", length, "'"))
        }
        query <- paste(sprintf("corpora=%s", shortname), collapse = "&")
        query <- sprintf("%s&clusterlength=%d&cutoff=%s", query, length, cutoff)
        if(! is.null(subset)) {
            subset <- match.arg(subset, c("shortsus", "longsus", "nonquote", "quote"))
            query <- sprintf("%s&subset=%s", query, subset)
        }
        rv <- api_request(endpoint = "cluster", query = query)
        clusters <- data.frame("cluster" = rv$data[ , 1], "count" = as.integer(rv$data[ , 2]), stringsAsFactors = FALSE)
        clusters <- clusters[order(clusters$count, decreasing = TRUE),]
        rownames(clusters) <- NULL
        return(clusters)
    }


Find out what texts are available::

    > lookup <- get_lookup()
    > lookup
         corpus                      author     id                         title
      1: ChiLit            Agnes Strickland  rival             The Rival Crusoes
      2: ChiLit                 Andrew Lang prigio                 Prince Prigio
      3: ChiLit           Ann Fraser Tytler  leila                 Leila at Home
      4: ChiLit                 Anna Sewell beauty                  Black Beauty
      5: ChiLit              Beatrix Potter  bunny    The Tale Of Benjamin Bunny
     ---                                                                        
    134:    ntc                Thomas Hardy native      The Return of the Native
    135:    ntc              Wilkie Collins Antoni Antonina, or the Fall of Rome
    136:    ntc              Wilkie Collins   arma                      Armadale
    137:    ntc              Wilkie Collins wwhite            The Woman in White
    138:    ntc William Makepeace Thackeray vanity                   Vanity Fair

Filter what is available::

    > lookup[lookup$author == "Thomas Hardy", ]
       corpus       author     id                     title
    1:    ntc Thomas Hardy   Jude          Jude the Obscure
    2:    ntc Thomas Hardy   Tess Tess of the D'Urbervilles
    3:    ntc Thomas Hardy native  The Return of the Native

Fetch the tokens for a specific text::

    > tokens <- get_tokens('leila')
    > str(tokens)
     chr [1:63026] "it" "was" "the" "intention" "of" "the" "writer" "of" "the" "following" "pages" "to" "have" "bid" "a" "last" "farewell" "to" ...

Fetch the tokens for all quotes text in novels by Jane Austen::

    > wanted <- lookup[lookup$author == "Jane Austen", ]$id
    > wanted
    [1] "ladysusan"  "mansfield"  "northanger" "sense"      "emma"       "persuasion" "pride"     

    > austen_quotes <- get_tokens(wanted, subset = "quote")
    > str(austen_quotes)
     chr [1:307445] "poor" "miss" "taylor" "i" "wish" "she" "were" "here" "again" "what" "a" "pity" "it" "is" "that" "mr" "weston" "ever" "thought" ...

Keep each text separate::

    > austen_quotes <- sapply(wanted, get_tokens, subset = "quote")
    > str(austen_quotes)
    List of 7
     $ ladysusan : chr [1:2791] "i" "like" "this" "man" ...
     $ mansfield : chr [1:62013] "what" "if" "they" "were" ...
     $ northanger: chr [1:28937] "catherine" "grows" "quite" "a" ...
     $ sense     : chr [1:51744] "yes" "he" "would" "give" ...
     $ emma      : chr [1:80319] "poor" "miss" "taylor" "i" ...
     $ persuasion: chr [1:28653] "elliot" "of" "kellynch" "hall" ...
     $ pride     : chr [1:52988] "my" "dear" "mr" "bennet" ...

    > sum(sapply(austen_quotes, length))
    [1] 307445

An now lets get some clusters for the Jane Austen novels::

    > austen_clusters <- get_clusters(shortname = wanted, length = 5, cutoff = 5, subset = "quote")
    > head(austen_clusters, 10)
                   cluster count
    1   i do not know what    26
    2   i am sure you will    16
    3   i do not know that    16
    4     i do not mean to    16
    5      and i am sure i    16
    6   i have no doubt of    14
    7     i do not think i    14
    8   i am sure i should    13
    9       i am sure i do    11
    10 i do not pretend to    11

