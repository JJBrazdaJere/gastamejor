"""Modulo de CLIENTES. Sirve de plantilla para los modulos que faltan.

OJO: la tabla "clientes" (a diferencia de productos y proveedores) NO tiene
auto-incremento en el id. Por eso el id se genera con COALESCE(MAX(id),0)+1
dentro del mismo INSERT. Limitacion: no es 100% seguro si hubiera muchos
usuarios cargando a la vez; para produccion convendria una secuencia/IDENTITY.
"""

import re

from base_datos import commit_db, leer_db, estado_operacion

formato = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


def obtener_cliente(db, num):
    return leer_db(db, "SELECT id, nombre, telefono, email FROM clientes WHERE id = %s;", (num,))


def obtener_clientes(db):
    return leer_db(db, "SELECT id, nombre, telefono, email FROM clientes ORDER BY id;")


def mostrar_cliente(db, num=None):
    if num:
        cliente = obtener_cliente(db, num)
    else:
        cliente = obtener_clientes(db)
    if cliente:
        for id_cli, nombre, telefono, email in cliente:
            print('id', id_cli, 'Nombre:', nombre, 'Telefono: ', telefono, 'email: ', email)
    else:
        print('Cliente no Encontrado')


def agregar_cliente(db, nombre, email, telefono=None):
    valido = 0
    if validar_email(email):
        valido += 1
    else:
        print('Error Email')
    if validar_nombre(nombre):
        valido += 1
    else:
        print('Error nombre')
    if valido == 2:
        return commit_db(
            db,
            ("INSERT INTO clientes (id, nombre, telefono, email) "
             "SELECT COALESCE(MAX(id), 0) + 1, %s, %s, %s FROM clientes RETURNING id;"),
            (nombre, telefono, email),
            True,
        )


def _informar_actualizacion(resultado, campo):
    estado = estado_operacion(resultado)
    if estado == 'ok':
        print(campo, 'actualizado correctamente')
    elif estado == 'no_encontrado':
        print('Cliente no encontrado')
    # Si el estado es 'error', base_datos ya informo el detalle.


def actualizar_cliente(db, cliente_id, nuevo_dato, dato):
    # dato: 1 = nombre, 2 = telefono, 3 = email
    if dato == 1:
        if validar_nombre(nuevo_dato):
            _informar_actualizacion(commit_db(db, "UPDATE clientes SET nombre =%s WHERE id= %s", (nuevo_dato, cliente_id)), 'Nombre')
        else:
            print('Error nombre')
    elif dato == 2:
        _informar_actualizacion(commit_db(db, "UPDATE clientes SET telefono =%s WHERE id= %s", (nuevo_dato, cliente_id)), 'Telefono')
    elif dato == 3:
        if validar_email(nuevo_dato):
            _informar_actualizacion(commit_db(db, "UPDATE clientes SET email =%s WHERE id= %s", (nuevo_dato, cliente_id)), 'Email')
        else:
            print('Error email')
    else:
        print('las opciones son 1: Nombre 2: Telefono 3: Email')


def eliminar_cliente(db, cliente_id):
    resultado = commit_db(db, "DELETE FROM clientes WHERE id= %s", (cliente_id,))
    estado = estado_operacion(resultado)
    if estado == 'ok':
        print('Cliente eliminado correctamente')
    elif estado == 'no_encontrado':
        print('Cliente no encontrado')
    # Si el estado es 'error', base_datos ya informo el detalle.


def validar_email(email):
    if not email:
        return False
    return bool(formato.match(email))


def validar_nombre(nombre):
    nombre_aux = nombre.strip()
    if not nombre_aux:
        print('El nombre no puede estar vacio!. ')
        return False
    return True
