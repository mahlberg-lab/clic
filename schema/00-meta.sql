BEGIN;


-- There is no aggregate function for range_merge, create one
-- https://dba.stackexchange.com/questions/173020/aggregate-ranges-by-merging#173021
DROP AGGREGATE IF EXISTS range_merge(anyrange);
CREATE AGGREGATE range_merge(anyrange) (
    sfunc = RANGE_MERGE,
    stype = ANYRANGE
);

-- Expand range in both directions by (i)
CREATE OR REPLACE FUNCTION range_expand(range INT8RANGE, i INT) RETURNS INT8RANGE IMMUTABLE AS
$BODY$
    SELECT INT8RANGE(LOWER(range) - i, UPPER(range) + i);
$BODY$ LANGUAGE sql;



COMMIT;
