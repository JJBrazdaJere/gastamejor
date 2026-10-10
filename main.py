"""Punto de entrada del sistema de gestion (menu de consola).

Este archivo SOLO se ocupa de la interaccion con el usuario: pedir datos,
mostrar resultados y avisar de los errores. La logica de negocio vive en los
modulos de dominio (productos, proveedores, clientes, empleados, ventas,
reportes), que devuelven datos o levantan excepciones de `errores`.

Esa separacion es lo que permitira reutilizar la logica en una futura
interfaz grafica o web (Django) sin reescribirla.

Nota: los textos que se imprimen van sin acentos a proposito.
"""

import sys
from decimal import Decimal, InvalidOperation

# Fuerza salida/entrada en UTF-8 para que los acentos de los DATOS se vean bien.
for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

from config import DB_CONFIG, variables_faltantes
from conexion import conectar_db
from errores import ErrorAplicacion
from clientes import (
    actualizar_cliente,
    agregar_cliente,
    eliminar_cliente,
    listar_clientes,
    obtener_cliente,
)
from empleados import (
    actualizar_empleado,
    agregar_empleado,
    eliminar_empleado,
    listar_empleados,
    obtener_empleado,
)
from productos import (
    actualizar_producto,
    actualizar_stock,
    agregar_producto,
    eliminar_producto,
    listar_productos,
    obtener_producto,
)
from proveedores import (
    actualizar_proveedor,
    agregar_proveedor,
    eliminar_proveedor,
    listar_proveedores,
    obtener_proveedor,
)
from reportes import reporte_stock, reporte_ventas, stock_bajo
from ventas import agregar_venta, eliminar_venta, listar_ventas, obtener_venta


# ---------------------------------------------------------------------------
# Ayudas de entrada / salida
# ---------------------------------------------------------------------------
def pedir_entero(mensaje):
    while True:
        valor = input(mensaje).strip()
        try:
            return int(valor)
        except ValueError:
            print("Ingresa un numero entero valido.")


def pedir_decimal(mensaje):
    while True:
        valor = input(mensaje).strip().replace(",", ".")
        try:
            return Decimal(valor)
        except InvalidOperation:
            print("Ingresa un numero valido (ej: 1234.50).")


def pedir_texto(mensaje):
    return input(mensaje).strip()


def intentar(funcion, *args, **kwargs):
    """Ejecuta una operacion de dominio. Devuelve (ok, resultado).

    Si la operacion levanta un error de negocio, lo muestra y devuelve
    (False, None). Asi el resto del menu no se rompe.
    """
    try:
        return True, funcion(*args, **kwargs)
    except ErrorAplicacion as error:
        print("Aviso:", error)
        return False, None


def pedir_campo(opciones):
    """opciones: dict {'1': 'nombre', ...}. Devuelve el campo o None."""
    for clave, etiqueta in opciones.items():
        print(" {}) {}".format(clave, etiqueta))
    return opciones.get(pedir_texto("Opcion: "))


def pedir_lineas():
    """Carga de productos para una venta: [(producto_id, cantidad), ...]."""
    lineas = []
    print("Carga de productos (deja el ID vacio para terminar):")
    while True:
        entrada = input("  ID producto: ").strip()
        if not entrada:
            break
        try:
            producto_id = int(entrada)
        except ValueError:
            print("  ID invalido.")
            continue
        lineas.append((producto_id, pedir_entero("  Cantidad: ")))
    return lineas


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------
def menu_productos(db):
    while True:
        print("\n--- PRODUCTOS ---")
        print("1) Listar todos")
        print("2) Ver por ID")
        print("3) Agregar")
        print("4) Actualizar stock")
        print("5) Actualizar nombre / categoria / precio")
        print("6) Eliminar")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(listar_productos, db)
            if ok:
                if filas:
                    for p in filas:
                        print("id {} | {} | {} | ${} | stock {} | proveedor {}".format(*p))
                else:
                    print("No hay productos cargados.")
        elif opcion == 2:
            ok, p = intentar(obtener_producto, db, pedir_entero("ID del producto: "))
            if ok:
                if p:
                    print("id {} | {} | {} | ${} | stock {} | proveedor {}".format(*p))
                else:
                    print("Producto no encontrado.")
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            categoria = pedir_texto("Categoria: ")
            precio = pedir_decimal("Precio: ")
            stock = pedir_entero("Stock: ")
            proveedor_id = pedir_entero("ID del proveedor: ")
            ok, nuevo = intentar(agregar_producto, db, nombre, categoria, precio, stock, proveedor_id)
            if ok:
                print("Producto agregado con ID", nuevo)
        elif opcion == 4:
            producto_id = pedir_entero("ID del producto: ")
            ok, _ = intentar(actualizar_stock, db, producto_id, pedir_entero("Nuevo stock: "))
            if ok:
                print("Stock actualizado.")
        elif opcion == 5:
            producto_id = pedir_entero("ID del producto: ")
            campo = pedir_campo({"1": "nombre", "2": "categoria", "3": "precio"})
            if not campo:
                print("Opcion invalida.")
                continue
            if campo == "precio":
                valor = pedir_decimal("Nuevo precio: ")
            else:
                valor = pedir_texto("Nuevo valor: ")
            ok, _ = intentar(actualizar_producto, db, producto_id, campo, valor)
            if ok:
                print("Producto actualizado.")
        elif opcion == 6:
            ok, _ = intentar(eliminar_producto, db, pedir_entero("ID del producto: "))
            if ok:
                print("Producto eliminado.")
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def menu_proveedores(db):
    while True:
        print("\n--- PROVEEDORES ---")
        print("1) Listar todos")
        print("2) Ver por ID")
        print("3) Agregar")
        print("4) Actualizar nombre / telefono / email")
        print("5) Eliminar")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(listar_proveedores, db)
            if ok:
                if filas:
                    for f in filas:
                        print("id {} | {} | Tel: {} | {}".format(*f))
                else:
                    print("No hay proveedores cargados.")
        elif opcion == 2:
            ok, f = intentar(obtener_proveedor, db, pedir_entero("ID del proveedor: "))
            if ok:
                print("id {} | {} | Tel: {} | {}".format(*f) if f else "Proveedor no encontrado.")
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            email = pedir_texto("Email: ")
            telefono = pedir_texto("Telefono: ")
            ok, nuevo = intentar(agregar_proveedor, db, nombre, email, telefono)
            if ok:
                print("Proveedor agregado con ID", nuevo)
        elif opcion == 4:
            proveedor_id = pedir_entero("ID del proveedor: ")
            campo = pedir_campo({"1": "nombre", "2": "telefono", "3": "email"})
            if not campo:
                print("Opcion invalida.")
                continue
            ok, _ = intentar(actualizar_proveedor, db, proveedor_id, campo, pedir_texto("Nuevo valor: "))
            if ok:
                print("Proveedor actualizado.")
        elif opcion == 5:
            ok, _ = intentar(eliminar_proveedor, db, pedir_entero("ID del proveedor: "))
            if ok:
                print("Proveedor eliminado.")
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def menu_clientes(db):
    while True:
        print("\n--- CLIENTES ---")
        print("1) Listar todos")
        print("2) Ver por ID")
        print("3) Agregar")
        print("4) Actualizar nombre / telefono / email")
        print("5) Eliminar")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(listar_clientes, db)
            if ok:
                if filas:
                    for f in filas:
                        print("id {} | {} | Tel: {} | {}".format(*f))
                else:
                    print("No hay clientes cargados.")
        elif opcion == 2:
            ok, f = intentar(obtener_cliente, db, pedir_entero("ID del cliente: "))
            if ok:
                print("id {} | {} | Tel: {} | {}".format(*f) if f else "Cliente no encontrado.")
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            email = pedir_texto("Email: ")
            telefono = pedir_texto("Telefono (opcional): ")
            ok, nuevo = intentar(agregar_cliente, db, nombre, email, telefono or None)
            if ok:
                print("Cliente agregado con ID", nuevo)
        elif opcion == 4:
            cliente_id = pedir_entero("ID del cliente: ")
            campo = pedir_campo({"1": "nombre", "2": "telefono", "3": "email"})
            if not campo:
                print("Opcion invalida.")
                continue
            ok, _ = intentar(actualizar_cliente, db, cliente_id, campo, pedir_texto("Nuevo valor: "))
            if ok:
                print("Cliente actualizado.")
        elif opcion == 5:
            ok, _ = intentar(eliminar_cliente, db, pedir_entero("ID del cliente: "))
            if ok:
                print("Cliente eliminado.")
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def menu_empleados(db):
    while True:
        print("\n--- EMPLEADOS ---")
        print("1) Listar todos")
        print("2) Ver por ID")
        print("3) Agregar")
        print("4) Actualizar nombre / apellido / puesto / email / salario")
        print("5) Eliminar")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(listar_empleados, db)
            if ok:
                if filas:
                    for f in filas:
                        print("id {} | {} {} | {} | {} | ${}".format(*f))
                else:
                    print("No hay empleados cargados.")
        elif opcion == 2:
            ok, f = intentar(obtener_empleado, db, pedir_entero("ID del empleado: "))
            if ok:
                print("id {} | {} {} | {} | {} | ${}".format(*f) if f else "Empleado no encontrado.")
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            apellido = pedir_texto("Apellido: ")
            puesto = pedir_texto("Puesto: ")
            email = pedir_texto("Email: ")
            salario = pedir_decimal("Salario: ")
            ok, nuevo = intentar(agregar_empleado, db, nombre, apellido, puesto, email, salario)
            if ok:
                print("Empleado agregado con ID", nuevo)
        elif opcion == 4:
            empleado_id = pedir_entero("ID del empleado: ")
            campo = pedir_campo({
                "1": "nombre", "2": "apellido", "3": "puesto", "4": "email", "5": "salario",
            })
            if not campo:
                print("Opcion invalida.")
                continue
            if campo == "salario":
                valor = pedir_decimal("Nuevo salario: ")
            else:
                valor = pedir_texto("Nuevo valor: ")
            ok, _ = intentar(actualizar_empleado, db, empleado_id, campo, valor)
            if ok:
                print("Empleado actualizado.")
        elif opcion == 5:
            ok, _ = intentar(eliminar_empleado, db, pedir_entero("ID del empleado: "))
            if ok:
                print("Empleado eliminado.")
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def menu_ventas(db):
    while True:
        print("\n--- VENTAS ---")
        print("1) Listar ventas")
        print("2) Ver detalle por ID")
        print("3) Registrar venta")
        print("4) Anular venta (devuelve stock)")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(listar_ventas, db)
            if ok:
                if filas:
                    for venta_id, fecha, cliente, empleado, items, total in filas:
                        print("Venta {} | {} | Cliente: {} | Empleado: {} | items: {} | total: ${}".format(
                            venta_id, fecha, cliente, empleado, items, total))
                else:
                    print("No hay ventas registradas.")
        elif opcion == 2:
            ok, resultado = intentar(obtener_venta, db, pedir_entero("ID de la venta: "))
            if ok:
                if resultado is None:
                    print("Venta no encontrada.")
                else:
                    cabecera, lineas = resultado
                    print("Venta {} | Fecha: {} | Cliente: {} | Empleado: {}".format(*cabecera))
                    total = 0
                    for _, nombre, cantidad, precio, subtotal in lineas:
                        print("   {} x {} a ${} = {}".format(nombre, cantidad, precio, subtotal))
                        total += subtotal
                    print("   TOTAL: ${}".format(total))
        elif opcion == 3:
            cliente_id = pedir_entero("ID del cliente: ")
            empleado_id = pedir_entero("ID del empleado: ")
            lineas = pedir_lineas()
            if not lineas:
                print("No se cargaron productos; venta cancelada.")
                continue
            ok, venta_id = intentar(agregar_venta, db, cliente_id, empleado_id, lineas)
            if ok:
                print("Venta registrada con ID", venta_id)
        elif opcion == 4:
            ok, _ = intentar(eliminar_venta, db, pedir_entero("ID de la venta a anular: "))
            if ok:
                print("Venta anulada y stock devuelto.")
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def menu_reportes(db):
    while True:
        print("\n--- REPORTES (solo lectura) ---")
        print("1) Reporte de stock (con proveedor y valor)")
        print("2) Productos con stock bajo (<= 5)")
        print("3) Reporte de ventas")
        print("0) Volver")
        opcion = pedir_entero("Opcion: ")

        if opcion == 1:
            ok, filas = intentar(reporte_stock, db)
            if ok:
                print("nombre | proveedor | precio | stock | estado | valor_stock")
                for f in filas:
                    print(" | ".join(str(x) for x in f))
        elif opcion == 2:
            ok, filas = intentar(stock_bajo, db)
            if ok:
                for nombre, precio, stock in filas:
                    print("{} | ${} | stock {}".format(nombre, precio, stock))
        elif opcion == 3:
            ok, filas = intentar(reporte_ventas, db)
            if ok:
                for venta_id, fecha, cliente, empleado, items, total in filas:
                    print("Venta {} | {} | Cliente: {} | Empleado: {} | items: {} | total: ${}".format(
                        venta_id, fecha, cliente, empleado, items, total))
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


def main():
    faltantes = variables_faltantes()
    if faltantes:
        print("Faltan datos de conexion en el archivo .env:", ", ".join(faltantes))
        print("Copia .env.example a .env y completa los valores.")
        sys.exit(1)

    mi_db = conectar_db(**DB_CONFIG)
    print("Conectado a la base de datos:", DB_CONFIG["dbname"])

    try:
        while True:
            print("\n=== SISTEMA DE GESTION ===")
            print("1) Productos")
            print("2) Proveedores")
            print("3) Clientes")
            print("4) Empleados")
            print("5) Ventas")
            print("6) Reportes")
            print("0) Salir")
            opcion = pedir_entero("Opcion: ")

            if opcion == 1:
                menu_productos(mi_db)
            elif opcion == 2:
                menu_proveedores(mi_db)
            elif opcion == 3:
                menu_clientes(mi_db)
            elif opcion == 4:
                menu_empleados(mi_db)
            elif opcion == 5:
                menu_ventas(mi_db)
            elif opcion == 6:
                menu_reportes(mi_db)
            elif opcion == 0:
                print("Hasta luego.")
                break
            else:
                print("Opcion invalida.")
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
    finally:
        mi_db.close()
        print("Conexion cerrada.")


if __name__ == "__main__":
    main()
