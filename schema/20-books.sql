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
CREATE INDEX IF NOT EXISTS token_crange ON token(crange);  -- Allows us to discover what's at this point
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
CREATE INDEX IF NOT EXISTS region_crange ON region(crange);  -- Allows us to discover what's at this point

/*
TODO:
Book metadata view: Picks out values for
* 'metadata.title'
* 'metadata.author'

Searching for n-grams is:
   * Get 'token.type' and 'boundary.*', sorted by crange
   * Window function to search next n rows, disregard if one is a boundary.
   * Group n' filter

Searching for concordance, e.g. "Oliver* * his arm"
  * Choose an anchor node from each list, e.g. first, longest.
  * Select everything matching one node, and nodes around it.
  * Filter this by rest of conditions

Get window around node crange (subset / combination of word range)
  * 3 window functions
*/

COMMIT;
