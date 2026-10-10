"""Pruebas de CLIENTES y de la distincion error / no-encontrado.

Usan el fixture `db` (ver conftest.py): todo se revierte al final.
"""

from base_datos import estado_operacion
from clientes import (
    agregar_cliente,
    actualizar_cliente,
    eliminar_cliente,
    obtener_cliente,
)
from productos import actualizar_stock


# --- estado_operacion: distingue los 3 casos --------------------------------
def test_estado_operacion_distingue_casos():
    assert estado_operacion(None) == "error"          # error de base de datos
    assert estado_operacion(0) == "no_encontrado"     # 0 filas afectadas
    assert estado_operacion(3) == "ok"                # 3 filas afectadas
    assert estado_operacion((7,)) == "ok"             # tupla de RETURNING


# --- CRUD de clientes --------------------------------------------------------
def test_alta_y_lectura_de_cliente(db):
    nuevo = agregar_cliente(db, "Cliente Test", "cli_ok@example.com", "555-0200")
    assert nuevo is not None
    cliente_id = nuevo[0]

    fila = obtener_cliente(db, cliente_id)
    assert len(fila) == 1
    assert fila[0][1] == "Cliente Test"
    assert fila[0][3] == "cli_ok@example.com"


def test_id_de_cliente_se_genera_incremental(db):
    primero = agregar_cliente(db, "C1", "c1@example.com")[0]
    segundo = agregar_cliente(db, "C2", "c2@example.com")[0]
    assert segundo == primero + 1


def test_telefono_de_cliente_es_opcional(db):
    nuevo = agregar_cliente(db, "Sin Tel", "sintel@example.com")
    assert nuevo is not None
    assert obtener_cliente(db, nuevo[0])[0][2] is None


def test_email_duplicado_de_cliente_es_rechazado(db):
    assert agregar_cliente(db, "C1", "dup_cli@example.com") is not None
    assert agregar_cliente(db, "C2", "dup_cli@example.com") is None


def test_actualizar_y_eliminar_cliente(db):
    cliente_id = agregar_cliente(db, "C1", "edit_cli@example.com", "123")[0]

    actualizar_cliente(db, cliente_id, "C1 Nuevo", 1)  # 1 = nombre
    assert obtener_cliente(db, cliente_id)[0][1] == "C1 Nuevo"

    eliminar_cliente(db, cliente_id)
    assert obtener_cliente(db, cliente_id) == []


# --- La mejora clave: no confundir error con "no encontrado" -----------------
def test_actualizar_producto_inexistente_dice_no_encontrado(db, capsys):
    actualizar_stock(db, 999999, 5)
    salida = capsys.readouterr().out
    assert "Producto no encontrado" in salida


def test_error_de_base_no_se_confunde_con_no_encontrado(db, capsys):
    agregar_cliente(db, "C1", "err1@example.com")
    c2 = agregar_cliente(db, "C2", "err2@example.com")[0]

    # Cambiar el email del C2 al del C1 -> UniqueViolation (error de base),
    # NO es un "cliente no encontrado".
    actualizar_cliente(db, c2, "err1@example.com", 3)  # 3 = email

    salida = capsys.readouterr().out
    assert "Error:" in salida
    assert "no encontrado" not in salida
