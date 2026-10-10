"""Logica de PROVEEDORES. No imprime: devuelve datos o levanta excepciones."""

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar_afectando,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorValidacion
from validaciones import validar_email, validar_texto

_COLUMNAS = "id, nombre, telefono, email"


def listar_proveedores(db):
    return consultar(db, "SELECT " + _COLUMNAS + " FROM proveedores ORDER BY id")


def obtener_proveedor(db, proveedor_id):
    return consultar_uno(
        db, "SELECT " + _COLUMNAS + " FROM proveedores WHERE id = %s", (proveedor_id,)
    )


def agregar_proveedor(db, nombre, email, telefono):
    nombre = validar_texto(nombre, "nombre")
    email = validar_email(email)
    telefono = validar_texto(telefono, "telefono")  # NOT NULL en la base
    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            "INSERT INTO proveedores (nombre, telefono, email) VALUES (%s, %s, %s) RETURNING id",
            (nombre, telefono, email),
        )
    return fila[0]


def actualizar_proveedor(db, proveedor_id, campo, valor):
    """campo: 'nombre', 'telefono' o 'email'."""
    if campo == "nombre":
        valor = validar_texto(valor, "nombre")
        sql = "UPDATE proveedores SET nombre = %s WHERE id = %s"
    elif campo == "telefono":
        valor = validar_texto(valor, "telefono")
        sql = "UPDATE proveedores SET telefono = %s WHERE id = %s"
    elif campo == "email":
        valor = validar_email(valor)
        sql = "UPDATE proveedores SET email = %s WHERE id = %s"
    else:
        raise ErrorValidacion("Campo invalido: use 'nombre', 'telefono' o 'email'.")
    with transaccion(db):
        ejecutar_afectando(db, sql, (valor, proveedor_id))


def eliminar_proveedor(db, proveedor_id):
    with transaccion(db):
        ejecutar_afectando(db, "DELETE FROM proveedores WHERE id = %s", (proveedor_id,))
