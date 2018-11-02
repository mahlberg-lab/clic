BEGIN;

CREATE OR REPLACE FUNCTION tokens_in_crange(in_book_id INT, in_crange INT4RANGE) RETURNS TABLE(crange INT4RANGE) STABLE AS
$BODY$
    SELECT t.crange
      FROM token t
      WHERE t.book_id = in_book_id AND t.crange <@ in_crange
      ORDER BY LOWER(t.crange)
$BODY$ LANGUAGE sql;
COMMENT ON FUNCTION public.tokens_in_crange(book_id INT, crange INT4RANGE) IS 'Get all tokens within the given crange';


CREATE OR REPLACE FUNCTION token_get_surrounding(book_id INT, rclass TEXT, anchor_loc INT, anchor_off INT, node_size INT, context_size INT) RETURNS TABLE(
    node_start INT,
    ttypes TEXT[],
    cranges INT4RANGE[]
) AS $BODY$
                    SELECT ARRAY_POSITION(ARRAY_AGG(t.ordering = anchor_loc), TRUE) - anchor_off node_start
                         , ARRAY_AGG(CASE WHEN t.ordering < (anchor_loc - anchor_off) THEN t.ttype -- i.e. part of the context, so rclass irrelevant
                                          WHEN t.ordering > (anchor_loc - anchor_off + node_size - 1) THEN t.ttype -- i.e. part of the context, so rclass irrelevant
                                          WHEN t.part_of ? token_get_surrounding.rclass THEN t.ttype
                                          ELSE NULL -- part of the node, but not in the right rclass, NULL should fail any node checks later on
                                           END) ttypes
                         , ARRAY_AGG(t.crange) cranges
                      FROM token t
                     WHERE t.book_id = token_get_surrounding.book_id
                       AND t.ordering BETWEEN anchor_loc - anchor_off - context_size
                                          AND anchor_loc - anchor_off + (node_size - 1) + context_size
$BODY$ LANGUAGE sql;
COMMENT ON FUNCTION token_get_surrounding(book_id INT, rclass TEXT, anchor_loc INT, anchor_off INT, node_size INT, context_size INT)
     IS $$Get all tokens surrounding an anchor token:
      - book_id: Book anchor token is in
      - rclass: rclass that node tokens should be part_of
      - anchor_log: The ordering value for the anchor token
      - anchor_off: The offset of the anchor in the (concordance) node
      - node_size: The number of tokens in the (concordance) node
      - The number of context nodes shown either side
      Returns:
      - The index of the first node token in the result arrays
      - An array of corresponding types for each token
      - An array of cranges within the book text for each token

      This is a separate function instead of a sub-query to force Postgres to
      consider it as a separate query, otherwise it ignores the ordering indexes
      and performs full-table scans.
      $$;

COMMIT;
