"""Logica de PRODUCTOS. No imprime: devuelve datos o levanta excepciones."""

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar_afectando,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorValidacion
from validaciones import validar_decimal, validar_entero, validar_texto

_COLUMNAS = "id, nombre, categoria, precio, stock, proveedor_id"


def listar_productos(db):
    return consultar(db, "SELECT " + _COLUMNAS + " FROM productos ORDER BY id")


def obtener_producto(db, producto_id):
    return consultar_uno(
        db, "SELECT " + _COLUMNAS + " FROM productos WHERE id = %s", (producto_id,)
    )


def agregar_producto(db, nombre, categoria, precio, stock, proveedor_id):
    nombre = validar_texto(nombre, "nombre")
    categoria = validar_texto(categoria, "categoria")
    precio = validar_decimal(precio, "precio", mayor_a=0)
    stock = validar_entero(stock, "stock", minimo=0)
    proveedor_id = validar_entero(proveedor_id, "proveedor_id", minimo=1)
    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            "INSERT INTO productos (nombre, categoria, precio, stock, proveedor_id) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (nombre, categoria, precio, stock, proveedor_id),
        )
    return fila[0]


def actualizar_stock(db, producto_id, nuevo_stock):
    nuevo_stock = validar_entero(nuevo_stock, "stock", minimo=0)
    with transaccion(db):
        ejecutar_afectando(
            db, "UPDATE productos SET stock = %s WHERE id = %s", (nuevo_stock, producto_id)
        )


def actualizar_producto(db, producto_id, campo, valor):
    """campo: 'nombre', 'categoria' o 'precio'."""
    if campo == "nombre":
        valor = validar_texto(valor, "nombre")
        sql = "UPDATE productos SET nombre = %s WHERE id = %s"
    elif campo == "categoria":
        valor = validar_texto(valor, "categoria")
        sql = "UPDATE productos SET categoria = %s WHERE id = %s"
    elif campo == "precio":
        valor = validar_decimal(valor, "precio", mayor_a=0)
        sql = "UPDATE productos SET precio = %s WHERE id = %s"
    else:
        raise ErrorValidacion("Campo invalido: use 'nombre', 'categoria' o 'precio'.")
    with transaccion(db):
        ejecutar_afectando(db, sql, (valor, producto_id))


def eliminar_producto(db, producto_id):
    with transaccion(db):
        ejecutar_afectando(db, "DELETE FROM productos WHERE id = %s", (producto_id,))
