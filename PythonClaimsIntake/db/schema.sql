-- Insurance Claims Intake — SQLite schema
-- Safe to re-run at every startup (CREATE IF NOT EXISTS).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS policies (
    policy_number TEXT PRIMARY KEY,
    holder_name   TEXT NOT NULL,
    policy_type   TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id              TEXT PRIMARY KEY,
    policy_number         TEXT NOT NULL REFERENCES policies(policy_number),
    first_name            TEXT NOT NULL,
    last_name             TEXT NOT NULL,
    phone                 TEXT NOT NULL,
    email                 TEXT,
    incident_date         TEXT NOT NULL,
    loss_type             TEXT NOT NULL,
    incident_description  TEXT NOT NULL,
    estimated_loss_amount REAL,
    incident_location     TEXT,
    status                TEXT NOT NULL DEFAULT 'Draft',
    created_at            TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_claims_last_name   ON claims(last_name);
CREATE INDEX IF NOT EXISTS idx_claims_policy      ON claims(policy_number);
CREATE INDEX IF NOT EXISTS idx_claims_created_at  ON claims(created_at);
