-- ============================================================
-- Migration  : add_adjuster_id
-- Generated  : 2026-11-06 11:48:58 UTC
-- Author     : Insurance Data Engineering Agent
-- Description: Add 'adjuster_id' column to the claims table
--
-- Apply with:
--     sqlite3 claims.db < db/migrations/20261106_114858_add_adjuster_id.sql
--
-- Rollback:
--     SQLite does not support DROP COLUMN (< v3.35).
--     To rollback: restore from backup, or recreate the table without this column.
-- ============================================================

PRAGMA foreign_keys = ON;

-- Step 1: Add the new column (safe — ALTER TABLE ADD COLUMN never locks)
ALTER TABLE claims
    ADD COLUMN adjuster_id TEXT DEFAULT NULL;

-- Step 2: Add an index if this column will be queried frequently
-- Uncomment the line below if needed:
-- CREATE INDEX IF NOT EXISTS idx_claims_adjuster_id ON claims(adjuster_id);

-- Step 3: Verify
SELECT COUNT(*) AS total_claims,
       SUM(CASE WHEN adjuster_id IS NULL THEN 1 ELSE 0 END) AS null_count
FROM claims;
