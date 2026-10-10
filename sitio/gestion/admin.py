"""Configuracion del admin de Django.

En esta primera entrega la GUI es el propio admin. Los modelos de las TABLAS
permiten alta/baja/modificacion; los modelos de las VISTAS son de solo lectura.
"""

from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from . import services
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


class DetalleVentaInlineForm(forms.ModelForm):
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")

    class Meta:
        model = DetalleVenta
        fields = ("producto", "cantidad")


class DetalleVentaInlineFormSet(BaseInlineFormSet):
    """Valida stock, exige al menos un producto y fija el precio del momento."""

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        cantidades = {}
        for form in self.forms:
            datos = getattr(form, "cleaned_data", None)
            if not datos or datos.get("DELETE"):
                continue
            producto = datos.get("producto")
            cantidad = datos.get("cantidad")
            if producto is None or cantidad is None:
                continue
            if producto.id in cantidades:
                raise ValidationError(
                    "El producto '{}' esta repetido: borra la linea sobrante "
                    "y suma la cantidad.".format(producto.nombre)
                )
            cantidades[producto.id] = cantidad
            # El precio se congela: el del producto al momento de la venta.
            form.instance.precio_unitario = producto.precio

        if not cantidades:
            raise ValidationError("La venta debe tener al menos un producto.")

        for producto_id, cantidad in cantidades.items():
            producto = Producto.objects.get(pk=producto_id)
            if cantidad > producto.stock:
                raise ValidationError(
                    "No hay stock suficiente de '{}' (hay {}, se piden {}).".format(
                        producto.nombre, producto.stock, cantidad
                    )
                )


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    form = DetalleVentaInlineForm
    formset = DetalleVentaInlineFormSet
    extra = 1
    fields = ("producto", "cantidad")
    readonly_fields = ("precio_unitario",)

    # Las lineas solo se editan al CREAR la venta. Al modificar una venta ya
    # registrada quedan de solo lectura (si no, habria que reajustar el stock).
    def has_add_permission(self, request, obj=None):
        return obj is None

    def has_change_permission(self, request, obj=None):
        return obj is None

    def has_delete_permission(self, request, obj=None):
        return obj is None


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

    def save_related(self, request, form, formsets, change):
        # Guarda cabecera + lineas y, si es una venta NUEVA, descuenta stock.
        super().save_related(request, form, formsets, change)
        if not change:
            services.registrar_stock_venta(form.instance)

    def delete_model(self, request, obj):
        # Anular: devuelve el stock y luego borra lineas + cabecera.
        services.devolver_stock_venta(obj)
        DetalleVenta.objects.filter(venta=obj).delete()
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            services.devolver_stock_venta(obj)
            DetalleVenta.objects.filter(venta=obj).delete()
        super().delete_queryset(request, queryset)


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
