"""Logica de EMPLEADOS. No imprime: devuelve datos o levanta excepciones.

Columnas: id, nombre, apellido, puesto, email (unico), salario (numeric).
El id ya lo genera la base (IDENTITY).
"""

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar_afectando,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorValidacion
from validaciones import validar_decimal, validar_email, validar_texto

_COLUMNAS = "id, nombre, apellido, puesto, email, salario"


def listar_empleados(db):
    return consultar(db, "SELECT " + _COLUMNAS + " FROM empleados ORDER BY id")


def obtener_empleado(db, empleado_id):
    return consultar_uno(
        db, "SELECT " + _COLUMNAS + " FROM empleados WHERE id = %s", (empleado_id,)
    )


def agregar_empleado(db, nombre, apellido, puesto, email, salario):
    nombre = validar_texto(nombre, "nombre")
    apellido = validar_texto(apellido, "apellido")
    puesto = validar_texto(puesto, "puesto")
    email = validar_email(email)
    salario = validar_decimal(salario, "salario", minimo=0)
    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            "INSERT INTO empleados (nombre, apellido, puesto, email, salario) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (nombre, apellido, puesto, email, salario),
        )
    return fila[0]


def actualizar_empleado(db, empleado_id, campo, valor):
    """campo: 'nombre', 'apellido', 'puesto', 'email' o 'salario'."""
    if campo == "nombre":
        valor = validar_texto(valor, "nombre")
        sql = "UPDATE empleados SET nombre = %s WHERE id = %s"
    elif campo == "apellido":
        valor = validar_texto(valor, "apellido")
        sql = "UPDATE empleados SET apellido = %s WHERE id = %s"
    elif campo == "puesto":
        valor = validar_texto(valor, "puesto")
        sql = "UPDATE empleados SET puesto = %s WHERE id = %s"
    elif campo == "email":
        valor = validar_email(valor)
        sql = "UPDATE empleados SET email = %s WHERE id = %s"
    elif campo == "salario":
        valor = validar_decimal(valor, "salario", minimo=0)
        sql = "UPDATE empleados SET salario = %s WHERE id = %s"
    else:
        raise ErrorValidacion(
            "Campo invalido: use 'nombre', 'apellido', 'puesto', 'email' o 'salario'."
        )
    with transaccion(db):
        ejecutar_afectando(db, sql, (valor, empleado_id))


def eliminar_empleado(db, empleado_id):
    with transaccion(db):
        ejecutar_afectando(db, "DELETE FROM empleados WHERE id = %s", (empleado_id,))
