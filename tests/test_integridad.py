"""Pruebas de integración contra PostgreSQL.

Usan el fixture `db` (ver conftest.py): los cambios se revierten al final,
así que NO dejan datos ni modifican los reales.
"""

from productos import (
    agregar_producto,
    actualizar_producto,
    actualizar_stock,
    eliminar_producto,
    obtener_producto,
)
from proveedores import agregar_proveedor, obtener_proveedor


def _crear_proveedor(db, email):
    return agregar_proveedor(db, "Proveedor Test", email, "555-0100")


def test_alta_y_lectura_de_proveedor(db):
    nuevo = _crear_proveedor(db, "prov_ok@example.com")
    assert nuevo is not None
    proveedor_id = nuevo[0]

    fila = obtener_proveedor(db, proveedor_id)
    assert len(fila) == 1
    assert fila[0][1] == "Proveedor Test"
    assert fila[0][3] == "prov_ok@example.com"


def test_crud_completo_de_producto(db):
    proveedor_id = _crear_proveedor(db, "prov_prod@example.com")[0]

    creado = agregar_producto(db, "Producto Test", "Cat Test", 10.5, 3, proveedor_id)
    assert creado is not None
    producto_id = creado[0]

    fila = obtener_producto(db, producto_id)
    assert fila[0][0] == "Producto Test"

    actualizar_stock(db, producto_id, 99)
    assert obtener_producto(db, producto_id)[0][2] == 99

    actualizar_producto(db, producto_id, 25.0, 3)  # 3 = precio
    assert float(obtener_producto(db, producto_id)[0][1]) == 25.0

    eliminar_producto(db, producto_id)
    assert obtener_producto(db, producto_id) == []


def test_email_duplicado_es_rechazado(db):
    assert _crear_proveedor(db, "dup@example.com") is not None
    # El segundo proveedor con el mismo email dispara UniqueViolation -> None.
    assert _crear_proveedor(db, "dup@example.com") is None


def test_producto_con_proveedor_inexistente_es_rechazado(db):
    # proveedor_id 999999 no existe -> ForeignKeyViolation -> None.
    resultado = agregar_producto(db, "Fantasma", "Cat", 9.99, 1, 999999)
    assert resultado is None


def test_producto_con_stock_negativo_no_se_inserta(db):
    proveedor_id = _crear_proveedor(db, "prov_stock@example.com")[0]
    # La validación de negocio corta antes de tocar la base -> None.
    resultado = agregar_producto(db, "Sin stock", "Cat", 5.0, -1, proveedor_id)
    assert resultado is None
