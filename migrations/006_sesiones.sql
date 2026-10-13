-- 006_sesiones.sql
-- Sesiones de login: cada inicio de sesion genera un TOKEN aleatorio que el
-- navegador guarda y envia en cada pedido. El token vence a las N horas.
--
-- Se guarda el token tal cual (es aleatorio y largo, no una contrasena). Si se
-- quiere invalidar todo de una, basta con vaciar la tabla.
-- ON DELETE CASCADE: al borrar la cuenta, se borran sus sesiones.

BEGIN;

CREATE TABLE sesiones (
    token      text        PRIMARY KEY,
    cliente_id integer     NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    creado_en  timestamptz NOT NULL DEFAULT now(),
    expira_en  timestamptz NOT NULL
);

CREATE INDEX sesiones_cliente_idx ON sesiones (cliente_id);

COMMIT;
