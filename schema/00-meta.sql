BEGIN;


-- There is no aggregate function for range_merge, create one
-- https://dba.stackexchange.com/questions/173020/aggregate-ranges-by-merging#173021
DROP AGGREGATE IF EXISTS range_merge(anyrange);
CREATE AGGREGATE range_merge(anyrange) (
    sfunc = RANGE_MERGE,
    stype = ANYRANGE
);

-- Expand range in both directions by (i)
CREATE OR REPLACE FUNCTION range_expand(range INT4RANGE, i INT) RETURNS INT4RANGE IMMUTABLE AS
$BODY$
    SELECT INT4RANGE(LOWER(range) - i, UPPER(range) + i);
$BODY$ LANGUAGE sql;


-- Disable indexes (for updates)
CREATE OR REPLACE FUNCTION index_disable(tbl UNKNOWN) RETURNS VOID AS
$BODY$
    UPDATE pg_index
       SET indisready = false
     WHERE indrelid = (
        SELECT oid
          FROM pg_class
         WHERE relname = tbl::TEXT)
$BODY$ LANGUAGE sql SECURITY DEFINER;

-- Re-enable indexes, and re-index table
CREATE OR REPLACE FUNCTION index_enable(tbl UNKNOWN) RETURNS VOID AS $$
BEGIN
    UPDATE pg_index
       SET indisready = true
     WHERE indrelid = (
        SELECT oid
          FROM pg_class
         WHERE relname = tbl::TEXT);
    EXECUTE FORMAT('REINDEX TABLE %1s', tbl);
END;
$$ LANGUAGE 'plpgsql' SECURITY DEFINER;


COMMIT;

-- Before we begin, vacuum any existing data, creating the
-- MATERIALISED VIEWS can be problematic otherwise.
VACUUM ANALYSE;
