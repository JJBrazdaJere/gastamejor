"""Logica de INGRESOS diarios.

Cada usuario carga lo que gano cada dia. El total de un mes es la suma de
esos ingresos MAS el "ingreso_fijo_mensual" de su cuenta (si cargo uno).

Este modulo NO imprime: devuelve datos o levanta excepciones.
"""

import re
from datetime import date
from decimal import Decimal

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorNoEncontrado, ErrorValidacion
from validaciones import formatear_monto, validar_decimal, validar_entero, validar_texto_opcional

_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validar_mes(mes):
    """Acepta y devuelve 'AAAA-MM' (ej: 2026-10)."""
    if not mes or not _MES.match(str(mes).strip()):
        raise ErrorValidacion("El mes debe tener el formato AAAA-MM (por ejemplo 2026-10).")
    return str(mes).strip()


def _primer_dia(mes):
    return mes + "-01"


def _validar_fecha(fecha):
    if fecha is None or str(fecha).strip() == "":
        return date.today()
    try:
        return date.fromisoformat(str(fecha).strip())
    except ValueError:
        raise ErrorValidacion("La fecha debe tener el formato AAAA-MM-DD.")


def agregar(db, cliente_id, monto, fecha=None, descripcion=None):
    """Registra un ingreso diario. Devuelve el id nuevo."""
    monto = validar_decimal(monto, "monto", mayor_a=0)
    fecha = _validar_fecha(fecha)
    descripcion = validar_texto_opcional(descripcion)
    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            """
            INSERT INTO ingresos (cliente_id, fecha, monto, descripcion)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (cliente_id, fecha, monto, descripcion),
        )
    return fila[0]


def listar(db, cliente_id, mes=None):
    """Ingresos del usuario. Si se pasa `mes`, solo los de ese mes."""
    if mes is not None and str(mes).strip() != "":
        mes = validar_mes(mes)
        return consultar(
            db,
            """
            SELECT id, fecha, monto, descripcion
            FROM ingresos
            WHERE cliente_id = %s
              AND fecha >= %s::date
              AND fecha < (%s::date + interval '1 month')
            ORDER BY fecha DESC, id DESC
            """,
            (cliente_id, _primer_dia(mes), _primer_dia(mes)),
        )
    return consultar(
        db,
        "SELECT id, fecha, monto, descripcion FROM ingresos "
        "WHERE cliente_id = %s ORDER BY fecha DESC, id DESC",
        (cliente_id,),
    )


def eliminar(db, cliente_id, ingreso_id):
    with transaccion(db):
        filas = ejecutar(
            db, "DELETE FROM ingresos WHERE id = %s AND cliente_id = %s", (ingreso_id, cliente_id)
        )
    if filas == 0:
        raise ErrorNoEncontrado("Ese ingreso no existe.")
    return True


def total_diario_mes(db, cliente_id, mes):
    """Suma de los ingresos diarios del mes (sin el fijo)."""
    mes = validar_mes(mes)
    fila = consultar_uno(
        db,
        """
        SELECT COALESCE(SUM(monto), 0), COUNT(*)
        FROM ingresos
        WHERE cliente_id = %s
          AND fecha >= %s::date
          AND fecha < (%s::date + interval '1 month')
        """,
        (cliente_id, _primer_dia(mes), _primer_dia(mes)),
    )
    total = fila[0] if fila and fila[0] is not None else Decimal("0")
    cantidad = fila[1] if fila else 0
    return total, cantidad


def _ingreso_fijo(db, cliente_id):
    fila = consultar_uno(
        db, "SELECT ingreso_fijo_mensual, moneda FROM clientes WHERE id = %s", (cliente_id,)
    )
    if not fila:
        raise ErrorNoEncontrado("Cuenta no encontrada.")
    return (fila[0] if fila[0] is not None else Decimal("0")), (fila[1] or "ARS")


def resumen_mes(db, cliente_id, mes):
    """Totales del mes: diarios + fijo = total."""
    mes = validar_mes(mes)
    total_diario, cantidad = total_diario_mes(db, cliente_id, mes)
    fijo, moneda = _ingreso_fijo(db, cliente_id)
    return {
        "mes": mes,
        "total_diario": formatear_monto(total_diario),
        "ingreso_fijo": formatear_monto(fijo),
        "total": formatear_monto(total_diario + fijo),
        "cantidad": cantidad,
        "moneda": moneda,
    }


def resumen_anual(db, cliente_id, anio):
    """Lista mes a mes (los meses con ingresos) de un ano."""
    anio = validar_entero(anio, "anio", minimo=1900)
    filas = consultar(
        db,
        """
        SELECT to_char(date_trunc('month', fecha), 'YYYY-MM') AS mes,
               SUM(monto), COUNT(*)
        FROM ingresos
        WHERE cliente_id = %s AND EXTRACT(YEAR FROM fecha) = %s
        GROUP BY date_trunc('month', fecha)
        ORDER BY 1
        """,
        (cliente_id, anio),
    )
    return [{"mes": mes, "total": formatear_monto(total), "cantidad": cantidad} for mes, total, cantidad in filas]
