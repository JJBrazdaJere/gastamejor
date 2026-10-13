"""Pruebas de CUENTAS contra PostgreSQL (el fixture `db` revierte todo)."""

import pytest

from cuentas import (
    actualizar_perfil,
    cambiar_password,
    cerrar_sesion,
    cliente_por_token,
    eliminar_cuenta,
    iniciar_sesion,
    obtener_por_id,
    registrar,
    reenviar_codigo,
    verificar_email,
)
from errores import ErrorNoEncontrado, ErrorUnico, ErrorValidacion
from ingresos import agregar, listar


def _registrar_verificado(db, sufijo):
    registro = registrar(
        db, "Usuario Test", "user" + sufijo, "password123", "user" + sufijo + "@example.com"
    )
    verificar_email(db, registro["email"], registro["codigo_test"])
    return registro


def test_registro_devuelve_codigo_en_modo_test(db):
    r = registrar(db, "Ana", "ana_test", "password123", "ana_test@example.com")
    assert r["id"] > 0
    assert r["email_verificado"] is False
    assert r["codigo_test"] and r["codigo_test"].isdigit()


def test_email_duplicado_es_rechazado(db):
    registrar(db, "A", "cuenta_a1", "password123", "dup_cuenta@example.com")
    with pytest.raises(ErrorUnico):
        registrar(db, "B", "cuenta_b1", "password123", "dup_cuenta@example.com")


def test_usuario_duplicado_es_rechazado(db):
    registrar(db, "A", "mismo_user", "password123", "cu1@example.com")
    with pytest.raises(ErrorUnico):
        registrar(db, "B", "mismo_user", "password123", "cu2@example.com")


def test_usuario_muy_corto_es_rechazado(db):
    with pytest.raises(ErrorValidacion):
        registrar(db, "A", "a", "password123", "cu3@example.com")


def test_password_corta_es_rechazada(db):
    with pytest.raises(ErrorValidacion):
        registrar(db, "A", "cuenta_corta", "123", "cu4@example.com")


def test_verificar_email_con_codigo_correcto(db):
    r = registrar(db, "V", "cuenta_v1", "password123", "v1@example.com")
    assert verificar_email(db, r["email"], r["codigo_test"]) is True
    # Es idempotente: verificarlo de nuevo no rompe.
    assert verificar_email(db, r["email"], r["codigo_test"]) is True


def test_verificar_email_con_codigo_malo(db):
    r = registrar(db, "V", "cuenta_v2", "password123", "v2@example.com")
    malo = "000000" if r["codigo_test"] != "000000" else "111111"
    with pytest.raises(ErrorValidacion):
        verificar_email(db, r["email"], malo)


def test_login_requiere_email_verificado(db):
    registrar(db, "L", "cuenta_l1", "password123", "l1@example.com")
    with pytest.raises(ErrorValidacion):
        iniciar_sesion(db, "cuenta_l1", "password123")


def test_login_ok_y_sesion(db):
    r = _registrar_verificado(db, "_s1")
    sesion = iniciar_sesion(db, r["usuario"], "password123")
    assert sesion["token"]
    cliente = cliente_por_token(db, sesion["token"])
    assert cliente["id"] == r["id"]
    # Tambien se puede entrar con el email.
    sesion2 = iniciar_sesion(db, r["email"], "password123")
    assert sesion2["token"] != sesion["token"]


def test_login_con_password_mala(db):
    r = _registrar_verificado(db, "_s2")
    with pytest.raises(ErrorValidacion):
        iniciar_sesion(db, r["usuario"], "otra_password")


def test_cerrar_sesion_invalida_el_token(db):
    r = _registrar_verificado(db, "_s3")
    sesion = iniciar_sesion(db, r["usuario"], "password123")
    cerrar_sesion(db, sesion["token"])
    assert cliente_por_token(db, sesion["token"]) is None


def test_token_inexistente_devuelve_none(db):
    assert cliente_por_token(db, "token-que-no-existe") is None


def test_actualizar_perfil(db):
    r = _registrar_verificado(db, "_p1")
    actualizar_perfil(db, r["id"], telefono="11-5555-0000", ingreso_fijo_mensual="50000", moneda="USD")
    cliente = obtener_por_id(db, r["id"])
    assert cliente["telefono"] == "11-5555-0000"
    assert cliente["ingreso_fijo_mensual"] == "50000.00"
    assert cliente["moneda"] == "USD"


def test_actualizar_perfil_moneda_invalida(db):
    r = _registrar_verificado(db, "_p2")
    with pytest.raises(ErrorValidacion):
        actualizar_perfil(db, r["id"], moneda="XXX")


def test_actualizar_perfil_sin_cambios_avisa(db):
    r = _registrar_verificado(db, "_p4")
    with pytest.raises(ErrorValidacion):
        actualizar_perfil(db, r["id"])


def test_cambiar_password(db):
    r = _registrar_verificado(db, "_p3")
    cambiar_password(db, r["id"], "password123", "nueva_password")
    with pytest.raises(ErrorValidacion):
        iniciar_sesion(db, r["usuario"], "password123")
    sesion = iniciar_sesion(db, r["usuario"], "nueva_password")
    assert sesion["token"]


def test_cambiar_password_actual_mala(db):
    r = _registrar_verificado(db, "_p5")
    with pytest.raises(ErrorValidacion):
        cambiar_password(db, r["id"], "no-es-la-actual", "nueva_password")


def test_reenviar_codigo(db):
    r = registrar(db, "R", "cuenta_r1", "password123", "r1@example.com")
    reenvio = reenviar_codigo(db, r["email"])
    assert reenvio["codigo_test"]
    verificar_email(db, r["email"], reenvio["codigo_test"])


def test_reenviar_codigo_a_cuenta_verificada_avisa(db):
    r = _registrar_verificado(db, "_r2")
    with pytest.raises(ErrorValidacion):
        reenviar_codigo(db, r["email"])


# ---------------------------------------------------------------------------
# Eliminar cuenta
# ---------------------------------------------------------------------------
def test_eliminar_cuenta_borra_cuenta_y_datos(db):
    r = _registrar_verificado(db, "_d1")
    sesion = iniciar_sesion(db, r["usuario"], "password123")
    agregar(db, r["id"], "1000", "2026-01-15")

    assert eliminar_cuenta(db, r["id"], "password123") is True

    # Ya no existe la cuenta, ni su sesion, ni sus ingresos (borrado en cascada).
    assert obtener_por_id(db, r["id"]) is None
    assert cliente_por_token(db, sesion["token"]) is None
    assert listar(db, r["id"]) == []


def test_eliminar_cuenta_password_mala_no_borra(db):
    r = _registrar_verificado(db, "_d2")
    with pytest.raises(ErrorValidacion):
        eliminar_cuenta(db, r["id"], "no-es-la-clave")
    # La cuenta sigue existiendo.
    assert obtener_por_id(db, r["id"]) is not None


def test_eliminar_cuenta_inexistente_avisa(db):
    with pytest.raises(ErrorNoEncontrado):
        eliminar_cuenta(db, 99999999, "password123")
