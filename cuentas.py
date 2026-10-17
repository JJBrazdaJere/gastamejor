"""Logica de CUENTAS de usuario sobre la tabla `clientes`.

Un cliente pasa a tener CUENTA cuando tiene `usuario` + `password_hash`.
El email se verifica con un codigo; el telefono es opcional.

Este modulo NO imprime: devuelve datos o levanta excepciones de `errores`.
Hoy lo usa la API HTTP (`servidor.py`); podria usarlo tambien el menu de
consola o cualquier otra interfaz.
"""

import hmac
import re
from datetime import datetime, timedelta, timezone

import correo
from base_datos import (
    consultar_uno,
    ejecutar,
    ejecutar_afectando,
    ejecutar_devolviendo,
    transaccion,
)
from config import CODIGO_VIGENCIA_MIN, SESION_HORAS
from errores import ErrorNoEncontrado, ErrorValidacion
from seguridad import (
    generar_codigo,
    generar_token,
    hashear_password,
    validar_password,
    verificar_password,
)
from validaciones import (
    formatear_monto,
    validar_decimal,
    validar_email,
    validar_texto,
    validar_texto_opcional,
)

# Usuario: 3 a 30 caracteres, letras/numeros y . _ -
_USUARIO = re.compile(r"^[A-Za-z0-9._-]{3,30}$")

# Recuperacion de contrasena: segundos de espera entre pedidos de codigo y
# cantidad de intentos fallidos antes de invalidar el codigo pendiente.
RECUPERACION_ENFRIAMIENTO_SEG = 120
RECUPERACION_INTENTOS_MAX = 5

# Monedas soportadas (las mismas que ofrece la app).
MONEDAS_SOPORTADAS = {
    "ARS", "MXN", "USD", "EUR", "CLP", "COP", "PEN", "UYU", "BOB", "PYG", "BRL", "CRC", "DOP",
}

# Datos que se devuelven al usuario (nunca el hash de la contrasena).
_COLUMNAS = (
    "id, nombre, usuario, email, telefono, email_verificado, "
    "ingreso_fijo_mensual, moneda, password_hash, creado_en"
)


def _ahora():
    return datetime.now(timezone.utc)


def validar_usuario(usuario):
    if not usuario or not _USUARIO.match(str(usuario).strip()):
        raise ErrorValidacion(
            "El usuario debe tener entre 3 y 30 caracteres "
            "(letras, numeros, punto, guion o guion bajo)."
        )
    return str(usuario).strip()


def validar_moneda(moneda):
    codigo = validar_texto(moneda, "moneda").upper()
    if codigo not in MONEDAS_SOPORTADAS:
        raise ErrorValidacion("Moneda no soportada: {}.".format(moneda))
    return codigo


def _publico(fila):
    """Convierte una fila de la base en un diccionario (sin el hash)."""
    return {
        "id": fila[0],
        "nombre": fila[1],
        "usuario": fila[2],
        "email": fila[3],
        "telefono": fila[4],
        "email_verificado": bool(fila[5]),
        "ingreso_fijo_mensual": formatear_monto(fila[6] if fila[6] is not None else 0),
        "moneda": fila[7] or "ARS",
    }


# ---------------------------------------------------------------------------
# Registro y verificacion de email
# ---------------------------------------------------------------------------
def registrar(db, nombre, usuario, password, email, telefono=None):
    """Crea la cuenta. Devuelve los datos publicos + el codigo (solo en modo test).

    El codigo de verificacion se guarda en la cuenta y se envia por correo.
    En MODO TEST no se envia: se imprime y se devuelve en `codigo_test` para
    poder verificar sin servidor de correo.
    """
    nombre = validar_texto(nombre, "nombre")
    usuario = validar_usuario(usuario)
    email = validar_email(email)
    telefono = validar_texto_opcional(telefono)
    validar_password(password)

    codigo = generar_codigo()
    expira = _ahora() + timedelta(minutes=CODIGO_VIGENCIA_MIN)
    password_hash = hashear_password(password)

    with transaccion(db):
        fila = ejecutar_devolviendo(
            db,
            """
            INSERT INTO clientes
                (nombre, email, telefono, usuario, password_hash,
                 email_verificado, codigo_verificacion, codigo_expira)
            VALUES (%s, %s, %s, %s, %s, false, %s, %s)
            RETURNING id
            """,
            (nombre, email, telefono, usuario, password_hash, codigo, expira),
        )
    cliente_id = fila[0]
    enviado = correo.enviar_codigo_verificacion(email, codigo)
    return {
        "id": cliente_id,
        "usuario": usuario,
        "email": email,
        "email_verificado": False,
        "codigo_test": None if enviado else codigo,
    }


def verificar_email(db, email, codigo):
    """Marca el email como verificado si el codigo coincide y no vencio."""
    email = validar_email(email)
    codigo = validar_texto(codigo, "codigo")
    fila = consultar_uno(
        db,
        "SELECT id, email_verificado, codigo_verificacion, codigo_expira "
        "FROM clientes WHERE lower(email) = lower(%s)",
        (email,),
    )
    if not fila:
        raise ErrorNoEncontrado("No existe una cuenta con ese email.")
    cliente_id, ya_verificado, guardado, expira = fila
    if ya_verificado:
        return True
    if not guardado:
        raise ErrorValidacion("No hay un codigo pendiente. Pedi que te enviemos uno nuevo.")
    if expira is not None and expira < _ahora():
        raise ErrorValidacion("El codigo vencio. Pedi uno nuevo.")
    if not hmac.compare_digest(str(guardado), str(codigo)):
        raise ErrorValidacion("El codigo no es correcto.")

    with transaccion(db):
        ejecutar_afectando(
            db,
            "UPDATE clientes SET email_verificado = true, "
            "codigo_verificacion = NULL, codigo_expira = NULL WHERE id = %s",
            (cliente_id,),
        )
    return True


def reenviar_codigo(db, email):
    """Genera y envia un codigo nuevo (si la cuenta no esta verificada)."""
    email = validar_email(email)
    fila = consultar_uno(
        db,
        "SELECT id, email_verificado FROM clientes WHERE lower(email) = lower(%s)",
        (email,),
    )
    if not fila:
        raise ErrorNoEncontrado("No existe una cuenta con ese email.")
    if fila[1]:
        raise ErrorValidacion("Esa cuenta ya esta verificada.")

    codigo = generar_codigo()
    expira = _ahora() + timedelta(minutes=CODIGO_VIGENCIA_MIN)
    with transaccion(db):
        ejecutar_afectando(
            db,
            "UPDATE clientes SET codigo_verificacion = %s, codigo_expira = %s WHERE id = %s",
            (codigo, expira, fila[0]),
        )
    enviado = correo.enviar_codigo_verificacion(email, codigo)
    return {"email": email, "codigo_test": None if enviado else codigo}


# ---------------------------------------------------------------------------
# Sesiones (login)
# ---------------------------------------------------------------------------
def iniciar_sesion(db, identificador, password):
    """Identificador = usuario O email. Devuelve el token de sesion."""
    identificador = validar_texto(identificador, "usuario o email")
    fila = consultar_uno(
        db,
        "SELECT " + _COLUMNAS + " FROM clientes "
        "WHERE lower(usuario) = lower(%s) OR lower(email) = lower(%s)",
        (identificador, identificador),
    )
    if not fila or not verificar_password(password, fila[8]):
        # Mismo mensaje para usuario inexistente y contrasena mal: no damos pistas.
        raise ErrorValidacion("Usuario o contrasena incorrectos.")
    if not fila[5]:
        raise ErrorValidacion(
            "Todavia no verificaste tu email. Revisa tu correo o pedi reenviar el codigo."
        )

    ahora = _ahora()
    expira = ahora + timedelta(hours=SESION_HORAS)
    token = generar_token()
    with transaccion(db):
        ejecutar(
            db,
            "INSERT INTO sesiones (token, cliente_id, expira_en) VALUES (%s, %s, %s)",
            (token, fila[0], expira),
        )
        # Limpieza: saca las sesiones vencidas de este usuario.
        ejecutar(
            db,
            "DELETE FROM sesiones WHERE cliente_id = %s AND expira_en < %s",
            (fila[0], ahora),
        )
    return {
        "token": token,
        "expira_en": expira.isoformat(),
        "cliente": _publico(fila),
    }


def cliente_por_token(db, token):
    """Devuelve el cliente de una sesion valida, o None si no sirve."""
    if not token:
        return None
    fila = consultar_uno(
        db,
        """
        SELECT c.id, c.nombre, c.usuario, c.email, c.telefono, c.email_verificado,
               c.ingreso_fijo_mensual, c.moneda, c.password_hash, c.creado_en, s.expira_en
        FROM sesiones s
        JOIN clientes c ON c.id = s.cliente_id
        WHERE s.token = %s
        """,
        (token,),
    )
    if not fila:
        return None
    if fila[10] is not None and fila[10] < _ahora():
        with transaccion(db):
            ejecutar(db, "DELETE FROM sesiones WHERE token = %s", (token,))
        return None
    return _publico(fila)


def cerrar_sesion(db, token):
    with transaccion(db):
        ejecutar(db, "DELETE FROM sesiones WHERE token = %s", (token,))
    return True


# ---------------------------------------------------------------------------
# Recuperacion de contrasena
# ---------------------------------------------------------------------------
def _limpiar_codigo_recuperacion(db, cliente_id):
    """Borra el codigo de recuperacion pendiente (vencido o agotado)."""
    with transaccion(db):
        ejecutar(
            db,
            "UPDATE clientes SET codigo_recuperacion = NULL, "
            "codigo_recuperacion_expira = NULL, codigo_recuperacion_intentos = 0 "
            "WHERE id = %s",
            (cliente_id,),
        )


def pedir_recuperacion(db, email):
    """Genera y envia un codigo para recuperar la contrasena.

    Nunca revela si el email existe: si la cuenta no esta, devuelve la misma
    respuesta generica (sin enviar correo). Solo se avisa si hay que esperar
    antes de pedir otro codigo.
    """
    email = validar_email(email)
    # El texto es siempre el mismo (exista o no la cuenta): asi nadie puede
    # averiguar que emails estan registrados.
    resultado = {
        "email": email,
        "codigo_test": None,
        "mensaje": (
            "Si existe una cuenta con ese email, te enviamos un código "
            "para recuperar la contraseña."
        ),
    }

    fila = consultar_uno(
        db,
        "SELECT id, ultimo_codigo_envio FROM clientes WHERE lower(email) = lower(%s)",
        (email,),
    )
    if not fila:
        return resultado

    cliente_id, ultimo_envio = fila
    if ultimo_envio is not None:
        transcurrido = (_ahora() - ultimo_envio).total_seconds()
        if transcurrido < RECUPERACION_ENFRIAMIENTO_SEG:
            raise ErrorValidacion(
                "Esperá unos minutos antes de pedir otro código para recuperar "
                "tu contraseña."
            )

    ahora = _ahora()
    codigo = generar_codigo()
    expira = ahora + timedelta(minutes=CODIGO_VIGENCIA_MIN)
    with transaccion(db):
        ejecutar_afectando(
            db,
            """
            UPDATE clientes
            SET codigo_recuperacion = %s, codigo_recuperacion_expira = %s,
                codigo_recuperacion_intentos = 0, ultimo_codigo_envio = %s
            WHERE id = %s
            """,
            (codigo, expira, ahora, cliente_id),
        )
    enviado = correo.enviar_codigo_recuperacion(email, codigo)
    resultado["codigo_test"] = None if enviado else codigo
    return resultado


def restablecer_password(db, email, codigo, nueva):
    """Cambia la contrasena con un codigo de recuperacion valido.

    Borra las sesiones abiertas (nadie sigue adentro con la contrasena vieja)
    y devuelve una sesion nueva, para que el usuario entre directo.
    """
    email = validar_email(email)
    codigo = validar_texto(codigo, "codigo")
    fila = consultar_uno(
        db,
        """
        SELECT id, nombre, usuario, email, telefono, email_verificado,
               ingreso_fijo_mensual, moneda, password_hash, creado_en,
               codigo_recuperacion, codigo_recuperacion_expira,
               codigo_recuperacion_intentos
        FROM clientes WHERE lower(email) = lower(%s)
        """,
        (email,),
    )
    # Acá SI se puede avisar: ya pasó el paso donde se pidió el código.
    if not fila:
        raise ErrorNoEncontrado("No existe una cuenta con ese email.")

    cliente_id = fila[0]
    guardado = fila[10]
    expira = fila[11]
    intentos = fila[12] or 0

    if not guardado:
        raise ErrorValidacion("No hay un código pendiente. Pedí uno nuevo.")
    if expira is not None and expira < _ahora():
        _limpiar_codigo_recuperacion(db, cliente_id)
        raise ErrorValidacion("El código venció. Pedí uno nuevo.")
    if intentos >= RECUPERACION_INTENTOS_MAX:
        _limpiar_codigo_recuperacion(db, cliente_id)
        raise ErrorValidacion("Demasiados intentos fallidos. Pedí un código nuevo.")
    if not hmac.compare_digest(str(guardado), str(codigo)):
        with transaccion(db):
            ejecutar_afectando(
                db,
                "UPDATE clientes SET codigo_recuperacion_intentos = "
                "codigo_recuperacion_intentos + 1 WHERE id = %s",
                (cliente_id,),
            )
        raise ErrorValidacion("El código no es correcto.")

    validar_password(nueva)
    password_hash = hashear_password(nueva)
    expira_sesion = _ahora() + timedelta(hours=SESION_HORAS)
    token = generar_token()
    with transaccion(db):
        ejecutar_afectando(
            db,
            """
            UPDATE clientes
            SET password_hash = %s, codigo_recuperacion = NULL,
                codigo_recuperacion_expira = NULL, codigo_recuperacion_intentos = 0
            WHERE id = %s
            """,
            (password_hash, cliente_id),
        )
        # Las sesiones viejas dejan de servir: la contrasena cambio.
        ejecutar(db, "DELETE FROM sesiones WHERE cliente_id = %s", (cliente_id,))
        ejecutar(
            db,
            "INSERT INTO sesiones (token, cliente_id, expira_en) VALUES (%s, %s, %s)",
            (token, cliente_id, expira_sesion),
        )

    try:
        correo.enviar_aviso_nueva_password(email)
    except Exception:  # noqa: BLE001 - la contrasena ya cambio; el aviso no es critico
        pass

    return {
        "token": token,
        "expira_en": expira_sesion.isoformat(),
        "cliente": _publico(fila),
    }


# ---------------------------------------------------------------------------
# Perfil
# ---------------------------------------------------------------------------
def obtener_por_id(db, cliente_id):
    fila = consultar_uno(
        db, "SELECT " + _COLUMNAS + " FROM clientes WHERE id = %s", (cliente_id,)
    )
    return _publico(fila) if fila else None


def actualizar_perfil(db, cliente_id, telefono=None, ingreso_fijo_mensual=None, moneda=None):
    """Actualiza solo los campos enviados (None = no tocar)."""
    campos = []
    valores = []
    if telefono is not None:
        campos.append("telefono = %s")
        valores.append(validar_texto_opcional(telefono))
    if ingreso_fijo_mensual is not None:
        monto = validar_decimal(ingreso_fijo_mensual, "ingreso fijo mensual", minimo=0)
        campos.append("ingreso_fijo_mensual = %s")
        valores.append(monto)
    if moneda is not None:
        campos.append("moneda = %s")
        valores.append(validar_moneda(moneda))
    if not campos:
        raise ErrorValidacion("No hay nada para actualizar.")

    valores.append(cliente_id)
    with transaccion(db):
        ejecutar_afectando(
            db, "UPDATE clientes SET " + ", ".join(campos) + " WHERE id = %s", tuple(valores)
        )
    return obtener_por_id(db, cliente_id)


def cambiar_password(db, cliente_id, actual, nueva):
    fila = consultar_uno(db, "SELECT email, password_hash FROM clientes WHERE id = %s", (cliente_id,))
    if not fila:
        raise ErrorNoEncontrado("Cuenta no encontrada.")
    if not verificar_password(actual, fila[1]):
        raise ErrorValidacion("La contrasena actual no es correcta.")
    validar_password(nueva)
    nuevo_hash = hashear_password(nueva)
    with transaccion(db):
        ejecutar_afectando(
            db, "UPDATE clientes SET password_hash = %s WHERE id = %s", (nuevo_hash, cliente_id)
        )
    correo.enviar_aviso_nueva_password(fila[0])
    return True


# ---------------------------------------------------------------------------
# Eliminar cuenta
# ---------------------------------------------------------------------------
def eliminar_cuenta(db, cliente_id, password):
    """Borra la cuenta del usuario (y, en cascada, sus ingresos y sesiones).

    Exige la contrasena actual para evitar borrados accidentales. Devuelve True.
    """
    fila = consultar_uno(
        db, "SELECT password_hash FROM clientes WHERE id = %s", (cliente_id,)
    )
    if not fila:
        raise ErrorNoEncontrado("Cuenta no encontrada.")
    if not verificar_password(password, fila[0]):
        raise ErrorValidacion("La contrasena no es correcta.")
    # Un solo DELETE: las tablas que dependen de `clientes` (ingresos y
    # sesiones) se declaran con ON DELETE CASCADE, asi que la base las limpia
    # sola (ver migrations/005_ingresos.sql y 006_sesiones.sql). Antes habia
    # borrados "a mano" de tablas que no existen (historial, ingresos_diarios):
    # el primer error de PostgreSQL abortaba la transaccion y no se borraba
    # nada. No se toleran errores de SQL con try/except: si algo falla, la
    # transaccion revierte y el error se informa.
    with transaccion(db):
        ejecutar_afectando(db, "DELETE FROM clientes WHERE id = %s", (cliente_id,))
    return True
