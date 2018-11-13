BEGIN;

CREATE OR REPLACE FUNCTION tokens_in_crange(in_book_id INT, in_crange INT4RANGE) RETURNS TABLE(crange INT4RANGE) STABLE AS
$BODY$
    SELECT t.crange
      FROM token t
      WHERE t.book_id = in_book_id AND t.crange <@ in_crange
      ORDER BY LOWER(t.crange)
$BODY$ LANGUAGE sql;
COMMENT ON FUNCTION public.tokens_in_crange(book_id INT, crange INT4RANGE) IS 'Get all tokens within the given crange';


COMMIT;
