"""Modelos de Django (espejo de las tablas y vistas existentes).

IMPORTANTE:
El esquema real lo definen las migraciones SQL del proyecto (carpeta
``migrations/``) sobre la base ``practica_django``. Por eso TODOS los modelos
son ``managed = False``: Django los usa para leer/escribir y para el admin,
pero NUNCA crea ni altera estas tablas. La logica de negocio (ventas, stock)
sigue viviendo en los modulos SQL crudos del CLI.
"""

from datetime import date

from django.db import models


class Proveedor(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30)
    email = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = "proveedores"
        verbose_name = "proveedor"
        verbose_name_plural = "proveedores"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = "productos"
        verbose_name = "producto"
        verbose_name_plural = "productos"

    def __str__(self):
        return self.nombre


class Cliente(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    email = models.CharField(unique=True, max_length=100)

    class Meta:
        managed = False
        db_table = "clientes"
        verbose_name = "cliente"
        verbose_name_plural = "clientes"

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=50)
    puesto = models.CharField(max_length=30)
    email = models.CharField(unique=True, max_length=100)
    salario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "empleados"
        verbose_name = "empleado"
        verbose_name_plural = "empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Venta(models.Model):
    id = models.AutoField(primary_key=True)
    # La base tiene DEFAULT CURRENT_DATE; replicamos eso en el formulario.
    fecha = models.DateField(default=date.today)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT)

    class Meta:
        managed = False
        db_table = "ventas"
        verbose_name = "venta"
        verbose_name_plural = "ventas"

    def __str__(self):
        return f"Venta #{self.id} ({self.fecha})"


class DetalleVenta(models.Model):
    pk = models.CompositePrimaryKey("venta_id", "producto_id")
    venta = models.ForeignKey(Venta, on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = "detalle_ventas"
        verbose_name = "detalle de venta"
        verbose_name_plural = "detalles de venta"

    def __str__(self):
        return f"Venta #{self.venta_id} - {self.producto}"


# --------------------------------------------------------------------------
# Vistas de la base (solo lectura, para reportes en el admin).
# --------------------------------------------------------------------------


class ReporteStock(models.Model):
    nombre = models.CharField(max_length=100, primary_key=True)
    proveedor = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    estado = models.CharField(max_length=20)
    valor_stock = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = "reporte_stock"
        verbose_name = "reporte de stock"
        verbose_name_plural = "reportes de stock"


class StockBajo(models.Model):
    nombre = models.CharField(max_length=100, primary_key=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

    class Meta:
        managed = False
        db_table = "stock_bajo"
        verbose_name = "stock bajo"
        verbose_name_plural = "stock bajo"


class ReporteVenta(models.Model):
    venta_id = models.IntegerField(primary_key=True)
    fecha_de_la_venta = models.DateField()
    nombre_del_cliente = models.CharField(max_length=100)
    nombre_del_empleado = models.CharField(max_length=150)
    cantidad_productos = models.BigIntegerField()
    total_de_la_venta = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        managed = False
        db_table = "reporte_ventas"
        verbose_name = "reporte de ventas"
        verbose_name_plural = "reportes de ventas"
