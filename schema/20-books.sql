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

    content TEXT,
    hash BYTEA
);
COMMENT ON TABLE  book IS 'Book name & contents';
COMMENT ON COLUMN book.name IS 'Short name of book, e.g. TTC';
COMMENT ON COLUMN book.content IS 'Full text contents of book';
CREATE UNIQUE INDEX IF NOT EXISTS book_name_book_id ON book(name, book_id);
COMMENT ON INDEX book_name_book_id IS 'Allow name -> book_id lookup to work without scanning book content';

ALTER TABLE book ADD COLUMN IF NOT EXISTS hash BYTEA;


CREATE TABLE IF NOT EXISTS token (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    crange INT4RANGE NOT NULL CHECK (UPPER(crange) > LOWER(crange)),
    PRIMARY KEY (book_id, crange),

    ttype TEXT NOT NULL,
    ordering INT NULL,
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
    PRIMARY KEY (book_id, rclass_id, crange),

    rvalue INT NULL
);
COMMENT ON TABLE  region IS $$Regions within a book (partition root: each book gets it's own sub-table)$$;
COMMENT ON COLUMN region.rvalue IS 'Value associated with range, e.g. chapter number';
COMMENT ON COLUMN region.crange IS 'Character range this applies to';


CREATE TABLE IF NOT EXISTS book_metadata (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    rclass_id INT NOT NULL,
    FOREIGN KEY (rclass_id) REFERENCES rclass(rclass_id),
    rvalue INT NULL,
    content TEXT NOT NULL
);
COMMENT ON TABLE book_metadata IS 'Selected regions exacted to use for listings (chapter titles, e.g.)';
COMMENT ON COLUMN book_metadata.content IS 'Content of this region (populated by book_import_finalise)';
CREATE INDEX IF NOT EXISTS book_metadata_rclass_id ON book_metadata(rclass_id);
COMMENT ON INDEX book_metadata_rclass_id IS 'Select metadata by type (e.g. author)';


CREATE TABLE IF NOT EXISTS book_word_count (
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id),
    rclass_id INT NOT NULL,
    FOREIGN KEY (rclass_id) REFERENCES rclass(rclass_id),
    rvalue INT NULL,
    word_count INT NOT NULL
);
COMMENT ON COLUMN book_word_count.word_count IS 'Number of words in region (populated by book_import_finalise)';
COMMENT ON TABLE book_word_count IS 'Count words within a selection of regions';


CREATE OR REPLACE FUNCTION book_import_init(new_name TEXT, new_content TEXT, new_hash BYTEA) RETURNS TABLE(
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
    INSERT INTO book (name, content, hash)
         VALUES (new_name, new_content, new_hash)
    ON CONFLICT (name) DO UPDATE SET content=EXCLUDED.content, hash=EXCLUDED.hash
    RETURNING book.book_id INTO new_book_id;

    -- Destroy / recreate token table for this book
    token_tbl = 'token_' || new_book_id;
    EXECUTE format($$
        DROP INDEX IF EXISTS %1$s_rclass_id;
        DROP INDEX IF EXISTS gist_%1$s_book_id_crange;
        DROP INDEX IF EXISTS %1$s_book_id_lower_crange;
        DROP INDEX IF EXISTS gist_%1$s_book_id_crange;
        DROP INDEX IF EXISTS %1$s_book_id_lower_crange;
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

    -- Empty metadata tables from any previous versions of book
    DELETE FROM book_metadata bm WHERE bm.book_id = new_book_id;
    DELETE FROM book_word_count bwc WHERE bwc.book_id = new_book_id;

    RETURN QUERY SELECT new_book_id, token_tbl, region_tbl;
END;
$BODY$ LANGUAGE 'plpgsql' SECURITY DEFINER;
COMMENT ON FUNCTION book_import_init(new_name TEXT, new_content TEXT, new_hash BYTEA) IS $$Start importing a new/replacement book. Returns:
- book_id: The assigned ID for the new book
- token_tbl: Name of the token table which should now be populated
- region_tb: Name of the region table which should now be populated$$;


CREATE OR REPLACE FUNCTION book_import_finalise(new_book_id INT) RETURNS VOID AS $BODY$
DECLARE
    token_tbl TEXT;
    region_tbl TEXT;
    t TEXT;
BEGIN
    token_tbl = 'token_' || new_book_id;
    region_tbl = 'region_' || new_book_id;

    -- Index region partition
    FOREACH t IN ARRAY array['region', region_tbl] LOOP
        EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_rclass_id ON %1$s (rclass_id)$$, t);
        EXECUTE format($$COMMENT ON INDEX %1$s_rclass_id IS 'Get regions by rclass'$$, t);
        EXECUTE format($$CREATE INDEX IF NOT EXISTS gist_%1$s_book_id_crange ON %1$s USING GIST (book_id, crange)$$, t);
        EXECUTE format($$COMMENT ON INDEX gist_%1$s_book_id_crange IS 'Finding regions in a range, joining to tokens'$$, t);
        EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_book_id_lower_crange ON %1$s (book_id, LOWER(crange))$$, t);
        EXECUTE format($$COMMENT ON INDEX %1$s_book_id_lower_crange IS 'Sorting on LOWER(crange)'$$, t);
    END LOOP;

    -- Index token partition
    FOREACH t IN ARRAY array['token', token_tbl] LOOP
        EXECUTE format($$CREATE INDEX IF NOT EXISTS gist_%1$s_book_id_crange ON %1$s USING GIST (book_id, crange)$$, t);
        EXECUTE format($$COMMENT ON INDEX gist_%1$s_book_id_crange IS 'Finding tokens in a range, joining to regions'$$, t);
        EXECUTE format($$CREATE INDEX IF NOT EXISTS %1$s_book_id_lower_crange ON %1$s (book_id, LOWER(crange))$$, t);
        EXECUTE format($$COMMENT ON INDEX %1$s_book_id_lower_crange IS 'Joining with a scalar equivalent to the PK'$$, t);
    END LOOP;

    -- Update tokens-part-of-regions lookup
    EXECUTE format($$
        WITH token_nesting AS
        (
            SELECT t.crange
                 , JSONB_OBJECT_AGG(r.rclass_id, r.rvalue) part_of
              FROM token_%1$s t, region_%1$s r
             WHERE t.crange <@ r.crange
          GROUP BY t.crange
        )
        UPDATE token_%1$s t
           SET part_of = tn.part_of
          FROM token_nesting tn
         WHERE t.crange = tn.crange
    $$, new_book_id);

    -- Update book metadata tables
    INSERT INTO book_metadata (book_id, rclass_id, rvalue, content)
         SELECT r.book_id
              , r.rclass_id
              , r.rvalue
              , SUBSTRING(b.content, LOWER(r.crange) + 1, (UPPER(r.crange) - LOWER(r.crange))) AS content
           FROM region r, book b, rclass rc
          WHERE b.book_id = r.book_id
            AND b.book_id = new_book_id
            AND r.rclass_id = rc.rclass_id
            AND rc.name IN (
                    'metadata.title',
                    'metadata.author',
                    'chapter.title',
                    'chapter.part');
    INSERT INTO book_word_count (book_id, rclass_id, rvalue, word_count)
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
            AND r.book_id = new_book_id
            AND rc.name IN (
                    'chapter.text',
                    'quote.quote',
                    'quote.nonquote',
                    'quote.suspension.short',
                    'quote.suspension.long');

    -- Add our indexes to the extra metadata
    FOREACH t IN ARRAY array['token', token_tbl] LOOP
        EXECUTE format($$CREATE UNIQUE INDEX IF NOT EXISTS unique_%1$s_book_id_ordering ON %1$s (book_id, ordering)$$, t);
        EXECUTE format($$COMMENT ON INDEX unique_%1$s_book_id_ordering IS 'Selecting tokens around a point in concordance'$$, t);
        EXECUTE format($$CREATE INDEX IF NOT EXISTS trgm_%1$s_book_id_ttype_part_of ON %1$s USING GIN (book_id, ttype gin_trgm_ops, part_of)$$, t);
        EXECUTE format($$COMMENT ON INDEX trgm_%1$s_book_id_ttype_part_of IS 'Select tokens by partial types & part_of regions in concorcance'$$, t);
    END LOOP;
END;
$BODY$ LANGUAGE 'plpgsql' SECURITY DEFINER;
COMMENT ON FUNCTION book_import_finalise(new_book_id INT) IS $$Update metadata and index new book data. Call once region/book tables are populated$$;


COMMIT;
