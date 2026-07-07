BEGIN;


CREATE TABLE IF NOT EXISTS corpus (
    corpus_id SERIAL,
    PRIMARY KEY (corpus_id),
    
    name TEXT NOT NULL,
    UNIQUE(name),
    title TEXT NOT NULL,
    carousel_image BYTEA NULL,
    ordering INT NOT NULL DEFAULT 0,
    example_url TEXT NULL
);

CREATE TABLE IF NOT EXISTS corpus_book (
    corpus_id INT NOT NULL,
    FOREIGN KEY (corpus_id) REFERENCES corpus(corpus_id) ON DELETE CASCADE,
    book_id INT NOT NULL,
    FOREIGN KEY (book_id) REFERENCES book(book_id) ON DELETE CASCADE,
    PRIMARY KEY (corpus_id, book_id)
);

-- ## Upgrades

ALTER TABLE corpus ADD COLUMN IF NOT EXISTS example_url TEXT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
         WHERE conrelid = 'corpus_book'::regclass
           AND contype = 'p'
    ) THEN
        ALTER TABLE corpus_book ADD PRIMARY KEY (corpus_id, book_id);
    END IF;
END$$;

-- ## Comments

COMMENT ON TABLE  corpus IS 'Groups of books';
COMMENT ON COLUMN corpus.name IS 'Short name of corpus, e.g. ChiLit';
COMMENT ON COLUMN corpus.title IS 'Title to show in interface, e.g. ''ChiLit - 19th Century Children''s Literature''';
COMMENT ON COLUMN corpus.carousel_image IS 'Bytes of a JPEG carousel image, with a 0.4 width/height ratio';
COMMENT ON COLUMN corpus.ordering IS 'Ordering of corpus items in interface, negative items are hidden';
COMMENT ON COLUMN corpus.example_url IS 'Example CLiC URL to demonstrate corpus';

COMMENT ON TABLE  corpus_book IS 'Corpus <-> books many-to-many';

COMMIT;
