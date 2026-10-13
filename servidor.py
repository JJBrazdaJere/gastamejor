"""Servidor HTTP (API JSON) para GastaMejor.

Usa solo la biblioteca estandar (`http.server`) + psycopg: no hay frameworks.

Endpoints (todos bajo /api):

    GET    /api/salud                     estado del servidor y la base
    POST   /api/registro                  {nombre, usuario, password, email, telefono?}
    POST   /api/verificar                 {email, codigo}
    POST   /api/reenviar                  {email}
    POST   /api/login                     {usuario, password}   -> {token, cliente}
    POST   /api/logout                    (auth)
    GET    /api/perfil                    (auth)
    PATCH  /api/perfil                    {telefono?, ingreso_fijo_mensual?, moneda?} (auth)
    POST   /api/password                  {actual, nueva} (auth)
    GET    /api/ingresos?mes=AAAA-MM      (auth)
    POST   /api/ingresos                  {monto, fecha?, descripcion?} (auth)
    DELETE /api/ingresos/{id}             (auth)
    GET    /api/resumen?mes=AAAA-MM       (auth)
    GET    /api/resumen/anual?anio=AAAA   (auth)

La autenticacion usa el encabezado:  Authorization: Bearer <token>

Ademas, si la ruta NO empieza con /api, sirve archivos de `frontend/` (comodo
para probar todo local en un solo servidor). El servidor NO reemplaza a
GitHub Pages: alli se sirve solo el frontend estatico.
"""

import argparse
import json
from datetime import date
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import cuentas
import ingresos
from config import (
    API_HOST,
    API_ORIGENES,
    API_PUERTO,
    DB_CONFIG,
    variables_faltantes,
)
from conexion import conectar_db
from errores import ErrorAplicacion, ErrorNoEncontrado, ErrorValidacion
from validaciones import formatear_monto

_FRONTEND = Path(__file__).resolve().parent / "frontend"

_TIPOS = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
    ".webmanifest": "application/manifest+json",
    ".txt": "text/plain; charset=utf-8",
}


def _json_ingreso(fila):
    """Fila (id, fecha, monto, descripcion) -> diccionario."""
    ingreso_id, fecha, monto, descripcion = fila
    return {
        "id": ingreso_id,
        "fecha": fecha.isoformat() if isinstance(fecha, date) else str(fecha),
        "monto": formatear_monto(monto),
        "descripcion": descripcion,
    }


def _json_cliente(cliente):
    return cliente


class Manejador(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "GastaMejorAPI/1.0"

    # ------------------------------------------------------------------ utils
    def log_message(self, formato, *args):
        # Log corto y sin ruido.
        print("{} - {}".format(self.address_string(), formato % args))

    def _cors(self):
        origen = self.headers.get("Origin", "")
        if "*" in API_ORIGENES or origen in API_ORIGENES:
            self.send_header("Access-Control-Allow-Origin", origen or "*")
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _responder(self, codigo, cuerpo=None, tipo="application/json; charset=utf-8"):
        datos = b""
        if cuerpo is not None:
            if isinstance(cuerpo, (dict, list)):
                datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
            elif isinstance(cuerpo, str):
                datos = cuerpo.encode("utf-8")
            else:
                datos = bytes(cuerpo)
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self._cors()
        self.end_headers()
        if datos and self.command != "HEAD":
            self.wfile.write(datos)

    def _json(self, codigo, cuerpo):
        self._responder(codigo, cuerpo)

    def _error(self, codigo, mensaje):
        self._responder(codigo, {"error": mensaje})

    def _leer_json(self):
        largo = int(self.headers.get("Content-Length") or 0)
        if largo <= 0:
            return {}
        crudo = self.rfile.read(largo)
        try:
            datos = json.loads(crudo.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ErrorValidacion("El cuerpo del pedido no es JSON valido.")
        if not isinstance(datos, dict):
            raise ErrorValidacion("El cuerpo del pedido debe ser un objeto JSON.")
        return datos

    def _token(self):
        cabecera = self.headers.get("Authorization", "")
        if cabecera.startswith("Bearer "):
            return cabecera[7:].strip()
        # Permite ?token=... (util para pruebas rapidas).
        return parse_qs(urlparse(self.path).query).get("token", [""])[0]

    # ------------------------------------------------------------- verbos
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_GET(self):
        self._despachar("GET")

    def do_POST(self):
        self._despachar("POST")

    def do_PATCH(self):
        self._despachar("PATCH")

    def do_DELETE(self):
        self._despachar("DELETE")

    # ------------------------------------------------------------- routing
    def _despachar(self, metodo):
        ruta = urlparse(self.path).path
        consulta = parse_qs(urlparse(self.path).query)
        try:
            if ruta == "/api" or ruta.startswith("/api/"):
                self._api(metodo, ruta, consulta)
            else:
                self._estatico(ruta)
        except ErrorValidacion as error:
            self._error(400, str(error))
        except ErrorNoEncontrado as error:
            self._error(404, str(error))
        except ErrorAplicacion as error:
            self._error(409, str(error))
        except Exception as error:  # noqa: BLE001 - ultima red de seguridad
            self.log_message("ERROR inesperado: %s", error)
            self._error(500, "Error interno del servidor.")

    def _conexion(self):
        return conectar_db(**DB_CONFIG)

    def _con_id(self):
        """Devuelve (db, cliente). Si no hay token valido, corta con 401."""
        db = self._conexion()
        cliente = cuentas.cliente_por_token(db, self._token())
        if cliente is None:
            db.close()
            self._error(401, "Sesion no valida. Inicia sesion de nuevo.")
            return None, None
        return db, cliente

    def _api(self, metodo, ruta, consulta):
        # --- Sin autenticacion ---
        if metodo == "GET" and ruta == "/api/salud":
            with self._conexion() as db:
                db.execute("SELECT 1")
            return self._json(200, {"ok": True, "db": True})

        if metodo == "POST" and ruta == "/api/registro":
            datos = self._leer_json()
            with self._conexion() as db:
                resultado = cuentas.registrar(
                    db,
                    datos.get("nombre"),
                    datos.get("usuario"),
                    datos.get("password"),
                    datos.get("email"),
                    datos.get("telefono"),
                )
            return self._json(201, resultado)

        if metodo == "POST" and ruta == "/api/verificar":
            datos = self._leer_json()
            with self._conexion() as db:
                cuentas.verificar_email(db, datos.get("email"), datos.get("codigo"))
            return self._json(200, {"ok": True, "mensaje": "Email verificado."})

        if metodo == "POST" and ruta == "/api/reenviar":
            datos = self._leer_json()
            with self._conexion() as db:
                resultado = cuentas.reenviar_codigo(db, datos.get("email"))
            return self._json(200, resultado)

        if metodo == "POST" and ruta == "/api/login":
            datos = self._leer_json()
            with self._conexion() as db:
                resultado = cuentas.iniciar_sesion(db, datos.get("usuario"), datos.get("password"))
            return self._json(200, resultado)

        # --- Con autenticacion ---
        if metodo == "POST" and ruta == "/api/logout":
            db, _ = self._con_id()
            if not db:
                return
            with db:
                cuentas.cerrar_sesion(db, self._token())
            return self._json(200, {"ok": True})

        if ruta == "/api/perfil" and metodo == "GET":
            db, cliente = self._con_id()
            if not db:
                return
            with db:
                return self._json(200, {"cliente": cliente})

        if ruta == "/api/perfil" and metodo == "PATCH":
            datos = self._leer_json()
            db, cliente = self._con_id()
            if not db:
                return
            with db:
                actualizado = cuentas.actualizar_perfil(
                    db,
                    cliente["id"],
                    telefono=datos.get("telefono"),
                    ingreso_fijo_mensual=datos.get("ingreso_fijo_mensual"),
                    moneda=datos.get("moneda"),
                )
            return self._json(200, {"cliente": actualizado})

        if ruta == "/api/password" and metodo == "POST":
            datos = self._leer_json()
            db, cliente = self._con_id()
            if not db:
                return
            with db:
                cuentas.cambiar_password(db, cliente["id"], datos.get("actual"), datos.get("nueva"))
            return self._json(200, {"ok": True, "mensaje": "Contrasena actualizada."})

        if ruta == "/api/ingresos" and metodo == "GET":
            db, cliente = self._con_id()
            if not db:
                return
            mes = consulta.get("mes", [None])[0]
            with db:
                filas = ingresos.listar(db, cliente["id"], mes)
            return self._json(200, {"ingresos": [_json_ingreso(f) for f in filas]})

        if ruta == "/api/ingresos" and metodo == "POST":
            datos = self._leer_json()
            db, cliente = self._con_id()
            if not db:
                return
            with db:
                nuevo = ingresos.agregar(
                    db,
                    cliente["id"],
                    datos.get("monto"),
                    datos.get("fecha"),
                    datos.get("descripcion"),
                )
            return self._json(201, {"id": nuevo})

        if ruta.startswith("/api/ingresos/") and metodo == "DELETE":
            ingreso_id = ruta.rsplit("/", 1)[-1]
            db, cliente = self._con_id()
            if not db:
                return
            with db:
                ingresos.eliminar(db, cliente["id"], ingreso_id)
            return self._json(200, {"ok": True})

        if ruta == "/api/resumen" and metodo == "GET":
            db, cliente = self._con_id()
            if not db:
                return
            mes = consulta.get("mes", [None])[0]
            with db:
                resumen = ingresos.resumen_mes(db, cliente["id"], mes)
            return self._json(200, resumen)

        if ruta == "/api/resumen/anual" and metodo == "GET":
            db, cliente = self._con_id()
            if not db:
                return
            anio = consulta.get("anio", [None])[0]
            with db:
                filas = ingresos.resumen_anual(db, cliente["id"], anio)
            return self._json(200, {"meses": filas})

        return self._error(404, "Ruta no encontrada: {} {}".format(metodo, ruta))

    # --------------------------------------------------------- archivos
    def _estatico(self, ruta):
        relativo = unquote(ruta).lstrip("/") or "index.html"
        destino = (_FRONTEND / relativo).resolve()
        # Evita salir de la carpeta frontend (../).
        if not str(destino).startswith(str(_FRONTEND.resolve())):
            return self._error(403, "Acceso denegado.")
        if destino.is_dir():
            destino = destino / "index.html"
        if not destino.is_file():
            return self._error(404, "No encontrado.")
        tipo = _TIPOS.get(destino.suffix.lower(), "application/octet-stream")
        self._responder(200, destino.read_bytes(), tipo=tipo)


def main():
    faltan = variables_faltantes()
    if faltan:
        print("Faltan datos de conexion en el .env:", ", ".join(faltan))
        print("Copia .env.example a .env y completa los valores.")
        return

    parser = argparse.ArgumentParser(description="API de GastaMejor")
    parser.add_argument("--host", default=API_HOST)
    parser.add_argument("--puerto", type=int, default=API_PUERTO)
    args = parser.parse_args()

    servidor = ThreadingHTTPServer((args.host, args.puerto), Manejador)
    print("GastaMejor API escuchando en http://{}:{}".format(args.host, args.puerto))
    print("Base de datos:", DB_CONFIG["dbname"])
    print("Prueba rapida: http://{}:{}/api/salud".format(args.host, args.puerto))
    print("Ctrl+C para cortar.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
