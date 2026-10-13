-- 004_clientes_auth_rollback.sql
-- Revierte la migracion 004.

BEGIN;

DROP INDEX IF EXISTS clientes_usuario_uk;

ALTER TABLE clientes DROP CONSTRAINT IF EXISTS clientes_ingreso_fijo_no_negativo;

ALTER TABLE clientes DROP COLUMN IF EXISTS creado_en;
ALTER TABLE clientes DROP COLUMN IF EXISTS moneda;
ALTER TABLE clientes DROP COLUMN IF EXISTS ingreso_fijo_mensual;
ALTER TABLE clientes DROP COLUMN IF EXISTS codigo_expira;
ALTER TABLE clientes DROP COLUMN IF EXISTS codigo_verificacion;
ALTER TABLE clientes DROP COLUMN IF EXISTS email_verificado;
ALTER TABLE clientes DROP COLUMN IF EXISTS password_hash;
ALTER TABLE clientes DROP COLUMN IF EXISTS usuario;

COMMIT;
