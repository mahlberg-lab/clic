BEGIN;


CREATE TABLE IF NOT EXISTS repository (
    repository_id SERIAL,
    PRIMARY KEY (repository_id),
    
    name TEXT NOT NULL,
    UNIQUE(name),
    version TEXT NOT NULL
);
COMMENT ON TABLE  repository IS 'Versions of repository stored';
COMMENT ON COLUMN repository.name IS 'Name of repository, e.g. corpora';
COMMENT ON COLUMN repository.version IS 'Git revision';


COMMIT;
