"""Configuración compartida de los tests (fixtures de pytest).

El fixture `db` abre una conexión real a la base indicada en el `.env`,
pero INTERCEPTA el método `commit` para que los cambios NO se confirmen.
Al terminar el test se hace `rollback`, así la base queda intacta.
"""

import os
import sys

import psycopg
import pytest

# Aseguramos que la carpeta del proyecto esté en el path para poder
# importar config, productos, proveedores, etc. al correr pytest.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import config  # noqa: E402


@pytest.fixture
def db():
    cfg = config.DB_CONFIG
    conexion = psycopg.connect(
        host=cfg["host"],
        port=cfg["port"],
        dbname=cfg["dbname"],
        user=cfg["user"],
        password=cfg["password"],
    )

    # "commit" pasa a ser un no-op: el trabajo queda dentro de la transacción
    # abierta y jamás se confirma. Al final el rollback lo descarta todo.
    conexion.commit = (lambda: None)

    # Forzamos una transacción externa. Así las operaciones del programa,
    # al detectar que ya hay una transacción en curso, usan SAVEPOINTs: si
    # una falla, solo se revierte esa operación y no lo ya hecho en el test.
    conexion.execute("SELECT 1")

    yield conexion

    conexion.rollback()
    conexion.close()
