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

# SSL de la conexión (necesario en Postgres en la nube, ej. Neon: "require").
_PGSSLMODE = os.environ.get("PGSSLMODE")
if _PGSSLMODE:
    DB_CONFIG["sslmode"] = _PGSSLMODE

# Variables que NO tienen valor por defecto: si faltan, no se puede conectar.
_VARIABLES_OBLIGATORIAS = ("dbname", "user", "password")


def variables_faltantes():
    """Devuelve la lista de datos obligatorios que faltan en el .env."""
    return [nombre for nombre in _VARIABLES_OBLIGATORIAS if not DB_CONFIG.get(nombre)]


# --- Correo (verificacion de email) ---
# CORREO_MODO="test" NO envia: imprime el codigo (ideal para probar).
# CORREO_MODO="smtp" envia de verdad con los datos SMTP de abajo.
CORREO_MODO = os.environ.get("CORREO_MODO", "test").strip().lower()

CORREO_CONFIG = {
    "host": os.environ.get("SMTP_HOST", ""),
    "port": int(os.environ.get("SMTP_PORT", "587")),
    "usuario": os.environ.get("SMTP_USER", ""),
    "password": os.environ.get("SMTP_PASSWORD", ""),
    "remitente": os.environ.get("SMTP_FROM", "") or os.environ.get("SMTP_USER", ""),
    "tls": os.environ.get("SMTP_TLS", "1") == "1",
}

# API HTTP de Brevo (CORREO_MODO="api"): envía por HTTPS (443), sin depender
# del puerto SMTP. Es la opción robusta en hostings que bloquean SMTP (Render).
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_API_URL = os.environ.get("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")


# --- API HTTP ---
API_HOST = os.environ.get("API_HOST", "127.0.0.1")
# Puerto: API_PUERTO o, si no está, PORT (lo define el hosting, ej. Render).
API_PUERTO = int(os.environ.get("API_PUERTO") or os.environ.get("PORT", "8000"))
# Origenes permitidos por CORS (separados por coma). "*" = cualquiera (dev).
API_ORIGENES = [o.strip() for o in os.environ.get("API_ORIGENES", "*").split(",") if o.strip()]

# --- Sesiones / verificacion ---
# Horas que dura una sesion iniciada (30 dias por defecto).
SESION_HORAS = int(os.environ.get("SESION_HORAS", "720"))
# Minutos de vigencia del codigo de verificacion de email.
CODIGO_VIGENCIA_MIN = int(os.environ.get("CODIGO_VIGENCIA_MIN", "15"))
