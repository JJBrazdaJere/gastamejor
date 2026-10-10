"""Pruebas de integración de productos y proveedores contra PostgreSQL.

Usan el fixture `db` (ver conftest.py): los cambios se revierten al final,
así que NO dejan datos ni modifican los reales.

Las operaciones ahora levantan excepciones de negocio (ErrorUnico,
ErrorClaveForanea, ErrorValidacion, ErrorNoEncontrado) en vez de devolver None.
"""

import pytest

from base_datos import consultar
from errores import ErrorClaveForanea, ErrorNoEncontrado, ErrorUnico, ErrorValidacion
from productos import (
    actualizar_producto,
    actualizar_stock,
    agregar_producto,
    eliminar_producto,
    obtener_producto,
)
from proveedores import agregar_proveedor, obtener_proveedor


def _crear_proveedor(db, email):
    return agregar_proveedor(db, "Proveedor Test", email, "555-0100")


def test_alta_y_lectura_de_proveedor(db):
    proveedor_id = _crear_proveedor(db, "prov_ok@example.com")
    fila = obtener_proveedor(db, proveedor_id)
    assert fila[1] == "Proveedor Test"
    assert fila[3] == "prov_ok@example.com"


def test_crud_completo_de_producto(db):
    proveedor_id = _crear_proveedor(db, "prov_prod@example.com")

    producto_id = agregar_producto(db, "Producto Test", "Cat Test", 10.5, 3, proveedor_id)
    fila = obtener_producto(db, producto_id)
    assert fila[1] == "Producto Test"

    actualizar_stock(db, producto_id, 99)
    assert obtener_producto(db, producto_id)[4] == 99

    actualizar_producto(db, producto_id, "precio", 25.0)
    assert float(obtener_producto(db, producto_id)[3]) == 25.0

    eliminar_producto(db, producto_id)
    assert obtener_producto(db, producto_id) is None


def test_email_duplicado_es_rechazado(db):
    _crear_proveedor(db, "dup@example.com")
    with pytest.raises(ErrorUnico):
        _crear_proveedor(db, "dup@example.com")


def test_producto_con_proveedor_inexistente_es_rechazado(db):
    with pytest.raises(ErrorClaveForanea):
        agregar_producto(db, "Fantasma", "Cat", 9.99, 1, 999999)


def test_producto_con_stock_negativo_es_rechazado(db):
    proveedor_id = _crear_proveedor(db, "prov_stock@example.com")
    with pytest.raises(ErrorValidacion):
        agregar_producto(db, "Sin stock", "Cat", 5.0, -1, proveedor_id)


def test_producto_con_precio_cero_es_rechazado(db):
    proveedor_id = _crear_proveedor(db, "prov_precio@example.com")
    with pytest.raises(ErrorValidacion):
        agregar_producto(db, "Gratis", "Cat", 0, 1, proveedor_id)


def test_actualizar_stock_inexistente_avisa(db):
    with pytest.raises(ErrorNoEncontrado):
        actualizar_stock(db, 999999, 5)


def test_eliminar_proveedor_con_productos_es_rechazado(db):
    proveedor_id = _crear_proveedor(db, "prov_fk@example.com")
    agregar_producto(db, "Dependiente", "Cat", 1.0, 1, proveedor_id)
    with pytest.raises(ErrorClaveForanea):
        from proveedores import eliminar_proveedor

        eliminar_proveedor(db, proveedor_id)


def test_consulta_con_like_y_parametros_vacios(db):
    # El '%' literal no debe confundirse con un marcador aunque llegue una
    # tupla vacia de parametros (defensa de base_datos._parametros).
    filas = consultar(db, "SELECT count(*) FROM productos WHERE nombre LIKE 'a%'", ())
    assert filas[0][0] >= 0
