"""Pruebas de INGRESOS contra PostgreSQL (el fixture `db` revierte todo)."""

import pytest

from cuentas import actualizar_perfil, registrar, verificar_email
from errores import ErrorNoEncontrado, ErrorValidacion
from ingresos import (
    agregar,
    eliminar,
    listar,
    resumen_anual,
    resumen_mes,
    total_diario_mes,
)


def _cuenta(db, sufijo):
    r = registrar(db, "Ingresos Test", "ing_" + sufijo, "password123", "ing_" + sufijo + "@example.com")
    verificar_email(db, r["email"], r["codigo_test"])
    return r["id"]


def test_agregar_y_listar(db):
    cid = _cuenta(db, "a1")
    agregar(db, cid, "1000", "2026-10-01", "Dia 1")
    agregar(db, cid, "2000", "2026-10-02")
    filas = listar(db, cid, "2026-10")
    assert len(filas) == 2
    assert filas[0][2] == 2000  # ordenado por fecha desc


def test_monto_debe_ser_positivo(db):
    cid = _cuenta(db, "a2")
    with pytest.raises(ErrorValidacion):
        agregar(db, cid, "0")
    with pytest.raises(ErrorValidacion):
        agregar(db, cid, "-5")


def test_fecha_invalida(db):
    cid = _cuenta(db, "a3")
    with pytest.raises(ErrorValidacion):
        agregar(db, cid, "100", "31/12/2026")


def test_mes_invalido(db):
    cid = _cuenta(db, "a4")
    with pytest.raises(ErrorValidacion):
        resumen_mes(db, cid, "2026-13")


def test_total_diario_y_resumen_del_mes(db):
    cid = _cuenta(db, "a5")
    agregar(db, cid, "1000", "2026-10-01")
    agregar(db, cid, "2500.50", "2026-10-15")
    agregar(db, cid, "999", "2026-11-01")  # otro mes: no debe sumar

    total, cantidad = total_diario_mes(db, cid, "2026-10")
    assert str(total) == "3500.50"
    assert cantidad == 2

    resumen = resumen_mes(db, cid, "2026-10")
    assert resumen["mes"] == "2026-10"
    assert resumen["total_diario"] == "3500.50"
    assert resumen["ingreso_fijo"] == "0.00"
    assert resumen["total"] == "3500.50"
    assert resumen["cantidad"] == 2


def test_resumen_incluye_ingreso_fijo(db):
    cid = _cuenta(db, "a6")
    actualizar_perfil(db, cid, ingreso_fijo_mensual="10000")
    agregar(db, cid, "1000", "2026-10-05")
    resumen = resumen_mes(db, cid, "2026-10")
    assert resumen["total_diario"] == "1000.00"
    assert resumen["ingreso_fijo"] == "10000.00"
    assert resumen["total"] == "11000.00"


def test_eliminar(db):
    cid = _cuenta(db, "a7")
    ingreso_id = agregar(db, cid, "500", "2026-10-03")
    eliminar(db, cid, ingreso_id)
    assert listar(db, cid, "2026-10") == []


def test_eliminar_inexistente(db):
    cid = _cuenta(db, "a8")
    with pytest.raises(ErrorNoEncontrado):
        eliminar(db, cid, 999999)


def test_un_usuario_no_borra_ingresos_de_otro(db):
    cid_a = _cuenta(db, "a9")
    cid_b = _cuenta(db, "b9")
    ingreso_id = agregar(db, cid_a, "500", "2026-10-03")
    with pytest.raises(ErrorNoEncontrado):
        eliminar(db, cid_b, ingreso_id)


def test_resumen_anual(db):
    cid = _cuenta(db, "an")
    agregar(db, cid, "1000", "2026-01-10")
    agregar(db, cid, "2000", "2026-02-10")
    agregar(db, cid, "500", "2027-01-10")
    filas = resumen_anual(db, cid, 2026)
    meses = [f["mes"] for f in filas]
    assert meses == ["2026-01", "2026-02"]
