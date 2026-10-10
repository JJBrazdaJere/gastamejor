-- 003_precio_unitario_rollback.sql
-- Revierte 003_precio_unitario.sql.

BEGIN;

ALTER TABLE detalle_ventas DROP CONSTRAINT IF EXISTS detalle_ventas_precio_positivo;
ALTER TABLE detalle_ventas DROP COLUMN IF EXISTS precio_unitario;

COMMIT;
