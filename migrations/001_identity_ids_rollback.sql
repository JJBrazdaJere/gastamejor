-- 001_identity_ids_rollback.sql
-- Revierte 001_identity_ids.sql (quita el IDENTITY de las 3 tablas).

BEGIN;

ALTER TABLE clientes  ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE empleados ALTER COLUMN id DROP IDENTITY IF EXISTS;
ALTER TABLE ventas    ALTER COLUMN id DROP IDENTITY IF EXISTS;

COMMIT;
