-- 005_ingresos_rollback.sql
-- Revierte la migracion 005.

BEGIN;

DROP TABLE IF EXISTS ingresos;

COMMIT;
