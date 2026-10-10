"""Reglas de negocio de ventas para la GUI (Django).

El CLI implementa estas mismas reglas con SQL crudo (``ventas.py``). Aca se
hacen con el ORM, dentro de ``transaction.atomic()`` (el admin ya envuelve el
guardado en una transaccion), para que la interfaz web tambien las aplique.
Ambas capas escriben en la MISMA base (``practica_django``).
"""

from django.core.exceptions import ValidationError
from django.db.models import F, Sum

from .models import DetalleVenta, Producto


def _totales_por_producto(venta):
    """Cantidad total vendida por producto en una venta."""
    return (
        DetalleVenta.objects.filter(venta=venta)
        .values("producto_id")
        .annotate(total=Sum("cantidad"))
    )


def registrar_stock_venta(venta):
    """Descuenta del stock lo vendido. Debe correr dentro de una transaccion.

    Bloquea cada producto (SELECT ... FOR UPDATE) para leer el stock de forma
    consistente y evitar que dos ventas simultaneas lo dejen en negativo.
    """
    for fila in _totales_por_producto(venta):
        producto = Producto.objects.select_for_update().get(pk=fila["producto_id"])
        if fila["total"] > producto.stock:
            raise ValidationError(
                "No hay stock suficiente de '{}' (hay {}, se piden {}).".format(
                    producto.nombre, producto.stock, fila["total"]
                )
            )
        producto.stock -= fila["total"]
        producto.save(update_fields=["stock"])


def devolver_stock_venta(venta):
    """Devuelve al stock lo que estaba vendido (anular una venta)."""
    for fila in _totales_por_producto(venta):
        Producto.objects.filter(pk=fila["producto_id"]).update(
            stock=F("stock") + fila["total"]
        )
