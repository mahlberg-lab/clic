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


-- Remove all of `idx` from `arr`
CREATE OR REPLACE FUNCTION multi_remove(arr anyarray, idx int[])
RETURNS anyarray
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$
  SELECT coalesce(array_agg(e ORDER BY i), arr[1:0])
  FROM unnest(arr) WITH ORDINALITY AS u(e, i)
  WHERE i <> ALL (idx)
$$;


-- Replace value at `idx` with `new_value`, and `nulls_after` values afterwards with NULL
CREATE OR REPLACE FUNCTION type_repl(
    arr         anycompatiblearray,
    idx         integer,
    new_value   anycompatible,
    nulls_after integer DEFAULT 0
) RETURNS anycompatiblearray
LANGUAGE plpgsql
IMMUTABLE PARALLEL SAFE
AS $$
DECLARE
    result ALIAS FOR $0;   -- same type as the return type
    lo  integer;
    hi  integer;
    i   integer;
BEGIN
    IF arr IS NULL OR idx IS NULL THEN
        RETURN arr;
    END IF;

    IF array_ndims(arr) > 1 THEN
        RAISE EXCEPTION 'type_repl() supports 1-dimensional arrays only';
    END IF;

    lo := array_lower(arr, 1);
    hi := array_upper(arr, 1);

    IF lo IS NULL OR idx < lo OR idx > hi THEN
        RAISE EXCEPTION 'index % out of range [%, %]', idx, lo, hi
            USING ERRCODE = 'array_subscript_error';
    END IF;

    IF arr[idx] IS NULL THEN
        -- ttype has already been marked as being outside of range. Don't remove this.
        RETURN arr;
    END IF;

    result := arr;
    result[idx] := new_value;

    -- clamp so we never grow the array past its original upper bound
    FOR i IN idx + 1 .. LEAST(idx + GREATEST(COALESCE(nulls_after, 0), 0), hi) LOOP
        result[i] := NULL;
    END LOOP;

    RETURN result;
END;
$$;


COMMIT;

-- Before we begin, vacuum any existing data, creating the
-- MATERIALISED VIEWS can be problematic otherwise.
-- NB: This make take several minutes
--VACUUM ANALYSE;
