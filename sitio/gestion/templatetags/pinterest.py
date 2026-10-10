"""Filtros de plantilla para la interfaz estilo Pinterest.

Generan "arte" con CSS a partir del texto del producto, asi no dependemos de
imagenes ni de internet.
"""

import hashlib

from django import template

register = template.Library()


def _hash(valor):
    return int(hashlib.md5(str(valor).encode("utf-8")).hexdigest(), 16)


@register.filter
def gradiente(valor):
    """Degradado CSS estable (mismo producto -> mismo color)."""
    h = _hash(valor)
    tono = h % 360
    tono2 = (tono + 45) % 360
    return "linear-gradient(135deg, hsl({}, 72%, 62%), hsl({}, 78%, 46%))".format(
        tono, tono2
    )


@register.filter
def altura(valor):
    """Alto variable (px) para dar el efecto de mamposteria."""
    return 150 + (_hash(valor) % 4) * 40
