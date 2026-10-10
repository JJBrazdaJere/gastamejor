from conexion import conectar_db
from base_datos import leer_db, commit_db
from productos import obtener_producto, mostrar_producto, agregar_producto, eliminar_producto,actualizar_stock
from proveedores import obtener_proveedor, mostrar_proveedor, agregar_proveedor, eliminar_proveedor, actualizar_proveedor

mi_db = conectar_db("localhost",5432,"practica_sql","postgres","CLAVE-ELIMINADA")
