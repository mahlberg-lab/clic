BEGIN;

-- We need this for GIST tokens on book_id INT as well as ranges.
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Enable trgm for indexing token ttypes for concordance LIKE search
CREATE EXTENSION IF NOT EXISTS btree_gin;
CREATE EXTENSION IF NOT EXISTS pg_trgm;


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
CREATE UNIQUE INDEX IF NOT EXISTS book_name_book_id ON book(name, book_id);
COMMENT ON INDEX book_name_book_id IS 'Allow name -> book_id lookup to work without scanning book content';


CREATE TABLE IF NOT EXISTS token (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    crange INT4RANGE NOT NULL CHECK (UPPER(crange) > LOWER(crange)),
    PRIMARY KEY (book_id, crange),

    ttype TEXT NOT NULL,
    ordering INT NULL,  -- TODO: Do we even need it, vs. LOWER(crange)?
    part_of JSONB NULL  -- NB: Ideally this would be NOT NULL DEFERRABLE but you can't do that yet
);
COMMENT ON TABLE  token IS $$Tokens within a book (partition root: each book gets it's own sub-table)$$;
COMMENT ON COLUMN token.ttype IS 'Token type, i.e. normalised token';
COMMENT ON COLUMN token.crange IS 'Character range to find this token at';
COMMENT ON COLUMN token.ordering IS 'Position of this token within book (populated by book_import_finalise)';
COMMENT ON COLUMN token.part_of IS 'Dict of all regions this token is part of (populated by book_import_finalise)';


CREATE TABLE IF NOT EXISTS region (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    rclass_id INT NOT NULL,
    FOREIGN KEY (rclass_id) REFERENCES rclass(rclass_id),
    crange INT4RANGE NOT NULL CHECK (UPPER(crange) > LOWER(crange)),
    PRIMARY KEY (book_id, rclass_id, crange), -- TODO: Is this being unique correct? Are there regions that get nested within themselves?

    rvalue INT NULL
);
COMMENT ON TABLE  region IS $$Regions within a book (partition root: each book gets it's own sub-table)$$;
COMMENT ON COLUMN region.rvalue IS 'Value associated with range, e.g. chapter number';
COMMENT ON COLUMN region.crange IS 'Character range this applies to';


CREATE OR REPLACE FUNCTION book_import_init(new_name TEXT, new_content TEXT) RETURNS TABLE(
    book_id INT,
    token_tbl TEXT,
    region_tbl TEXT
) AS $BODY$
DECLARE
    new_book_id INT;
    token_tbl TEXT;
    region_tbl TEXT;
    ret RECORD;
BEGIN
    INSERT INTO book (name, content)
         VALUES (new_name, new_content)
    ON CONFLICT (name) DO UPDATE SET content=EXCLUDED.content
    RETURNING book.book_id INTO new_book_id;

    -- Destroy / recreate token table for this book
    token_tbl = 'token_' || new_book_id;
    EXECUTE format($$
        DROP TABLE IF EXISTS %1$s
    $$, token_tbl);
    EXECUTE format($$
        CREATE TABLE %1$s (
            CHECK ( book_id = %2$s )
        ) INHERITS (token)
    $$, token_tbl, new_book_id);

    -- Destroy / recreate region table for this book
    region_tbl = 'region_' || new_book_id;
    EXECUTE format($$
        DROP TABLE IF EXISTS %1$s
    $$, region_tbl);
    EXECUTE format($$
        CREATE TABLE %1$s (
            CHECK ( book_id = %2$s )
        ) INHERITS (region)
    $$, region_tbl, new_book_id);

    RETURN QUERY SELECT new_book_id, token_tbl, region_tbl;
END;
$BODY$ LANGUAGE 'plpgsql' SECURITY DEFINER;
COMMENT ON FUNCTION book_import_init(new_name TEXT, new_content TEXT) IS $$Start importing a new/replacement book. Returns:
- book_id: The assigned ID for the new book
- token_tbl: Name of the token table which should now be populated
- region_tb: Name of the region table which should now be populated$$;


CREATE OR REPLACE FUNCTION book_import_finalise(new_book_id INT) RETURNS VOID AS $BODY$
DECLARE
    token_tbl TEXT;
    region_tbl TEXT;
BEGIN
    token_tbl = 'token_' || new_book_id;
    region_tbl = 'region_' || new_book_id;

    -- Index region partition
    EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_rclass_id ON %1$s (rclass_id)$$, region_tbl);
    EXECUTE format($$COMMENT ON INDEX %1$s_rclass_id IS 'Get regions by rclass'$$, region_tbl);
    EXECUTE format($$CREATE INDEX IF NOT EXISTS gist_%1$s_book_id_crange ON %1$s USING GIST (book_id, crange)$$, region_tbl);
    EXECUTE format($$COMMENT ON INDEX gist_%1$s_book_id_crange IS 'Finding regions in a range, joining to tokens'$$, region_tbl);
    EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_book_id_lower_crange ON %1$s (book_id, LOWER(crange))$$, region_tbl);
    EXECUTE format($$COMMENT ON INDEX %1$s_book_id_lower_crange IS 'Sorting on LOWER(crange)'$$, region_tbl);

    -- Index token partition
    EXECUTE format($$CREATE INDEX IF NOT EXISTS gist_%1$s_book_id_crange ON %1$s USING GIST (book_id, crange)$$, token_tbl);
    EXECUTE format($$COMMENT ON INDEX gist_%1$s_book_id_crange IS 'Finding tokens in a range, joining to regions'$$, token_tbl);
    EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_book_id_lower_crange ON %1$s (book_id, LOWER(crange))$$, token_tbl);
    EXECUTE format($$COMMENT ON INDEX %1$s_book_id_lower_crange IS 'Joining with a scalar equivalent to the PK'$$, token_tbl);

    -- Add extra token metadata to this partition
    EXECUTE format($$
        WITH token_ordering AS
        (
            SELECT t.book_id
                 , t.crange
                 , ROW_NUMBER() OVER (ORDER BY t.book_id, t.crange) ordering
              FROM %1$s t
             WHERE t.book_id = %2$s
        )
        UPDATE %1$s t
           SET ordering = o.ordering
             , part_of = (SELECT JSONB_OBJECT_AGG(r.rclass_id, r.rvalue) FROM region r WHERE t.book_id = r.book_id AND t.crange <@ r.crange)
          FROM token_ordering o
         WHERE t.book_id = o.book_id
           AND t.crange = o.crange
           AND t.book_id = %2$s
    $$, token_tbl, new_book_id);

    -- Add our indexes to the extra metadata
    EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_book_id_ordering ON %1$s (book_id, ordering)$$, token_tbl);
    EXECUTE format($$COMMENT ON INDEX %1$s_book_id_ordering IS 'Selecting tokens around a point in concordance'$$, token_tbl);
    EXECUTE format($$CREATE INDEX IF NOT EXISTS trgm_%1$s_ttype_part_of ON %1$s USING GIN (book_id, ttype gin_trgm_ops, part_of)$$, token_tbl);
    EXECUTE format($$COMMENT ON INDEX trgm_%1$s_ttype_part_of IS 'Select tokens by partial types & part_of regions in concorcance'$$, token_tbl);
END;
$BODY$ LANGUAGE 'plpgsql' SECURITY DEFINER;
COMMENT ON FUNCTION book_import_finalise(new_book_id INT) IS $$Update metadata and index new book data. Call once region/book tables are populated$$;


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
