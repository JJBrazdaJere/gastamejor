"""Punto de entrada del sistema de gestion.

Muestra un menu, lee la opcion del usuario y llama a las funciones de los
modulos de dominio (productos y proveedores). Las credenciales se leen del
archivo ".env" a traves de config.DB_CONFIG (no estan en el codigo).

Para agregar un modulo nuevo (clientes, empleados, ventas...):
  1. Crear el archivo del modulo (ej: clientes.py).
  2. Importar sus funciones arriba.
  3. Agregar una opcion al menu principal y una funcion menu_<entidad>().

Nota: los textos que se imprimen van sin acentos a proposito, porque la
consola de Windows (cp850) no los muestra bien.
"""

import sys

from config import DB_CONFIG, variables_faltantes
from conexion import conectar_db
from productos import (
    agregar_producto,
    actualizar_producto,
    actualizar_stock,
    eliminar_producto,
    mostrar_producto,
    mostrar_productos,
)
from proveedores import (
    agregar_proveedor,
    actualizar_proveedor,
    eliminar_proveedor,
    mostrar_proveedor,
)


# ---------------------------------------------------------------------------
# Ayudas para leer datos del usuario de forma segura
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
            return float(valor)
        except ValueError:
            print("Ingresa un numero valido (ej: 1234.50).")


def pedir_texto(mensaje):
    return input(mensaje).strip()


# ---------------------------------------------------------------------------
# Menu de PRODUCTOS
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
            mostrar_productos(db)
        elif opcion == 2:
            mostrar_producto(db, pedir_entero("ID del producto: "))
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            categoria = pedir_texto("Categoria: ")
            precio = pedir_decimal("Precio: ")
            stock = pedir_entero("Stock: ")
            proveedor_id = pedir_entero("ID del proveedor: ")
            nuevo = agregar_producto(db, nombre, categoria, precio, stock, proveedor_id)
            if nuevo:
                print("Producto agregado con ID", nuevo[0])
        elif opcion == 4:
            producto_id = pedir_entero("ID del producto: ")
            nuevo_stock = pedir_entero("Nuevo stock: ")
            actualizar_stock(db, producto_id, nuevo_stock)
        elif opcion == 5:
            producto_id = pedir_entero("ID del producto: ")
            print("Que dato queres cambiar? 1) Nombre  2) Categoria  3) Precio")
            dato = pedir_entero("Opcion: ")
            if dato == 3:
                valor = pedir_decimal("Nuevo precio: ")
            elif dato in (1, 2):
                valor = pedir_texto("Nuevo valor: ")
            else:
                print("Opcion invalida.")
                continue
            actualizar_producto(db, producto_id, valor, dato)
        elif opcion == 6:
            eliminar_producto(db, pedir_entero("ID del producto: "))
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


# ---------------------------------------------------------------------------
# Menu de PROVEEDORES
# ---------------------------------------------------------------------------
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
            mostrar_proveedor(db)
        elif opcion == 2:
            mostrar_proveedor(db, pedir_entero("ID del proveedor: "))
        elif opcion == 3:
            nombre = pedir_texto("Nombre: ")
            email = pedir_texto("Email: ")
            telefono = pedir_texto("Telefono: ")
            nuevo = agregar_proveedor(db, nombre, email, telefono)
            if nuevo:
                print("Proveedor agregado con ID", nuevo[0])
        elif opcion == 4:
            proveedor_id = pedir_entero("ID del proveedor: ")
            print("Que dato queres cambiar? 1) Nombre  2) Telefono  3) Email")
            dato = pedir_entero("Opcion: ")
            valor = pedir_texto("Nuevo valor: ")
            actualizar_proveedor(db, proveedor_id, valor, dato)
        elif opcion == 5:
            eliminar_proveedor(db, pedir_entero("ID del proveedor: "))
        elif opcion == 0:
            return
        else:
            print("Opcion invalida.")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
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
            print("0) Salir")
            opcion = pedir_entero("Opcion: ")

            if opcion == 1:
                menu_productos(mi_db)
            elif opcion == 2:
                menu_proveedores(mi_db)
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
