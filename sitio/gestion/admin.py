"""Configuracion del admin de Django.

En esta primera entrega la GUI es el propio admin. Los modelos de las TABLAS
permiten alta/baja/modificacion; los modelos de las VISTAS son de solo lectura.
"""

from django.contrib import admin

from .models import (
    Cliente,
    DetalleVenta,
    Empleado,
    Producto,
    Proveedor,
    ReporteStock,
    ReporteVenta,
    StockBajo,
    Venta,
)

admin.site.site_header = "API SQL-PY - Administracion"
admin.site.site_title = "API SQL-PY"
admin.site.index_title = "Gestion de la base practica_django"


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    fields = ("producto", "cantidad", "precio_unitario")


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "telefono", "email")
    search_fields = ("nombre", "email")
    ordering = ("id",)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "categoria", "precio", "stock", "proveedor")
    list_filter = ("categoria", "proveedor")
    search_fields = ("nombre", "categoria")
    list_select_related = ("proveedor",)
    ordering = ("id",)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "telefono", "email")
    search_fields = ("nombre", "email")
    ordering = ("id",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "puesto", "salario", "email")
    list_filter = ("puesto",)
    search_fields = ("nombre", "apellido", "email")
    ordering = ("id",)


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha", "cliente", "empleado")
    list_filter = ("fecha",)
    search_fields = ("cliente__nombre", "empleado__nombre", "empleado__apellido")
    list_select_related = ("cliente", "empleado")
    date_hierarchy = "fecha"
    inlines = (DetalleVentaInline,)
    ordering = ("-fecha", "-id")

    # El admin NO aplica las reglas de negocio (descontar stock, sumar
    # cantidades): eso vive en el CLI. Advertimos en el formulario.
    change_form_template = None


class VistaSoloLecturaAdmin(admin.ModelAdmin):
    """Base para las vistas: se ven, pero no se editan."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ReporteStock)
class ReporteStockAdmin(VistaSoloLecturaAdmin):
    list_display = ("nombre", "proveedor", "precio", "stock", "estado", "valor_stock")
    search_fields = ("nombre", "proveedor")
    ordering = ("nombre",)


@admin.register(StockBajo)
class StockBajoAdmin(VistaSoloLecturaAdmin):
    list_display = ("nombre", "precio", "stock")
    ordering = ("stock",)


@admin.register(ReporteVenta)
class ReporteVentaAdmin(VistaSoloLecturaAdmin):
    list_display = (
        "venta_id",
        "fecha_de_la_venta",
        "nombre_del_cliente",
        "nombre_del_empleado",
        "cantidad_productos",
        "total_de_la_venta",
    )
    search_fields = ("nombre_del_cliente", "nombre_del_empleado")
    date_hierarchy = "fecha_de_la_venta"
    ordering = ("-fecha_de_la_venta", "-venta_id")
