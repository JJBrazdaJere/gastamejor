"""Pruebas unitarias de `validaciones` (no necesitan base de datos).

Ahora los validadores LEVANTAN ErrorValidacion cuando el dato es malo,
en lugar de devolver True/False. Eso obliga a manejar el error en un solo
lugar y evita olvidarse de comprobar el resultado.
"""

import pytest

from errores import ErrorValidacion
from validaciones import (
    validar_decimal,
    validar_email,
    validar_email_opcional,
    validar_entero,
    validar_texto,
    validar_texto_opcional,
)


# --- validar_texto ----------------------------------------------------------
def test_validar_texto_recorta_espacios():
    assert validar_texto("  Hola  ", "nombre") == "Hola"


@pytest.mark.parametrize("valor", ["", "   ", None])
def test_validar_texto_invalido(valor):
    with pytest.raises(ErrorValidacion):
        validar_texto(valor, "nombre")


# --- validar_entero ---------------------------------------------------------
def test_validar_entero_ok():
    assert validar_entero("5", "stock") == 5


@pytest.mark.parametrize("valor", ["x", None, 1.5])
def test_validar_entero_invalido(valor):
    with pytest.raises(ErrorValidacion):
        validar_entero(valor, "stock")


def test_validar_entero_respeta_minimo():
    assert validar_entero(0, "stock", minimo=0) == 0
    with pytest.raises(ErrorValidacion):
        validar_entero(-1, "stock", minimo=0)


# --- validar_decimal --------------------------------------------------------
def test_validar_decimal_mayor_a_cero():
    assert validar_decimal("10.5", "precio", mayor_a=0) == 10.5
    with pytest.raises(ErrorValidacion):
        validar_decimal(0, "precio", mayor_a=0)
    with pytest.raises(ErrorValidacion):
        validar_decimal(-3, "precio", mayor_a=0)


def test_validar_decimal_respeta_minimo():
    assert validar_decimal(0, "salario", minimo=0) == 0
    with pytest.raises(ErrorValidacion):
        validar_decimal(-1, "salario", minimo=0)


# --- validar_email ----------------------------------------------------------
@pytest.mark.parametrize("email", ["ventas@techsupply.com", "a.b+c@sub.dominio.com"])
def test_email_valido(email):
    assert validar_email(email) == email


@pytest.mark.parametrize("email", ["sin-arroba", "a@b", "a@@b.com", "", None])
def test_email_invalido(email):
    with pytest.raises(ErrorValidacion):
        validar_email(email)


def test_email_opcional_acepta_vacio():
    assert validar_email_opcional(None) is None
    assert validar_email_opcional("   ") is None
    assert validar_email_opcional("ok@example.com") == "ok@example.com"


def test_texto_opcional_acepta_vacio():
    assert validar_texto_opcional(None) is None
    assert validar_texto_opcional("   ") is None
    assert validar_texto_opcional("  x ") == "x"
