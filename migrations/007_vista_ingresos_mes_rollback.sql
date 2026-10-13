-- 007_vista_ingresos_mes_rollback.sql
-- Revierte la migracion 007.

BEGIN;

DROP VIEW IF EXISTS ingresos_mes;

COMMIT;
