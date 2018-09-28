BEGIN;

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
);
COMMENT ON TABLE  book IS 'Book name & contents';
COMMENT ON COLUMN book.name IS 'Short name of book, e.g. TTC';
COMMENT ON COLUMN book.content IS 'Full text contents of book';
CREATE UNIQUE INDEX IF NOT EXISTS book_name_book_id ON book(name, book_id); -- TODO: To act as lookup


CREATE TABLE IF NOT EXISTS token (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),

    crange INT8RANGE NOT NULL,
    ttype TEXT NOT NULL,
    ordering INT NOT NULL  -- TODO: INT enough?
);
COMMENT ON TABLE  token IS 'Tokens within a book';
COMMENT ON COLUMN token.ttype IS 'Token type, i.e. normalised token';
COMMENT ON COLUMN token.crange IS 'Character range to find this token at';
COMMENT ON COLUMN token.ordering IS 'Position of this token in chapter';
CREATE INDEX IF NOT EXISTS gist_token_crange ON token USING GIST (crange);  -- Allows us to discover what's at this point
CREATE INDEX IF NOT EXISTS token_ordering ON token (ordering);  -- Allows us to select tokens around given ones
-- TODO: Could use trgm? https://niallburkley.com/blog/index-columns-for-like-in-postgres/


CREATE TABLE IF NOT EXISTS region (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),

    crange INT8RANGE NOT NULL,
    rclass_id INT NOT NULL,
    FOREIGN KEY (rclass_id) REFERENCES rclass(rclass_id),
    rvalue INT NULL
);
COMMENT ON TABLE  region IS 'Regions within a book';
COMMENT ON COLUMN region.rvalue IS 'Value associated with range, e.g. chapter number';
COMMENT ON COLUMN region.crange IS 'Character range this applies to';
CREATE INDEX IF NOT EXISTS region_rclass_id ON region (rclass_id);  -- Get regions by rclass
CREATE INDEX IF NOT EXISTS gist_region_crange ON region USING GIST (crange);  -- Allows us to discover what's at this point


CREATE OR REPLACE FUNCTION tokens_in_crange(in_book_id INT, in_crange INT8RANGE) RETURNS TABLE(crange INT8RANGE) STABLE AS
$BODY$
    SELECT t.crange
      FROM token t
      WHERE t.book_id = in_book_id AND t.crange <@ in_crange
      ORDER BY ordering
$BODY$ LANGUAGE sql;
COMMENT ON FUNCTION public.tokens_in_crange(book_id INT, crange INT8RANGE) IS 'Get all tokens within the given crange';


DROP MATERIALIZED VIEW IF EXISTS book_metadata;
CREATE MATERIALIZED VIEW book_metadata AS
    SELECT r.book_id,
           r.rclass_id,
           r.rvalue,
           SUBSTRING(b.content, LOWER(r.crange)::INT + 1, (UPPER(r.crange) - LOWER(r.crange))::INT+1) AS content
      FROM region r, book b, rclass rc
     WHERE b.book_id = r.book_id
       AND r.rclass_id = rc.rclass_id
       AND rc.name IN (
           'metadata.title',
           'metadata.author',
           'chapter.title');
COMMENT ON MATERIALIZED VIEW book_metadata IS 'Extracted metadata from book contents';


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
       AND r.book_id = 2
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

/*
Searching for n-grams is:
   * Get 'token.type' and 'boundary.*', sorted by crange
   * Window function to search next n rows, disregard if one is a boundary.
   * Group n' filter
*/

COMMIT;
