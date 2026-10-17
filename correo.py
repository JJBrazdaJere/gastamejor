"""Envio de correo electronico.

Por defecto funciona en MODO TEST (`CORREO_MODO=test`): en vez de mandar el
correo, imprime el contenido en la consola. Asi se puede probar la
verificacion sin configurar un servidor SMTP.

Hay dos modos de envio real:
- `CORREO_MODO=smtp`: con los datos SMTP del `.env` (sirve en local).
- `CORREO_MODO=api`: con la API HTTP de Brevo (`BREVO_API_KEY`). Sale por
  HTTPS (443), asi que funciona en hostings que bloquean los puertos SMTP
  (por ejemplo Render). Es la opcion recomendada al publicar.
Es la unica capa que "habla hacia afuera"; los modulos de dominio solo la
llaman (`correo.enviar_codigo_verificacion`).
"""

import json
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from config import BREVO_API_KEY, BREVO_API_URL, CORREO_CONFIG, CORREO_MODO
from errores import ErrorAplicacion


def en_modo_test():
    return CORREO_MODO not in ("smtp", "api")


def _separar_remitente(texto):
    """'Nombre <mail@x>' -> ('Nombre', 'mail@x'); 'mail@x' -> ('', 'mail@x')."""
    texto = (texto or "").strip()
    if "<" in texto and ">" in texto:
        nombre = texto[: texto.index("<")].strip().strip('"')
        correo = texto[texto.index("<") + 1 : texto.index(">")].strip()
        return nombre, correo
    return "", texto


def _enviar_con_api(destino, asunto, cuerpo):
    """Envia por la API HTTP de Brevo (HTTPS). No usa puertos SMTP."""
    if not BREVO_API_KEY:
        raise ErrorAplicacion("Falta BREVO_API_KEY en el .env para usar CORREO_MODO=api.")
    nombre, correo = _separar_remitente(CORREO_CONFIG["remitente"])
    if not correo:
        raise ErrorAplicacion("Falta el remitente (SMTP_FROM) para enviar el correo.")

    carga = {
        "sender": {"email": correo, "name": nombre or correo},
        "to": [{"email": destino}],
        "subject": asunto,
        "textContent": cuerpo,
    }
    peticion = urllib.request.Request(
        BREVO_API_URL,
        data=json.dumps(carga).encode("utf-8"),
        headers={
            "api-key": BREVO_API_KEY,
            "content-type": "application/json",
            "accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            respuesta.read()
    except urllib.error.HTTPError as error:
        detalle = error.read().decode("utf-8", "replace")[:300]
        raise ErrorAplicacion(
            "No se pudo enviar el correo (API Brevo {}): {}".format(error.code, detalle)
        ) from error
    except (urllib.error.URLError, OSError) as error:
        raise ErrorAplicacion("No se pudo enviar el correo (API Brevo): {}".format(error)) from error
    return True


def enviar(destino, asunto, cuerpo):
    """Envia un correo. En modo test solo lo imprime. Devuelve True si se envio.

    Lanza ErrorAplicacion si el envio real falla (para que el pedido HTTP
    pueda avisar en vez de quedar colgado).
    """
    if en_modo_test():
        print("")
        print("========== CORREO (modo test, NO se envio) ==========")
        print("Para:   {}".format(destino))
        print("Asunto: {}".format(asunto))
        print("-----------------------------------------------------")
        print(cuerpo)
        print("=====================================================")
        print("")
        return False

    if CORREO_MODO == "api":
        return _enviar_con_api(destino, asunto, cuerpo)

    if not CORREO_CONFIG.get("host") or not CORREO_CONFIG.get("remitente"):
        raise ErrorAplicacion(
            "El correo esta en modo SMTP pero faltan SMTP_HOST/SMTP_FROM en el .env."
        )

    mensaje = EmailMessage()
    mensaje["From"] = CORREO_CONFIG["remitente"]
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    try:
        with smtplib.SMTP(CORREO_CONFIG["host"], CORREO_CONFIG["port"], timeout=15) as smtp:
            if CORREO_CONFIG.get("tls"):
                smtp.starttls()
            if CORREO_CONFIG.get("usuario"):
                smtp.login(CORREO_CONFIG["usuario"], CORREO_CONFIG["password"])
            smtp.send_message(mensaje)
    except (OSError, smtplib.SMTPException) as error:
        raise ErrorAplicacion("No se pudo enviar el correo: {}".format(error)) from error
    return True


def enviar_codigo_verificacion(destino, codigo):
    """Correo con el codigo para verificar la cuenta."""
    asunto = "GastaMejor: verifica tu cuenta"
    cuerpo = (
        "Hola,\n\n"
        "Tu codigo de verificacion de GastaMejor es:\n\n"
        "    {}\n\n"
        "Vence en unos minutos. Si no te registraste, ignora este mensaje.\n"
    ).format(codigo)
    return enviar(destino, asunto, cuerpo)


def enviar_codigo_recuperacion(destino, codigo):
    """Correo con el codigo para recuperar la contrasena."""
    asunto = "GastaMejor: recuperar tu contraseña"
    cuerpo = (
        "Hola,\n\n"
        "Tu codigo para recuperar la contrasena de GastaMejor es:\n\n"
        "    {}\n\n"
        "Vence en unos minutos. Si no pediste recuperar tu contrasena, "
        "ignora este mensaje.\n"
    ).format(codigo)
    return enviar(destino, asunto, cuerpo)


def enviar_aviso_nueva_password(destino):
    """Aviso (sin contrasena) cuando se cambia la contrasena de la cuenta."""
    asunto = "GastaMejor: se cambio tu contrasena"
    cuerpo = (
        "Hola,\n\n"
        "La contrasena de tu cuenta de GastaMejor se cambio correctamente.\n"
        "Si no fuiste vos, responde a este correo (o usa \"Reportar\") cuanto antes.\n"
    )
    return enviar(destino, asunto, cuerpo)
