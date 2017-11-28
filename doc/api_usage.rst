CLiC API usage
==============

The CLiC API can also be queried directly and JSON returned.

For tracking purposes, please set the User Agent and "X-Clic-Client" header to
something that identifies your application.

For more information on particular endpoints, please see the documentation in:

* `server/clic/subset.py <../server/clic/subset.py>`_: For text subsets (e.g. quotes / suspensions) or entire chapters
* `server/clic/cluster.py <../server/clic/cluster.py>`_: For clusters

Code examples
=============

R
-

.. code-block:: R

    library(httr)
    library(jsonlite)
    library(data.table)

    UA <- "CLiC_API_Example_R_Code"  # user agent !! CHANGE ME !!

    api_request <- function(
        endpoint = c("subset", "corpora"),
        query = NULL,
        hostname = "clic.bham.ac.uk"
    ) {
        endpoint <- match.arg(endpoint)
        uri <- modify_url("",
            scheme = "http",
            hostname = hostname,
            path = paste0("/api/", endpoint),
            query = ifelse(is.null(query), "", query)
        )
        req <- GET(uri, add_headers('X-Clic-Client' = UA))
        if (http_error(req)) {
            stop(sprintf("Request failed: status %s - URL '%s'", status_code(req), uri))
        }
        if (http_type(req) != "application/json") {
            stop("API did not return JSON")
        }
        fromJSON( content(req, as = "text", encoding = "UTF-8") )
    }


    get_lookup <- function() {
        rv <- api_request(endpoint = "corpora")
        DT <- rbindlist(
            rv$corpora$children, fill = TRUE,
            idcol = 'corpus'
        )[ , corpus := rv$corpora$id[corpus]]
        setkey(DT)
        return(DT[])
    }

    ##  lookup <- get_lookup()
    ##
    ##  > lookup
    ##       corpus                      author     id                         title
    ##    1: ChiLit            Agnes Strickland  rival             The Rival Crusoes
    ##    2: ChiLit                 Andrew Lang prigio                 Prince Prigio
    ##    3: ChiLit           Ann Fraser Tytler  leila                 Leila at Home
    ##    4: ChiLit                 Anna Sewell beauty                  Black Beauty
    ##    5: ChiLit              Beatrix Potter  bunny    The Tale Of Benjamin Bunny
    ##   ---                                                                        
    ##  134:    ntc                Thomas Hardy native      The Return of the Native
    ##  135:    ntc              Wilkie Collins Antoni Antonina, or the Fall of Rome
    ##  136:    ntc              Wilkie Collins   arma                      Armadale
    ##  137:    ntc              Wilkie Collins wwhite            The Woman in White
    ##  138:    ntc William Makepeace Thackeray vanity                   Vanity Fair


    get_tokens <- function(
        shortname,
        subset = NULL,
        lowercase = TRUE,
        punctuation = FALSE
    ) {
        query <- paste(paste0("corpora=", shortname), collapse = "&")
        if(! is.null(subset)) {
            subset <- match.arg(subset, c("shortsus", "longsus", "nonquote", "quote"))
            query <- paste0(query, "&subset=", subset )
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

    ##  > tokens <- get_tokens('leila')
    ##  
    ##  > str(tokens)
    ##   chr [1:63026] "it" "was" "the" "intention" "of" "the" "writer" "of" "the" "following" "pages" ...

    ##  > wanted <- lookup[lookup$author == "Jane Austen", ]$id
    ##  > wanted
    ##  [1] "emma"       "persuasion" "pride"      "ladysusan"  "mansfield"  "northanger" "sense"     
    ##  
    ##  > austin_quotes <- get_tokens(wanted, subset = "quote")
    ##  > str(austin_quotes)
    ##   chr [1:307445] "poor" "miss" "taylor" "i" "wish" "she" "were" "here" "again" "what" "a" "pity" "it" "is" "that" "mr" "weston" "ever" "thought" ...

    ##  > austin_quotes <- sapply(wanted, get_tokens, subset = "quote")
    ##  > str(austin_quotes)
    ##  List of 7
    ##   $ emma      : chr [1:80319] "poor" "miss" "taylor" "i" ...
    ##   $ persuasion: chr [1:28653] "elliot" "of" "kellynch" "hall" ...
    ##   $ pride     : chr [1:52988] "my" "dear" "mr" "bennet" ...
    ##   $ ladysusan : chr [1:2791] "i" "like" "this" "man" ...
    ##   $ mansfield : chr [1:62013] "what" "if" "they" "were" ...
    ##   $ northanger: chr [1:28937] "catherine" "grows" "quite" "a" ...
    ##   $ sense     : chr [1:51744] "yes" "he" "would" "give" ...
    ##  > sum(sapply(austin_quotes, length))
    ##  [1] 307445

