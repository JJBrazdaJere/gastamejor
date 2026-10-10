"""Pruebas unitarias: no necesitan base de datos."""

from productos import (
    validar_categoria,
    validar_nombre,
    validar_precio,
    validar_stock,
)
from proveedores import validar_email
from proveedores import validar_nombre as validar_nombre_proveedor


# --- productos.validar_stock -------------------------------------------------
def test_stock_negativo_es_invalido():
    assert validar_stock(-1) is False


def test_stock_cero_y_positivo_son_validos():
    assert validar_stock(0) is True
    assert validar_stock(5) is True


# --- productos.validar_nombre ------------------------------------------------
def test_nombre_vacio_o_solo_espacios_es_invalido():
    assert validar_nombre("") is False
    assert validar_nombre("   ") is False


def test_nombre_con_texto_es_valido():
    assert validar_nombre("Teclado") is True


# --- productos.validar_precio ------------------------------------------------
def test_precio_cero_o_negativo_es_invalido():
    assert validar_precio(0) is False
    assert validar_precio(-5) is False


def test_precio_positivo_es_valido():
    assert validar_precio(0.01) is True
    assert validar_precio(1500) is True


# --- productos.validar_categoria ---------------------------------------------
def test_categoria_vacia_es_invalida():
    assert validar_categoria("") is False
    assert validar_categoria("  ") is False


def test_categoria_con_texto_es_valida():
    assert validar_categoria("Periféricos") is True


# --- proveedores.validar_email ----------------------------------------------
def test_email_valido():
    assert validar_email("ventas@techsupply.com") is True
    assert validar_email("a.b+c@sub.dominio.com") is True


def test_email_invalido():
    assert validar_email("sin-arroba") is False
    assert validar_email("a@b") is False          # sin dominio de 2+ letras
    assert validar_email("a@@b.com") is False
    assert validar_email("") is False


def test_email_none_no_rompe():
    # Antes lanzaba TypeError; ahora debe devolver False sin excepción.
    assert validar_email(None) is False


# --- proveedores.validar_nombre ---------------------------------------------
def test_nombre_proveedor_vacio_es_invalido():
    assert validar_nombre_proveedor("") is False
    assert validar_nombre_proveedor("Proveedor OK") is True
