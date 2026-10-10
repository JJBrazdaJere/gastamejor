"""Pruebas de EMPLEADOS contra PostgreSQL (el fixture `db` revierte todo)."""

import pytest

from empleados import (
    actualizar_empleado,
    agregar_empleado,
    eliminar_empleado,
    obtener_empleado,
)
from errores import ErrorUnico, ErrorValidacion


def test_alta_y_lectura_de_empleado(db):
    empleado_id = agregar_empleado(
        db, "Ana", "Lopez", "Vendedor", "ana@example.com", 500000
    )
    fila = obtener_empleado(db, empleado_id)
    assert fila[1] == "Ana"
    assert fila[2] == "Lopez"
    assert fila[3] == "Vendedor"
    assert fila[4] == "ana@example.com"
    assert float(fila[5]) == 500000.0


def test_id_se_genera_automaticamente(db):
    primero = agregar_empleado(db, "A", "B", "P", "e1@example.com", 1)
    segundo = agregar_empleado(db, "C", "D", "P", "e2@example.com", 1)
    assert segundo > primero


def test_email_duplicado_de_empleado_es_rechazado(db):
    agregar_empleado(db, "A", "B", "P", "dupe@example.com", 100)
    with pytest.raises(ErrorUnico):
        agregar_empleado(db, "C", "D", "P", "dupe@example.com", 100)


def test_salario_negativo_es_rechazado(db):
    with pytest.raises(ErrorValidacion):
        agregar_empleado(db, "A", "B", "P", "neg@example.com", -1)


def test_salario_cero_es_valido(db):
    empleado_id = agregar_empleado(db, "A", "B", "P", "cero@example.com", 0)
    assert float(obtener_empleado(db, empleado_id)[5]) == 0.0


def test_actualizar_y_eliminar_empleado(db):
    empleado_id = agregar_empleado(db, "A", "B", "P", "edit@example.com", 100)

    actualizar_empleado(db, empleado_id, "puesto", "Gerente")
    assert obtener_empleado(db, empleado_id)[3] == "Gerente"

    actualizar_empleado(db, empleado_id, "salario", 999.5)
    assert float(obtener_empleado(db, empleado_id)[5]) == 999.5

    eliminar_empleado(db, empleado_id)
    assert obtener_empleado(db, empleado_id) is None
