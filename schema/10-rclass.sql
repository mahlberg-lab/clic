BEGIN;


CREATE TABLE IF NOT EXISTS rclass (
    rclass_id INT,
    PRIMARY KEY (rclass_id),

    name TEXT NOT NULL,
    CHECK(name ~ '^[A-Za-z0-9_.]+$'),
    description TEXT NOT NULL
);
COMMENT ON TABLE  rclass IS 'Machine readable region types';
COMMENT ON COLUMN rclass.name IS 'Machine-readable name for class, meet LTREE requirements';
COMMENT ON COLUMN rclass.description IS 'Description for region class, define rvalue';


/* Populate vocabulary */
CREATE OR REPLACE FUNCTION pg_temp.upsert_rclass(new_id INT, new_name TEXT, new_description TEXT) RETURNS VOID AS
$BODY$
    INSERT INTO rclass (rclass_id, name, description)
        VALUES (new_id, new_name, new_description)
        ON CONFLICT (rclass_id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description;
$BODY$ LANGUAGE sql;
SELECT pg_temp.upsert_rclass(101, 'metadata.title', 'Book title');
SELECT pg_temp.upsert_rclass(102, 'metadata.author', 'Book author');
SELECT pg_temp.upsert_rclass(201, 'boundary.chapter', 'Whitespace between chapters');
SELECT pg_temp.upsert_rclass(202, 'boundary.paragraph', 'Whitespace between paragraphs');
SELECT pg_temp.upsert_rclass(203, 'boundary.sentence', 'Punctuation denoting end of sentences');
SELECT pg_temp.upsert_rclass(204, 'boundary.quote_start', 'Opening quote mark');
SELECT pg_temp.upsert_rclass(205, 'boundary.quote_end', 'Closing quote mark');
SELECT pg_temp.upsert_rclass(301, 'chapter.text', 'Chapter text (value: Chapter number)');
SELECT pg_temp.upsert_rclass(302, 'chapter.title', 'Chapter title (value: Chapter number)');
SELECT pg_temp.upsert_rclass(401, 'chapter.paragraph', 'Paragraph (value: Number within chapter)');
SELECT pg_temp.upsert_rclass(402, 'chapter.sentence', 'Paragraph (value: Number within chapter)');
SELECT pg_temp.upsert_rclass(501, 'quote.quote', 'Sections enclosed by boundary.quote_start & boundary.quote_end');
SELECT pg_temp.upsert_rclass(502, 'quote.nonquote', 'Text within a chapter but not in quote');
SELECT pg_temp.upsert_rclass(503, 'quote.suspension.short', 'Suspension between quote');
SELECT pg_temp.upsert_rclass(504, 'quote.suspension.long', 'Suspension between quote');
SELECT pg_temp.upsert_rclass(505, 'quote.embedded', 'Sections enclosed by boundary.quote_start & boundary.quote_end');
SELECT pg_temp.upsert_rclass(506, 'quote.embedded.suspension.short', 'Suspension between quote');
SELECT pg_temp.upsert_rclass(507, 'quote.embedded.suspension.long', 'Suspension between quote');


COMMIT;
