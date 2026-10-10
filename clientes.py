"""Logica de CLIENTES. No imprime: devuelve datos o levanta excepciones.

El id ya lo genera la base (IDENTITY). El telefono es opcional (columna NULL).
"""

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar_afectando,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorValidacion
from validaciones import validar_email, validar_texto, validar_texto_opcional

_COLUMNAS = "id, nombre, telefono, email"


def listar_clientes(db):
    return consultar(db, "SELECT " + _COLUMNAS + " FROM clientes ORDER BY id")


def obtener_cliente(db, cliente_id):
    return consultar_uno(
        db, "SELECT " + _COLUMNAS + " FROM clientes WHERE id = %s", (cliente_id,)
    )


def agregar_cliente(db, nombre, email, telefono=None):
    nombre = validar_texto(nombre, "nombre")
    email = validar_email(email)
    telefono = validar_texto_opcional(telefono)
    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            "INSERT INTO clientes (nombre, telefono, email) VALUES (%s, %s, %s) RETURNING id",
            (nombre, telefono, email),
        )
    return fila[0]


def actualizar_cliente(db, cliente_id, campo, valor):
    """campo: 'nombre', 'telefono' o 'email'."""
    if campo == "nombre":
        valor = validar_texto(valor, "nombre")
        sql = "UPDATE clientes SET nombre = %s WHERE id = %s"
    elif campo == "telefono":
        valor = validar_texto_opcional(valor)
        sql = "UPDATE clientes SET telefono = %s WHERE id = %s"
    elif campo == "email":
        valor = validar_email(valor)
        sql = "UPDATE clientes SET email = %s WHERE id = %s"
    else:
        raise ErrorValidacion("Campo invalido: use 'nombre', 'telefono' o 'email'.")
    with transaccion(db):
        ejecutar_afectando(db, sql, (valor, cliente_id))


def eliminar_cliente(db, cliente_id):
    with transaccion(db):
        ejecutar_afectando(db, "DELETE FROM clientes WHERE id = %s", (cliente_id,))
