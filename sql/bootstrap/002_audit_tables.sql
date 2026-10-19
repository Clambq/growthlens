CREATE TABLE IF NOT EXISTS audit.ingestion_runs (
    run_id TEXT PRIMARY KEY,
    dataset TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    error TEXT
);

CREATE TABLE IF NOT EXISTS audit.ingestion_files (
    file_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES audit.ingestion_runs(run_id),
    source_file TEXT NOT NULL,
    target_table TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    rows_read BIGINT NOT NULL,
    rows_inserted BIGINT NOT NULL
);
