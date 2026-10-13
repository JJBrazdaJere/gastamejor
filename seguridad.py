"""Seguridad: contrasenas, tokens de sesion y codigos de verificacion.

No imprime ni toca la base: solo transforma/verifica valores y genera
cadenas aleatorias. Asi el resto del sistema no necesita saber COMO se
guardan las contrasenas (hoy: scrypt + sal aleatoria por usuario).
"""

import hashlib
import hmac
import secrets

from errores import ErrorValidacion

# Parametros de scrypt. N=2**14 usa ~16 MB de memoria por hash: suficiente
# para el uso real y rapido para los tests.
_ALGORITMO = "scrypt"
_N = 2 ** 14
_R = 8
_P = 1
_LARGO_HASH = 32
_LARGO_SAL = 16

# Largo minimo de contrasena.
LARGO_MINIMO_PASSWORD = 8


def validar_password(password):
    """Valida la contrasena y la devuelve tal cual (sin normalizar)."""
    if not isinstance(password, str) or len(password) < LARGO_MINIMO_PASSWORD:
        raise ErrorValidacion(
            "La contrasena debe tener al menos {} caracteres.".format(LARGO_MINIMO_PASSWORD)
        )
    return password


def hashear_password(password):
    """Devuelve un texto con sal + parametros + hash, todo en un solo campo.

    Formato: scrypt$N$r$p$sal_hex$hash_hex
    """
    validar_password(password)
    sal = secrets.token_bytes(_LARGO_SAL)
    derivado = hashlib.scrypt(
        password.encode("utf-8"), salt=sal, n=_N, r=_R, p=_P, dklen=_LARGO_HASH
    )
    return "{}${}${}${}${}${}".format(
        _ALGORITMO, _N, _R, _P, sal.hex(), derivado.hex()
    )


def verificar_password(password, almacenado):
    """Compara una contrasena con el hash guardado. Nunca levanta: True/False.

    La comparacion usa hmac.compare_digest para no filtrar informacion por el
    tiempo que tarda en fallar.
    """
    if not isinstance(password, str) or not almacenado:
        return False
    try:
        algoritmo, n, r, p, sal_hex, hash_hex = str(almacenado).split("$")
        if algoritmo != _ALGORITMO:
            return False
        sal = bytes.fromhex(sal_hex)
        esperado = bytes.fromhex(hash_hex)
        derivado = hashlib.scrypt(
            password.encode("utf-8"), salt=sal, n=int(n), r=int(r), p=int(p),
            dklen=len(esperado),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(derivado, esperado)


def generar_token():
    """Token de sesion: 256 bits en base64 url-safe (imposible de adivinar)."""
    return secrets.token_urlsafe(32)


def generar_codigo(largo=6):
    """Codigo numerico de verificacion, con el generador criptografico."""
    return "".join(secrets.choice("0123456789") for _ in range(largo))
