-- Users Schema Rollback
-- Version: 000

DROP POLICY IF EXISTS users_self_access ON users;
DROP TABLE IF EXISTS users CASCADE; 