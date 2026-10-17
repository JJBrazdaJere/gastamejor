"""Pruebas de la recuperación de contraseña (fixture `db`, todo se revierte)."""

from datetime import datetime, timedelta, timezone

import pytest

from base_datos import ejecutar_afectando
from cuentas import (
    cliente_por_token,
    iniciar_sesion,
    pedir_recuperacion,
    registrar,
    restablecer_password,
    verificar_email,
)
from errores import ErrorNoEncontrado, ErrorValidacion


def _ahora_utc():
    return datetime.now(timezone.utc)


def _cuenta_verificada(db, sufijo):
    r = registrar(
        db, "Usuario Test", "rec" + sufijo, "password123", "rec" + sufijo + "@example.com"
    )
    verificar_email(db, r["email"], r["codigo_test"])
    return r


def test_flujo_feliz_recuperacion(db):
    r = _cuenta_verificada(db, "_f1")
    pedido = pedir_recuperacion(db, r["email"])
    assert pedido["codigo_test"] and pedido["codigo_test"].isdigit()

    res = restablecer_password(db, r["email"], pedido["codigo_test"], "nueva_password")
    assert res["token"]
    assert res["cliente"]["id"] == r["id"]
    assert cliente_por_token(db, res["token"])["id"] == r["id"]

    # La contraseña vieja ya no entra; la nueva sí.
    with pytest.raises(ErrorValidacion):
        iniciar_sesion(db, r["usuario"], "password123")
    assert iniciar_sesion(db, r["usuario"], "nueva_password")["token"]


def test_sesion_abierta_antes_queda_invalidada(db):
    r = _cuenta_verificada(db, "_f2")
    vieja = iniciar_sesion(db, r["email"], "password123")
    assert cliente_por_token(db, vieja["token"]) is not None

    pedido = pedir_recuperacion(db, r["email"])
    restablecer_password(db, r["email"], pedido["codigo_test"], "nueva_password")

    # La sesión que estaba abierta ya no sirve.
    assert cliente_por_token(db, vieja["token"]) is None


def test_codigo_incorrecto_avisa(db):
    r = _cuenta_verificada(db, "_f3")
    pedido = pedir_recuperacion(db, r["email"])
    malo = "000000" if pedido["codigo_test"] != "000000" else "111111"
    with pytest.raises(ErrorValidacion):
        restablecer_password(db, r["email"], malo, "nueva_password")


def test_codigo_vencido_avisa_y_pide_uno_nuevo(db):
    r = _cuenta_verificada(db, "_f4")
    pedido = pedir_recuperacion(db, r["email"])
    ejecutar_afectando(
        db,
        "UPDATE clientes SET codigo_recuperacion_expira = %s WHERE lower(email) = lower(%s)",
        (_ahora_utc() - timedelta(minutes=1), r["email"]),
    )
    with pytest.raises(ErrorValidacion, match="nuevo"):
        restablecer_password(db, r["email"], pedido["codigo_test"], "nueva_password")
    # El código vencido se borró: ahora no hay nada pendiente.
    with pytest.raises(ErrorValidacion, match="pendiente"):
        restablecer_password(db, r["email"], pedido["codigo_test"], "nueva_password")


def test_cinco_intentos_fallidos_agotan_el_codigo(db):
    r = _cuenta_verificada(db, "_f5")
    pedido = pedir_recuperacion(db, r["email"])
    correcto = pedido["codigo_test"]
    malo = "000000" if correcto != "000000" else "111111"

    for _ in range(5):
        with pytest.raises(ErrorValidacion):
            restablecer_password(db, r["email"], malo, "nueva_password")

    # Ya ni con el código correcto: hay que pedir uno nuevo.
    with pytest.raises(ErrorValidacion, match="intentos"):
        restablecer_password(db, r["email"], correcto, "nueva_password")


def test_enfriamiento_no_deja_pedir_otro_codigo(db):
    r = _cuenta_verificada(db, "_f6")
    pedir_recuperacion(db, r["email"])
    with pytest.raises(ErrorValidacion, match="minutos"):
        pedir_recuperacion(db, r["email"])


def test_pedir_para_email_inexistente_no_revela_nada(db):
    res = pedir_recuperacion(db, "no-existe-rec@example.com")
    # Misma respuesta genérica, sin código: no se puede saber si la cuenta existe.
    assert res["email"] == "no-existe-rec@example.com"
    assert res["codigo_test"] is None
    assert "existe una cuenta" in res["mensaje"]


def test_restablecer_email_inexistente_avisa(db):
    with pytest.raises(ErrorNoEncontrado):
        restablecer_password(db, "no-existe-rec2@example.com", "123456", "nueva_password")


def test_restablecer_sin_codigo_pendiente_avisa(db):
    r = _cuenta_verificada(db, "_f7")
    with pytest.raises(ErrorValidacion, match="pendiente"):
        restablecer_password(db, r["email"], "123456", "nueva_password")


def test_restablecer_exige_password_larga(db):
    r = _cuenta_verificada(db, "_f8")
    pedido = pedir_recuperacion(db, r["email"])
    with pytest.raises(ErrorValidacion):
        restablecer_password(db, r["email"], pedido["codigo_test"], "corta")
