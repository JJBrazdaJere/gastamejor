"""Pruebas de VENTAS contra PostgreSQL.

Verifican lo más importante del módulo:
  - la venta descuenta stock,
  - se valida el stock disponible,
  - las cantidades repetidas se suman,
  - se guarda el precio del momento,
  - anular devuelve el stock,
  - todo es atómico (si falla, no queda nada a medias).

El fixture `db` (conftest.py) usa savepoints, así que un fallo dentro de un
test no borra lo ya preparado en ese mismo test.
"""

import pytest

from clientes import agregar_cliente
from empleados import agregar_empleado
from errores import ErrorNoEncontrado, ErrorValidacion
from productos import agregar_producto, obtener_producto
from proveedores import agregar_proveedor
from ventas import agregar_venta, eliminar_venta, listar_ventas, obtener_venta


def _contexto(db):
    """Crea un proveedor, un producto (stock 10), un cliente y un empleado."""
    proveedor = agregar_proveedor(db, "Prov Ventas", "prov_ventas@example.com", "555")
    producto = agregar_producto(db, "Prod Ventas", "Cat", 100.0, 10, proveedor)
    cliente = agregar_cliente(db, "Cli Ventas", "cli_ventas@example.com")
    empleado = agregar_empleado(
        db, "Emp", "Ventas", "Vendedor", "emp_ventas@example.com", 1000
    )
    return cliente, empleado, producto


def test_registrar_venta_descuenta_stock_y_guarda_precio(db):
    cliente, empleado, producto = _contexto(db)

    venta_id = agregar_venta(db, cliente, empleado, [(producto, 3)])
    assert venta_id > 0

    # 10 - 3 = 7
    assert obtener_producto(db, producto)[4] == 7

    cabecera, lineas = obtener_venta(db, venta_id)
    assert len(lineas) == 1
    assert lineas[0][2] == 3                 # cantidad
    assert float(lineas[0][3]) == 100.0      # precio_unitario guardado


def test_producto_repetido_suma_cantidades(db):
    cliente, empleado, producto = _contexto(db)

    venta_id = agregar_venta(db, cliente, empleado, [(producto, 2), (producto, 3)])
    _, lineas = obtener_venta(db, venta_id)
    assert len(lineas) == 1
    assert lineas[0][2] == 5
    assert obtener_producto(db, producto)[4] == 5   # 10 - 5


def test_venta_sin_stock_falla_y_no_cambia_nada(db):
    cliente, empleado, producto = _contexto(db)
    with pytest.raises(ErrorValidacion):
        agregar_venta(db, cliente, empleado, [(producto, 99)])
    # El stock quedó intacto: la operación falló entera.
    assert obtener_producto(db, producto)[4] == 10


def test_venta_de_producto_inexistente_falla(db):
    cliente, empleado, _ = _contexto(db)
    with pytest.raises(ErrorNoEncontrado):
        agregar_venta(db, cliente, empleado, [(999999, 1)])


def test_venta_de_cliente_inexistente_falla(db):
    _, empleado, producto = _contexto(db)
    with pytest.raises(ErrorNoEncontrado):
        agregar_venta(db, 999999, empleado, [(producto, 1)])


def test_venta_sin_productos_es_invalida(db):
    cliente, empleado, _ = _contexto(db)
    with pytest.raises(ErrorValidacion):
        agregar_venta(db, cliente, empleado, [])


def test_anular_venta_devuelve_stock(db):
    cliente, empleado, producto = _contexto(db)

    venta_id = agregar_venta(db, cliente, empleado, [(producto, 4)])
    assert obtener_producto(db, producto)[4] == 6

    eliminar_venta(db, venta_id)
    assert obtener_producto(db, producto)[4] == 10
    assert obtener_venta(db, venta_id) is None


def test_anular_venta_inexistente_falla(db):
    with pytest.raises(ErrorNoEncontrado):
        eliminar_venta(db, 999999)


def test_listar_ventas_incluye_la_venta(db):
    cliente, empleado, producto = _contexto(db)
    venta_id = agregar_venta(db, cliente, empleado, [(producto, 2)])

    filas = listar_ventas(db)
    assert any(fila[0] == venta_id for fila in filas)
