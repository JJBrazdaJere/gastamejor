"""Conexion a PostgreSQL.

Se abre en modo `autocommit=True`: cada sentencia suelta (por ejemplo un
SELECT de un reporte) se ejecuta y termina sola, sin dejar una transaccion
abierta colgada. Las operaciones que deben ser atomicas (como registrar una
venta) se agrupan con el context manager `base_datos.transaccion`, que abre
su propia transaccion y la confirma o revierte.
"""

import psycopg


def conectar_db(host, port, dbname, user, password):
    return psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        autocommit=True,
    )
