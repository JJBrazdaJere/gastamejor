"""Pruebas del servidor HTTP (`servidor.py`) que NO necesitan la base.

Levantan el manejador en un puerto libre y comprueban el comportamiento de la
capa HTTP: archivos estaticos, HEAD, rutas inexistentes y el 405 JSON para los
verbos sin manejador (antes `http.server` devolvia 501 en HTML).
"""

import http.client
import json
import threading

import pytest
from http.server import ThreadingHTTPServer

import servidor


@pytest.fixture(scope="module")
def puerto():
    """Servidor real en un puerto efimero, durante todo el modulo."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), servidor.Manejador)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        yield httpd.server_address[1]
    finally:
        httpd.shutdown()
        httpd.server_close()
        hilo.join(timeout=5)


def pedir(puerto, metodo, ruta):
    """Hace un pedido y devuelve (codigo, cabeceras, cuerpo_como_texto)."""
    conexion = http.client.HTTPConnection("127.0.0.1", puerto, timeout=5)
    try:
        conexion.request(metodo, ruta)
        respuesta = conexion.getresponse()
        cuerpo = respuesta.read().decode("utf-8", "replace")
        return respuesta.status, dict(respuesta.getheaders()), cuerpo
    finally:
        conexion.close()


def test_get_archivo_estatico(puerto):
    codigo, cabeceras, cuerpo = pedir(puerto, "GET", "/index.html")
    assert codigo == 200
    assert "text/html" in cabeceras["Content-Type"]
    assert "<html" in cuerpo.lower()


def test_head_responde_sin_cuerpo(puerto):
    codigo, cabeceras, cuerpo = pedir(puerto, "HEAD", "/index.html")
    assert codigo == 200
    assert cuerpo == ""
    # Content-Length se mantiene aunque no viaje el cuerpo.
    assert int(cabeceras["Content-Length"]) > 0


def test_get_ruta_inexistente_es_404_json(puerto):
    codigo, cabeceras, cuerpo = pedir(puerto, "GET", "/no-existe-xyz.html")
    assert codigo == 404
    assert cabeceras["Content-Type"].startswith("application/json")
    assert "error" in json.loads(cuerpo)


def test_api_ruta_inexistente_es_404_json(puerto):
    codigo, cabeceras, cuerpo = pedir(puerto, "GET", "/api/ruta-que-no-existe")
    assert codigo == 404
    assert "error" in json.loads(cuerpo)


@pytest.mark.parametrize("metodo", ["PUT", "TRACE"])
def test_verbo_sin_manejador_es_405_json(puerto, metodo):
    codigo, cabeceras, cuerpo = pedir(puerto, metodo, "/")
    assert codigo == 405
    assert cabeceras["Content-Type"].startswith("application/json")
    assert "Allow" in cabeceras
    assert "error" in json.loads(cuerpo)


def test_post_sobre_archivo_estatico_es_405(puerto):
    codigo, cabeceras, cuerpo = pedir(puerto, "POST", "/index.html")
    assert codigo == 405
    assert "GET" in cabeceras["Allow"]
    assert "error" in json.loads(cuerpo)
