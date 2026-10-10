"""Configuración central del proyecto.

Lee el archivo ".env" (que NO se sube a Git) y expone los datos de
conexión en el diccionario DB_CONFIG. Así la contraseña queda fuera del
código y se cambia en un solo lugar.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Ruta absoluta al .env, junto a este archivo, para que funcione
# sin importar desde qué carpeta se ejecute el programa.
_RUTA_ENV = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_RUTA_ENV)

# Datos de conexión. "None" en dbname/user/password significa "obligatorio".
DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE"),
    "user": os.environ.get("PGUSER"),
    "password": os.environ.get("PGPASSWORD"),
}

# Variables que NO tienen valor por defecto: si faltan, no se puede conectar.
_VARIABLES_OBLIGATORIAS = ("dbname", "user", "password")


def variables_faltantes():
    """Devuelve la lista de datos obligatorios que faltan en el .env."""
    return [nombre for nombre in _VARIABLES_OBLIGATORIAS if not DB_CONFIG.get(nombre)]
