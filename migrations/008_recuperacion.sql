-- 008_recuperacion.sql
-- Recuperar la contrasena sin iniciar sesion: se envia un codigo por email.
-- El codigo se guarda con su vencimiento, la cantidad de intentos fallidos y
-- la fecha del ultimo envio (para el enfriamiento entre pedidos).
--
-- Todas las columnas nuevas son NULL o tienen DEFAULT, asi que las filas que
-- ya existian siguen siendo validas.

BEGIN;

ALTER TABLE clientes ADD COLUMN codigo_recuperacion         varchar(6);
ALTER TABLE clientes ADD COLUMN codigo_recuperacion_expira  timestamptz;
ALTER TABLE clientes ADD COLUMN codigo_recuperacion_intentos integer NOT NULL DEFAULT 0;
ALTER TABLE clientes ADD COLUMN ultimo_codigo_envio         timestamptz;

COMMIT;
