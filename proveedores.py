import re
from base_datos import commit_db, leer_db

formato = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

def obtener_proveedor(db, num):
    return leer_db(db,"SELECT id, nombre, telefono, email FROM proveedores WHERE id = %s;",(num,))

def obtener_proveedores(db):
    return leer_db(db,'SELECT id, nombre, telefono, email FROM proveedores;')
    
def mostrar_proveedor(db, num = None):
    if num:
        proveedor = obtener_proveedor(db, num)
    else:
        proveedor = obtener_proveedores(db)
    if proveedor:
        for id_prov, nombre, telefono, email in proveedor:
            print('id',id_prov,'Nombre:',nombre ,'Telefono: ',telefono,'email: ',email)
    else:
        print('Proveedor no Encontrado')

def agregar_proveedor(db, nombre, email, telefono):
    valido=0
    if validar_email (email):
        valido +=1
    else:
        print('Error Email')
    if validar_nombre(nombre):
        valido+=1
    else:
        print('Error nombre')
    if telefono:
        valido +=1
    else:
        print('El telefono es obligatorio (la base lo exige NOT NULL).')
    if valido == 3:
        return commit_db(db,("INSERT INTO proveedores (nombre, telefono, email) VALUES (%s, %s, %s) RETURNING id;"),(nombre, telefono, email), True)#true para el returning ID

def actualizar_proveedor(db,proveedor_id,nuevo_dato,dato):
    if dato == 1:
        if validar_nombre(nuevo_dato):
            resultado = commit_db(db,"UPDATE proveedores SET nombre =%s WHERE id= %s",(nuevo_dato,proveedor_id))
            if resultado:
                print('Nombre actualizado correctamente')
            else:
                print('Proveedor no encontrado')
        else:
            print('Error nombre')
    elif dato == 2:
            resultado = commit_db(db,"UPDATE proveedores SET telefono =%s WHERE id= %s",(nuevo_dato,proveedor_id))
            if resultado:
                print('Telefono actualizado correctamente')
            else:
                print('Proveedor no encontrado')
    elif dato == 3:
            if validar_email(nuevo_dato):
                resultado = commit_db(db,"UPDATE proveedores SET email =%s WHERE id= %s",(nuevo_dato,proveedor_id))
                if resultado:
                    print('Email actualizado correctamente')
                else:
                    print('Proveedor no encontrado')
            else:
                print('Error email')
    else:
        print('las opciones son 1: Nombre 2: Telefono 3: Email')

def eliminar_proveedor(db,proveedor_id):
    resultado = commit_db(db,"DELETE FROM proveedores WHERE id= %s",(proveedor_id,))
    if resultado:
        print('Proveedor eliminado correctamente')
    else:
        print('Proveedor no encontrado')
     
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
