-- 003_precio_unitario.sql
-- Guarda el precio del producto EN EL MOMENTO de la venta.
-- Sin esto, el total de una venta vieja cambia si despues se actualiza el
-- precio del producto. Primero se completa con el precio actual y despues
-- se marca NOT NULL.

BEGIN;

ALTER TABLE detalle_ventas ADD COLUMN precio_unitario numeric;

UPDATE detalle_ventas d
   SET precio_unitario = p.precio
  FROM productos p
 WHERE p.id = d.producto_id;

ALTER TABLE detalle_ventas ALTER COLUMN precio_unitario SET NOT NULL;
ALTER TABLE detalle_ventas ADD CONSTRAINT detalle_ventas_precio_positivo CHECK (precio_unitario > 0);

COMMIT;
