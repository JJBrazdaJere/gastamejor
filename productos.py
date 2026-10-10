from base_datos import commit_db, leer_db

def obtener_producto(db, num):
    return leer_db(db,"SELECT nombre, precio, stock FROM productos WHERE id = %s",(num,))

def mostrar_producto(db, num):
    producto = obtener_producto(db, num)
    if producto:
        for nombre, precio, stock in producto:
            print('Nombre:',nombre ,'$',precio,'Stock: ',stock)
    else:
        print('Producto no Encontrado')

def agregar_producto(db, nombre, categoria, precio, stock, proveedor_id):
    valido=0
    if validar_stock (stock):
        valido +=1
    if validar_nombre(nombre):
        valido +=1
    if validar_precio(precio):
        valido +=1
    if validar_categoria(categoria):
        valido +=1
    if valido == 4:
        return commit_db(db,("INSERT INTO productos (nombre, categoria, precio, stock, proveedor_id) VALUES (%s, %s, %s, %s, %s) RETURNING id;"),(nombre, categoria, precio, stock, proveedor_id), True)

def actualizar_stock(db,producto_id, nuevo_stock):
    if validar_stock(nuevo_stock):
        resultado = commit_db(db,"UPDATE productos SET stock =%s WHERE id= %s",(nuevo_stock,producto_id))
        if resultado:
            print('Stock actualizado correctamente')
        else:
            print('Producto no encontrado')

def eliminar_producto(db,producto_id):
    resultado = commit_db(db,"DELETE FROM productos WHERE id= %s",(producto_id,))
    if resultado:
        print('Producto eliminado correctamente')
    else:
        print('Producto no encontrado')
     
def validar_stock(stock):
    if stock < 0:
        print('El stock no puede ser negativo!.')
        return False
    return True
def validar_nombre(nombre):
    nombre_aux = nombre.strip()
    if not nombre_aux:
        print('El nombre no puede estar vacio!. ')
        return False
    return True
def validar_precio(precio):
    if precio > 0.0:
        return True
    print('El precio no puede ser negativo!.')
    return False
def validar_categoria(categoria):
    categoria_aux = categoria.strip()
    if not categoria_aux:
        print('La categoria no puede estar vacio!.')
        return False
    return True
