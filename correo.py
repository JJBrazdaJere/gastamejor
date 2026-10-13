"""Envio de correo electronico.

Por defecto funciona en MODO TEST (`CORREO_MODO=test`): en vez de mandar el
correo, imprime el contenido en la consola. Asi se puede probar la
verificacion sin configurar un servidor SMTP.

Con `CORREO_MODO=smtp` y los datos SMTP del `.env` envia de verdad.
Es la unica capa que "habla hacia afuera"; los modulos de dominio solo la
llaman (`correo.enviar_codigo_verificacion`).
"""

import smtplib
from email.message import EmailMessage

from config import CORREO_CONFIG, CORREO_MODO
from errores import ErrorAplicacion


def en_modo_test():
    return CORREO_MODO != "smtp"


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


def enviar_aviso_nueva_password(destino):
    """Aviso (sin contrasena) cuando se cambia la contrasena de la cuenta."""
    asunto = "GastaMejor: se cambio tu contrasena"
    cuerpo = (
        "Hola,\n\n"
        "La contrasena de tu cuenta de GastaMejor se cambio correctamente.\n"
        "Si no fuiste vos, responde a este correo (o usa \"Reportar\") cuanto antes.\n"
    )
    return enviar(destino, asunto, cuerpo)
