"""Acceso generico a PostgreSQL.

Reglas de esta capa:
  - NO imprime nada: devuelve datos o levanta una excepcion de `errores`.
  - NO confirma (commit) por si sola. Para escribir se usa el context manager
    `transaccion(db)`, que confirma todo junto o revierte todo si algo falla.

Ese diseno permite operaciones ATOMICAS: por ejemplo, registrar una venta
(cabecera + lineas + descuento de stock) como una sola unidad.
"""

import psycopg

from errores import ErrorBaseDatos, ErrorClaveForanea, ErrorNoEncontrado, ErrorUnico


def transaccion(db):
    """Agrupa operaciones: confirma al salir, revierte si hay cualquier error.

    Uso:
        with transaccion(db):
            ejecutar(db, "UPDATE ...")
            ejecutar(db, "INSERT ...")

    Si ya hay una transaccion en curso, usa un SAVEPOINT automaticamente
    (asi el fallo de una operacion interna no arrastra a las anteriores).

    Devuelve el context manager de psycopg (no es un generador): se usa
    siempre como `with transaccion(db):`.
    """
    return db.transaction()


def _traducir(error):
    """Convierte un error de psycopg en una excepcion propia y clara."""
    if isinstance(error, psycopg.errors.UniqueViolation):
        return ErrorUnico("Ya existe un registro con ese valor unico (por ej. email duplicado).")
    if isinstance(error, psycopg.errors.ForeignKeyViolation):
        return ErrorClaveForanea("El registro relacionado no existe o tiene datos asociados.")
    if isinstance(error, psycopg.errors.ExclusionViolation):
        return ErrorBaseDatos("Ese registro se solapa con otro (restriccion de exclusion).")
    if isinstance(error, psycopg.errors.CheckViolation):
        return ErrorBaseDatos("Un valor no cumple las reglas de la base de datos (CHECK).")
    if isinstance(error, psycopg.errors.NotNullViolation):
        return ErrorBaseDatos("Falta un dato obligatorio (NOT NULL).")
    return ErrorBaseDatos(str(error))


def consultar(db, sql, parametros=None):
    """SELECT que devuelve TODAS las filas (lista de tuplas)."""
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    except psycopg.Error as error:
        raise _traducir(error) from error


def consultar_uno(db, sql, parametros=None):
    """SELECT que devuelve UNA fila (tupla) o None si no hay resultados."""
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()
    except psycopg.Error as error:
        raise _traducir(error) from error


def ejecutar(db, sql, parametros=None):
    """INSERT / UPDATE / DELETE. Devuelve la cantidad de filas afectadas."""
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.rowcount
    except psycopg.Error as error:
        raise _traducir(error) from error


def ejecutar_devolviendo(db, sql, parametros=None):
    """Como ejecutar(), pero para sentencias con RETURNING. Devuelve la fila."""
    try:
        with db.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchone()
    except psycopg.Error as error:
        raise _traducir(error) from error


def ejecutar_afectando(db, sql, parametros=None):
    """Como ejecutar(), pero si no afecto ninguna fila levanta ErrorNoEncontrado."""
    filas = ejecutar(db, sql, parametros)
    if filas == 0:
        raise ErrorNoEncontrado("No se encontro el registro para modificar o eliminar.")
    return filas
