"""Pruebas de SEGURIDAD (no tocan la base de datos)."""

import pytest

from errores import ErrorValidacion
from seguridad import (
    generar_codigo,
    generar_token,
    hashear_password,
    verificar_password,
)


def test_hash_no_guarda_la_contrasena_en_claro():
    almacenado = hashear_password("secreto123")
    assert "secreto123" not in almacenado
    assert almacenado.startswith("scrypt$")


def test_verificar_password_correcta_e_incorrecta():
    almacenado = hashear_password("secreto123")
    assert verificar_password("secreto123", almacenado) is True
    assert verificar_password("otra-cosa", almacenado) is False


def test_dos_hashes_del_mismo_password_son_distintos():
    # Por la sal aleatoria: asi no se puede comparar "a ojo".
    assert hashear_password("secreto123") != hashear_password("secreto123")


def test_password_corta_es_rechazada():
    with pytest.raises(ErrorValidacion):
        hashear_password("corta")


def test_verificar_password_con_datos_raros_no_rompe():
    assert verificar_password("x", "no-es-un-hash") is False
    assert verificar_password("x", None) is False
    assert verificar_password(None, "scrypt$1$2$3$aa$bb") is False


def test_token_largo_y_unico():
    t1 = generar_token()
    t2 = generar_token()
    assert t1 != t2
    assert len(t1) >= 32


def test_codigo_es_numerico_de_6():
    codigo = generar_codigo()
    assert len(codigo) == 6
    assert codigo.isdigit()
