"""Vistas de la interfaz visual (estilo Pinterest).

Solo lectura: muestran el catalogo de productos. Crear/editar se hace en el
admin de Django. No exponen clientes ni empleados.
"""

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Producto

# A partir de este stock mostramos el aviso "Stock bajo".
UMBRAL_STOCK_BAJO = 5


def _categorias():
    """Nombres de categoria distintos (los 'tableros')."""
    return (
        Producto.objects.values_list("categoria", flat=True)
        .distinct()
        .order_by("categoria")
    )


def catalogo(request):
    """Grilla de tarjetas con buscador y filtro por categoria."""
    q = (request.GET.get("q") or "").strip()
    categoria = (request.GET.get("categoria") or "").strip()

    productos = Producto.objects.select_related("proveedor").order_by("nombre")
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(categoria__icontains=q)
        )
    if categoria:
        productos = productos.filter(categoria__iexact=categoria)

    contexto = {
        "productos": productos,
        "categorias": _categorias(),
        "q": q,
        "categoria_activa": categoria,
        "umbral_stock_bajo": UMBRAL_STOCK_BAJO,
    }
    return render(request, "gestion/catalogo.html", contexto)


def detalle(request, pk):
    """Ficha del producto (el 'pin')."""
    producto = get_object_or_404(
        Producto.objects.select_related("proveedor"), pk=pk
    )
    contexto = {
        "producto": producto,
        "umbral_stock_bajo": UMBRAL_STOCK_BAJO,
    }
    return render(request, "gestion/producto_detalle.html", contexto)
