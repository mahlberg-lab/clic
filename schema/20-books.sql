BEGIN;

-- We need this for GIST tokens on book_id INT as well as ranges.
CREATE EXTENSION btree_gist;

/*
TODO: Versioning
* Before we versioned the entire thing. Now we could:
  * Have a separate version column for book? corpus?
  * At what point are things immutable?
*/

CREATE TABLE IF NOT EXISTS book (
    book_id SERIAL,
    PRIMARY KEY (book_id),

    name TEXT NOT NULL,
    UNIQUE (name),

    content TEXT
    -- TODO: Include title/author here, instead of extracting from text?
    -- TODO: What about year? Can we include that in the corpora text? Would allow, e.g. all 19thC texts
);
COMMENT ON TABLE  book IS 'Book name & contents';
COMMENT ON COLUMN book.name IS 'Short name of book, e.g. TTC';
COMMENT ON COLUMN book.content IS 'Full text contents of book';
CREATE UNIQUE INDEX IF NOT EXISTS book_name_book_id ON book(name, book_id); -- TODO: To act as lookup


CREATE TABLE IF NOT EXISTS token (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    crange INT4RANGE NOT NULL CHECK (UPPER(crange) > LOWER(crange)),
    PRIMARY KEY (book_id, crange),

    ttype TEXT NOT NULL,
    ordering INT NOT NULL  -- TODO: Do we even need it, vs. LOWER(crange)?
);
COMMENT ON TABLE  token IS 'Tokens within a book';
COMMENT ON COLUMN token.ttype IS 'Token type, i.e. normalised token';
COMMENT ON COLUMN token.crange IS 'Character range to find this token at';
COMMENT ON COLUMN token.ordering IS 'Position of this token in chapter';
CREATE INDEX IF NOT EXISTS gist_token_book_id_crange ON token USING GIST (book_id, crange);
COMMENT ON INDEX gist_token_book_id_crange IS 'Finding tokens in a range, joining to regions';
CREATE INDEX IF NOT EXISTS token_book_id_lower_crange ON token (book_id, LOWER(crange));
COMMENT ON INDEX token_book_id_lower_crange IS 'Joining with a scalar equivalent to the PK';
CREATE INDEX IF NOT EXISTS token_lower_crange ON token (LOWER(crange));
COMMENT ON INDEX token_lower_crange IS 'Sorting on LOWER(crange)';
CREATE INDEX IF NOT EXISTS token_ordering ON token (ordering);
COMMENT ON INDEX token_ordering IS 'Allows us to select tokens around given ones';
-- TODO: Could use trgm? https://niallburkley.com/blog/index-columns-for-like-in-postgres/


CREATE TABLE IF NOT EXISTS region (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    rclass_id INT NOT NULL,
    FOREIGN KEY (rclass_id) REFERENCES rclass(rclass_id),
    crange INT4RANGE NOT NULL CHECK (UPPER(crange) > LOWER(crange)),
    PRIMARY KEY (book_id, rclass_id, crange), -- TODO: Is this being unique correct? Are there regions that get nested within themselves?

    rvalue INT NULL
);
COMMENT ON TABLE  region IS 'Regions within a book';
COMMENT ON COLUMN region.rvalue IS 'Value associated with range, e.g. chapter number';
COMMENT ON COLUMN region.crange IS 'Character range this applies to';
CREATE INDEX IF NOT EXISTS region_rclass_id ON region (rclass_id);
COMMENT ON INDEX region_rclass_id IS 'Get regions by rclass';
CREATE INDEX IF NOT EXISTS gist_region_book_id_crange ON region USING GIST (book_id, crange);
COMMENT ON INDEX gist_region_book_id_crange IS 'Finding regions in a range, joining to tokens';
CREATE INDEX IF NOT EXISTS region_book_id_lower_crange ON region (book_id, LOWER(crange));
COMMENT ON INDEX region_book_id_lower_crange IS 'Sorting on LOWER(crange)';


CREATE OR REPLACE FUNCTION tokens_in_crange(in_book_id INT, in_crange INT4RANGE) RETURNS TABLE(crange INT4RANGE) STABLE AS
$BODY$
    SELECT t.crange
      FROM token t
      WHERE t.book_id = in_book_id AND t.crange <@ in_crange
      ORDER BY LOWER(t.crange)
$BODY$ LANGUAGE sql;
COMMENT ON FUNCTION public.tokens_in_crange(book_id INT, crange INT4RANGE) IS 'Get all tokens within the given crange';


DROP MATERIALIZED VIEW IF EXISTS book_metadata;
CREATE MATERIALIZED VIEW book_metadata AS
    SELECT r.book_id,
           r.rclass_id,
           r.rvalue,
           SUBSTRING(b.content, LOWER(r.crange) + 1, (UPPER(r.crange) - LOWER(r.crange))) AS content
      FROM region r, book b, rclass rc
     WHERE b.book_id = r.book_id
       AND r.rclass_id = rc.rclass_id
       AND rc.name IN (
           'metadata.title',
           'metadata.author',
           'chapter.title');
COMMENT ON MATERIALIZED VIEW book_metadata IS 'Extracted metadata from book contents';
CREATE INDEX IF NOT EXISTS book_metadata_rclass_id ON book_metadata(rclass_id);
COMMENT ON INDEX book_metadata_rclass_id IS 'Select metadata by type (e.g. author)';


DROP MATERIALIZED VIEW IF EXISTS book_word_count;
CREATE MATERIALIZED VIEW book_word_count AS
    SELECT r.book_id,
           r.rclass_id,
           r.rvalue,
           (
               SELECT COUNT(t.ttype)
                 FROM token t
                WHERE t.book_id = r.book_id AND t.crange <@ r.crange
           ) word_count
      FROM region r, rclass rc
     WHERE r.rclass_id = rc.rclass_id
       AND rc.name IN (
               'chapter.text',
               'quote.quote',
               'quote.nonquote',
               'quote.suspension.short',
               'quote.suspension.long');
COMMENT ON MATERIALIZED VIEW book_word_count IS 'Count words within a selection of regions';


CREATE OR REPLACE FUNCTION refresh_book_materialized_views()
RETURNS VOID SECURITY DEFINER LANGUAGE PLPGSQL
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW book_metadata;
    REFRESH MATERIALIZED VIEW book_word_count;
END $$;
COMMENT ON FUNCTION refresh_book_materialized_views() IS 'Rebuild materialized views based on book contents';


COMMIT;
