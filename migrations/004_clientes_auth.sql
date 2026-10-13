-- 004_clientes_auth.sql
-- Convierte a "clientes" en una tabla con CUENTA DE USUARIO:
-- usuario + contrasena (hash) + email verificado + telefono opcional.
-- Tambien guarda un ingreso fijo mensual opcional y la moneda elegida.
--
-- Todas las columnas nuevas son NULL o tienen DEFAULT, asi que las filas que
-- ya existian siguen siendo validas (quedan como clientes "sin cuenta").

BEGIN;

ALTER TABLE clientes ADD COLUMN usuario               varchar(50);
ALTER TABLE clientes ADD COLUMN password_hash         text;
ALTER TABLE clientes ADD COLUMN email_verificado      boolean     NOT NULL DEFAULT false;
ALTER TABLE clientes ADD COLUMN codigo_verificacion   varchar(10);
ALTER TABLE clientes ADD COLUMN codigo_expira         timestamptz;
ALTER TABLE clientes ADD COLUMN ingreso_fijo_mensual  numeric(14,2) NOT NULL DEFAULT 0;
ALTER TABLE clientes ADD COLUMN moneda                varchar(3)  NOT NULL DEFAULT 'ARS';
ALTER TABLE clientes ADD COLUMN creado_en             timestamptz NOT NULL DEFAULT now();

-- El ingreso fijo no puede ser negativo.
ALTER TABLE clientes ADD CONSTRAINT clientes_ingreso_fijo_no_negativo
    CHECK (ingreso_fijo_mensual >= 0);

-- El usuario es unico sin distinguir mayusculas (juan == Juan).
CREATE UNIQUE INDEX clientes_usuario_uk ON clientes (lower(usuario))
    WHERE usuario IS NOT NULL;

COMMIT;
