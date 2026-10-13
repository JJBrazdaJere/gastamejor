"""Validaciones reutilizables por todos los modulos.

Cada funcion valida y ADEMAS devuelve el valor ya normalizado (sin espacios,
convertido a numero, etc.). Si el dato es invalido levantan ErrorValidacion.
Esto evita repetir la misma logica en cada modulo.
"""

import re
from decimal import Decimal, InvalidOperation

from errores import ErrorValidacion

# Email simple: algo@algo.dominio (dominio de 2+ letras).
FORMATO_EMAIL = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')


def validar_email(email):
    if not email or not FORMATO_EMAIL.match(str(email).strip()):
        raise ErrorValidacion("El email '{}' no tiene un formato valido.".format(email))
    return str(email).strip()


def validar_texto(valor, campo):
    if valor is None or not str(valor).strip():
        raise ErrorValidacion("El campo '{}' no puede estar vacio.".format(campo))
    return str(valor).strip()


def validar_entero(valor, campo, minimo=None):
    # Ojo: int(1.5) en Python NO falla, trunca a 1. Eso sería peligroso para
    # stock o cantidades, así que exigimos que sea realmente un entero.
    if isinstance(valor, bool):
        raise ErrorValidacion("El campo '{}' debe ser un numero entero.".format(campo))
    if isinstance(valor, int):
        numero = valor
    else:
        texto = str(valor).strip()
        if not texto or not texto.lstrip("-").isdigit():
            raise ErrorValidacion("El campo '{}' debe ser un numero entero.".format(campo))
        numero = int(texto)
    if minimo is not None and numero < minimo:
        raise ErrorValidacion(
            "El campo '{}' no puede ser menor a {}.".format(campo, minimo)
        )
    return numero


def validar_decimal(valor, campo, minimo=None, mayor_a=None):
    # Usamos Decimal (no float) para no arrastrar errores de redondeo en
    # precios o salarios. Aceptamos coma como separador decimal.
    if isinstance(valor, bool):
        raise ErrorValidacion("El campo '{}' debe ser un numero.".format(campo))
    texto = str(valor).strip().replace(",", ".")
    try:
        numero = Decimal(texto)
    except (InvalidOperation, ValueError):
        raise ErrorValidacion("El campo '{}' debe ser un numero.".format(campo))
    if not numero.is_finite():
        raise ErrorValidacion("El campo '{}' debe ser un numero.".format(campo))
    if mayor_a is not None and numero <= Decimal(str(mayor_a)):
        raise ErrorValidacion("El campo '{}' debe ser mayor a {}.".format(campo, mayor_a))
    if minimo is not None and numero < Decimal(str(minimo)):
        raise ErrorValidacion("El campo '{}' no puede ser menor a {}.".format(campo, minimo))
    return numero


def validar_email_opcional(email):
    """Para tablas donde el email puede ser nulo/vacio (devuelve None)."""
    if email is None or not str(email).strip():
        return None
    return validar_email(email)


def validar_texto_opcional(valor):
    if valor is None or not str(valor).strip():
        return None
    return str(valor).strip()


def formatear_monto(valor):
    """Devuelve un monto como texto con 2 decimales (ej: '3500.50').

    Se usa para responder por la API: asi el dinero nunca viaja como float
    (que arrastra errores de redondeo) y siempre tiene el mismo formato.
    """
    return str(Decimal(str(valor)).quantize(Decimal("0.01")))
