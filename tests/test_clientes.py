"""Pruebas de CLIENTES contra PostgreSQL (el fixture `db` revierte todo)."""

import pytest

from clientes import (
    actualizar_cliente,
    agregar_cliente,
    eliminar_cliente,
    listar_clientes,
    obtener_cliente,
)
from errores import ErrorNoEncontrado, ErrorUnico, ErrorValidacion


def test_alta_y_lectura_de_cliente(db):
    cliente_id = agregar_cliente(db, "Cliente Test", "cli_ok@example.com", "555-0200")
    fila = obtener_cliente(db, cliente_id)
    assert fila[1] == "Cliente Test"
    assert fila[3] == "cli_ok@example.com"


def test_id_se_genera_automaticamente(db):
    # No pasamos id: lo genera la base (IDENTITY). Deben ser crecientes.
    primero = agregar_cliente(db, "C1", "c1@example.com")
    segundo = agregar_cliente(db, "C2", "c2@example.com")
    assert isinstance(primero, int) and primero > 0
    assert segundo > primero


def test_telefono_de_cliente_es_opcional(db):
    cliente_id = agregar_cliente(db, "Sin Tel", "sintel@example.com")
    assert obtener_cliente(db, cliente_id)[2] is None


def test_email_duplicado_de_cliente_es_rechazado(db):
    agregar_cliente(db, "C1", "dup_cli@example.com")
    with pytest.raises(ErrorUnico):
        agregar_cliente(db, "C2", "dup_cli@example.com")


def test_email_invalido_es_rechazado(db):
    with pytest.raises(ErrorValidacion):
        agregar_cliente(db, "C1", "no-es-un-email")


def test_actualizar_y_eliminar_cliente(db):
    cliente_id = agregar_cliente(db, "C1", "edit_cli@example.com", "123")

    actualizar_cliente(db, cliente_id, "nombre", "C1 Nuevo")
    assert obtener_cliente(db, cliente_id)[1] == "C1 Nuevo"

    eliminar_cliente(db, cliente_id)
    assert obtener_cliente(db, cliente_id) is None


def test_actualizar_cliente_inexistente_avisa(db):
    with pytest.raises(ErrorNoEncontrado):
        actualizar_cliente(db, 999999, "nombre", "X")


def test_listar_clientes_devuelve_lista(db):
    agregar_cliente(db, "Listado", "listar@example.com")
    correos = [fila[3] for fila in listar_clientes(db)]
    assert "listar@example.com" in correos
