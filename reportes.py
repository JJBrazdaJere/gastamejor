"""Reportes de SOLO LECTURA, apoyados en las vistas que ya tiene la base."""

from base_datos import consultar


def reporte_stock(db):
    """Productos con proveedor, estado de stock y valor (vista reporte_stock)."""
    return consultar(db, "SELECT * FROM reporte_stock ORDER BY nombre")


def stock_bajo(db):
    """Productos con stock <= 5 (vista stock_bajo)."""
    return consultar(db, "SELECT * FROM stock_bajo ORDER BY nombre")


def reporte_ventas(db):
    """Resumen de ventas con totales (vista reporte_ventas)."""
    return consultar(db, "SELECT * FROM reporte_ventas ORDER BY venta_id")
