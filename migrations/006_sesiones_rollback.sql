-- 006_sesiones_rollback.sql
-- Revierte la migracion 006.

BEGIN;

DROP TABLE IF EXISTS sesiones;

COMMIT;
