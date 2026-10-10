"""Logica de VENTAS. No imprime: devuelve datos o levanta excepciones.

Una venta = una cabecera en `ventas` + N lineas en `detalle_ventas`.
- Al registrar: se valida stock, se DESCUENTA stock y se guarda el precio
  del momento (precio_unitario). Todo en UNA transaccion: si algo falla,
  no queda nada a medias.
- Al anular: se DEVUELVE el stock y se borran lineas + cabecera.
- Si un producto se repite en la carga, se SUMAN las cantidades.
"""

from collections import OrderedDict

from base_datos import (
    consultar,
    consultar_uno,
    ejecutar,
    ejecutar_devolviendo,
    transaccion,
)
from errores import ErrorNoEncontrado, ErrorValidacion
from validaciones import validar_entero


def _normalizar_lineas(lineas):
    """Recibe [(producto_id, cantidad), ...] y suma las cantidades repetidas."""
    acumulado = OrderedDict()
    for producto_id, cantidad in lineas:
        producto_id = validar_entero(producto_id, "producto_id", minimo=1)
        cantidad = validar_entero(cantidad, "cantidad", minimo=1)
        acumulado[producto_id] = acumulado.get(producto_id, 0) + cantidad
    if not acumulado:
        raise ErrorValidacion("La venta debe tener al menos un producto.")
    return list(acumulado.items())


def listar_ventas(db):
    """Cabecera + cantidad de items + total (calculado con el precio guardado)."""
    return consultar(
        db,
        "SELECT v.id, v.fecha, c.nombre, e.nombre, "
        "       COALESCE(SUM(d.cantidad), 0), "
        "       COALESCE(SUM(d.cantidad * d.precio_unitario), 0) "
        "FROM ventas v "
        "JOIN clientes c ON c.id = v.cliente_id "
        "JOIN empleados e ON e.id = v.empleado_id "
        "LEFT JOIN detalle_ventas d ON d.venta_id = v.id "
        "GROUP BY v.id, v.fecha, c.nombre, e.nombre "
        "ORDER BY v.id",
    )


def obtener_venta(db, venta_id):
    """Devuelve (cabecera, lineas) o None si la venta no existe."""
    cabecera = consultar_uno(
        db,
        "SELECT v.id, v.fecha, c.nombre, e.nombre "
        "FROM ventas v "
        "JOIN clientes c ON c.id = v.cliente_id "
        "JOIN empleados e ON e.id = v.empleado_id "
        "WHERE v.id = %s",
        (venta_id,),
    )
    if cabecera is None:
        return None
    lineas = consultar(
        db,
        "SELECT d.producto_id, p.nombre, d.cantidad, d.precio_unitario, "
        "       (d.cantidad * d.precio_unitario) AS subtotal "
        "FROM detalle_ventas d "
        "JOIN productos p ON p.id = d.producto_id "
        "WHERE d.venta_id = %s ORDER BY p.nombre",
        (venta_id,),
    )
    return cabecera, lineas


def agregar_venta(db, cliente_id, empleado_id, lineas, fecha=None):
    """Registra una venta completa y devuelve su id. Todo o nada."""
    cliente_id = validar_entero(cliente_id, "cliente_id", minimo=1)
    empleado_id = validar_entero(empleado_id, "empleado_id", minimo=1)
    lineas = _normalizar_lineas(lineas)

    with transaccion(db):
        if consultar_uno(db, "SELECT 1 FROM clientes WHERE id = %s", (cliente_id,)) is None:
            raise ErrorNoEncontrado("El cliente {} no existe.".format(cliente_id))
        if consultar_uno(db, "SELECT 1 FROM empleados WHERE id = %s", (empleado_id,)) is None:
            raise ErrorNoEncontrado("El empleado {} no existe.".format(empleado_id))

        # 1) Cabecera. Si no se pasa fecha, la pone la base (CURRENT_DATE).
        if fecha is None:
            fila = ejecutar_devolviendo(
                db,
                "INSERT INTO ventas (cliente_id, empleado_id) VALUES (%s, %s) RETURNING id",
                (cliente_id, empleado_id),
            )
        else:
            fila = ejecutar_devolviendo(
                db,
                "INSERT INTO ventas (fecha, cliente_id, empleado_id) VALUES (%s, %s, %s) RETURNING id",
                (fecha, cliente_id, empleado_id),
            )
        venta_id = fila[0]

        # 2) Lineas. FOR UPDATE bloquea la fila del producto para leer el stock
        #    de forma consistente dentro de la transaccion.
        for producto_id, cantidad in lineas:
            producto = consultar_uno(
                db,
                "SELECT precio, stock FROM productos WHERE id = %s FOR UPDATE",
                (producto_id,),
            )
            if producto is None:
                raise ErrorNoEncontrado("El producto {} no existe.".format(producto_id))
            precio, stock = producto
            if stock < cantidad:
                raise ErrorValidacion(
                    "No hay stock suficiente del producto {} (hay {}, se piden {}).".format(
                        producto_id, stock, cantidad
                    )
                )
            ejecutar(
                db,
                "INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) "
                "VALUES (%s, %s, %s, %s)",
                (venta_id, producto_id, cantidad, precio),
            )
            ejecutar(
                db,
                "UPDATE productos SET stock = stock - %s WHERE id = %s",
                (cantidad, producto_id),
            )
    return venta_id


def eliminar_venta(db, venta_id):
    """Anula una venta: devuelve stock, borra lineas y cabecera (atomico)."""
    venta_id = validar_entero(venta_id, "venta_id", minimo=1)
    with transaccion(db):
        lineas = consultar(
            db,
            "SELECT producto_id, cantidad FROM detalle_ventas WHERE venta_id = %s FOR UPDATE",
            (venta_id,),
        )
        for producto_id, cantidad in lineas:
            ejecutar(
                db,
                "UPDATE productos SET stock = stock + %s WHERE id = %s",
                (cantidad, producto_id),
            )
        ejecutar(db, "DELETE FROM detalle_ventas WHERE venta_id = %s", (venta_id,))
        filas = ejecutar(db, "DELETE FROM ventas WHERE id = %s", (venta_id,))
        if filas == 0:
            raise ErrorNoEncontrado("La venta {} no existe.".format(venta_id))
