from base_datos import commit_db, leer_db, estado_operacion

def obtener_producto(db, num):
    return leer_db(db,"SELECT nombre, precio, stock FROM productos WHERE id = %s",(num,))

def mostrar_producto(db, num):
    producto = obtener_producto(db, num)
    if producto:
        for nombre, precio, stock in producto:
            print('Nombre:',nombre ,'$',precio,'Stock: ',stock)
    else:
        print('Producto no Encontrado')

def obtener_productos(db):
    return leer_db(db,"SELECT id, nombre, categoria, precio, stock, proveedor_id FROM productos ORDER BY id")

def mostrar_productos(db):
    productos = obtener_productos(db)
    if productos:
        for id_prod, nombre, categoria, precio, stock, proveedor_id in productos:
            print('id',id_prod,'| Nombre:',nombre,'| Categoria:',categoria,'| $',precio,'| Stock:',stock,'| Proveedor:',proveedor_id)
    else:
        print('No hay productos cargados.')

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

def _informar_actualizacion(resultado, campo):
    estado = estado_operacion(resultado)
    if estado == 'ok':
        print(campo, 'actualizado correctamente')
    elif estado == 'no_encontrado':
        print('Producto no encontrado')
    # Si el estado es 'error', base_datos ya informo el detalle.

def actualizar_stock(db,producto_id, nuevo_stock):
    if validar_stock(nuevo_stock):
        resultado = commit_db(db,"UPDATE productos SET stock =%s WHERE id= %s",(nuevo_stock,producto_id))
        _informar_actualizacion(resultado, 'Stock')

def actualizar_producto(db, producto_id, nuevo_dato, dato):
    # dato: 1 = nombre, 2 = categoria, 3 = precio
    if dato == 1:
        if validar_nombre(nuevo_dato):
            _informar_actualizacion(commit_db(db,"UPDATE productos SET nombre=%s WHERE id= %s",(nuevo_dato,producto_id)), 'Nombre')
        else:
            print('Error nombre')
    elif dato == 2:
        if validar_categoria(nuevo_dato):
            _informar_actualizacion(commit_db(db,"UPDATE productos SET categoria=%s WHERE id= %s",(nuevo_dato,producto_id)), 'Categoria')
        else:
            print('Error categoria')
    elif dato == 3:
        if validar_precio(nuevo_dato):
            _informar_actualizacion(commit_db(db,"UPDATE productos SET precio=%s WHERE id= %s",(nuevo_dato,producto_id)), 'Precio')
        else:
            print('Error precio')
    else:
        print('Las opciones son 1: Nombre 2: Categoria 3: Precio')

def eliminar_producto(db,producto_id):
    resultado = commit_db(db,"DELETE FROM productos WHERE id= %s",(producto_id,))
    estado = estado_operacion(resultado)
    if estado == 'ok':
        print('Producto eliminado correctamente')
    elif estado == 'no_encontrado':
        print('Producto no encontrado')
    # Si el estado es 'error', base_datos ya informo el detalle.
     
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
    print('El precio debe ser mayor a 0!.')
    return False
def validar_categoria(categoria):
    categoria_aux = categoria.strip()
    if not categoria_aux:
        print('La categoria no puede estar vacio!.')
        return False
    return True
