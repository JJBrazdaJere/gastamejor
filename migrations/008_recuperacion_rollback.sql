-- 008_recuperacion_rollback.sql
-- Revierte la migracion 008.

BEGIN;

ALTER TABLE clientes DROP COLUMN IF EXISTS ultimo_codigo_envio;
ALTER TABLE clientes DROP COLUMN IF EXISTS codigo_recuperacion_intentos;
ALTER TABLE clientes DROP COLUMN IF EXISTS codigo_recuperacion_expira;
ALTER TABLE clientes DROP COLUMN IF EXISTS codigo_recuperacion;

COMMIT;
