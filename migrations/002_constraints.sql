-- 002_constraints.sql
-- Restricciones que hoy solo valida Python: ahora tambien las exige la base.

BEGIN;

ALTER TABLE detalle_ventas ADD CONSTRAINT detalle_ventas_cantidad_positiva CHECK (cantidad > 0);
ALTER TABLE productos      ADD CONSTRAINT productos_precio_positivo    CHECK (precio > 0);
ALTER TABLE productos      ADD CONSTRAINT productos_stock_no_negativo  CHECK (stock >= 0);

-- La fecha de una venta se completa sola si no se envia.
ALTER TABLE ventas ALTER COLUMN fecha SET DEFAULT CURRENT_DATE;

COMMIT;
