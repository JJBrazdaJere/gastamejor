"use strict";

/* ============================================================
   GastaMejor — Cliente de la API (api.js)
   Habla con el backend (servidor.py) para cuentas e ingresos diarios.
   Si no hay backend configurado, la app sigue funcionando en modo
   invitado (todo local en localStorage): solo no habrá cuenta.
   ============================================================ */

const CLAVE_TOKEN = "gastamejor.token.v1";
const CLAVE_API_URL = "gastamejor.apiUrl.v1";

/* Dirección del backend. Por defecto vacío = mismo origen (cuando el
   sitio lo sirve el propio backend, ej. local). En GitHub Pages hay que
   apuntarla al backend publicado (se configura en la página de cuenta). */
function apiBase() {
  if (typeof window !== "undefined" && window.GASTAMEJOR_API) {
    return String(window.GASTAMEJOR_API).replace(/\/+$/, "");
  }
  try {
    const guardada = localStorage.getItem(CLAVE_API_URL);
    if (guardada) return String(guardada).replace(/\/+$/, "");
  } catch (_) {
    /* sin persistencia */
  }
  return "";
}

function apiGuardarUrl(url) {
  try {
    localStorage.setItem(CLAVE_API_URL, String(url || "").replace(/\/+$/, ""));
  } catch (_) {
    /* sin persistencia */
  }
}

/* ---------- Token de sesión ---------- */
function apiToken() {
  try {
    return localStorage.getItem(CLAVE_TOKEN) || "";
  } catch (_) {
    return "";
  }
}

function apiGuardarToken(token) {
  try {
    localStorage.setItem(CLAVE_TOKEN, token);
  } catch (_) {
    /* sin persistencia */
  }
}

function apiBorrarToken() {
  try {
    localStorage.removeItem(CLAVE_TOKEN);
  } catch (_) {
    /* sin persistencia */
  }
}

/* ---------- Petición genérica ---------- */
async function apiPedir(metodo, ruta, cuerpo) {
  const cabeceras = {};
  const token = apiToken();
  if (token) cabeceras["Authorization"] = "Bearer " + token;

  const opciones = { method: metodo, headers: cabeceras };
  if (cuerpo !== undefined && cuerpo !== null) {
    cabeceras["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }

  let respuesta;
  const controlador = new AbortController();
  const temporizador = setTimeout(function () { controlador.abort(); }, 60000);
  opciones.signal = controlador.signal;
  try {
    respuesta = await fetch(apiBase() + ruta, opciones);
  } catch (_) {
    const error = new Error(
      "No se pudo conectar con el servidor. La base de datos puede estar en reposo; intentá nuevamente en unos segundos. " +
        "En local, arrancá `python servidor.py` y abrí http://127.0.0.1:8000/cuenta.html."
    );
    error.conexion = true;
    throw error;
  } finally {
    clearTimeout(temporizador);
  }

  let datos = null;
  const texto = await respuesta.text();
  if (texto) {
    try {
      datos = JSON.parse(texto);
    } catch (_) {
      datos = null;
    }
  }

  if (!respuesta.ok) {
    const error = new Error(mensajeDeRespuesta(respuesta.status, datos));
    error.status = respuesta.status;
    error.sinBackend = esRespuestaSinBackend(respuesta.status, datos);
    throw error;
  }
  return datos;
}

/* El backend de GastaMejor siempre contesta JSON. Si un 404/405/501 llega con
   un cuerpo que no es JSON, casi seguro que la dirección no es la API, sino un
   servidor de archivos estáticos (`python -m http.server`) o GitHub Pages. */
function esRespuestaSinBackend(status, datos) {
  return (status === 404 || status === 405 || status === 501) && !datos;
}

function mensajeDeRespuesta(status, datos) {
  if (datos && datos.error) return datos.error;

  if (status === 501) {
    return (
      "Esta dirección es un servidor de archivos, no el backend de GastaMejor (error 501). " +
      "En local: cortá ese servidor y arrancá `python servidor.py`; después abrí " +
      "http://127.0.0.1:8000/cuenta.html."
    );
  }
  if (status === 404 || status === 405) {
    return (
      "No se encontró la API de GastaMejor en " +
      (apiBase() || "esta dirección") +
      " (error " +
      status +
      "). Para usar cuentas hace falta el backend (servidor.py)."
    );
  }
  return "Error " + status + " del servidor.";
}

/* ---------- Endpoints ---------- */
const API = {
  hayToken: apiToken,

  salud: () => apiPedir("GET", "/api/salud"),
  registro: (datos) => apiPedir("POST", "/api/registro", datos),
  verificar: (email, codigo) => apiPedir("POST", "/api/verificar", { email: email, codigo: codigo }),
  reenviar: (email) => apiPedir("POST", "/api/reenviar", { email: email }),
  login: (usuario, password) => apiPedir("POST", "/api/login", { usuario: usuario, password: password }),
  pedirRecuperacion: (email) => apiPedir("POST", "/api/recuperar", { email: email }),
  restablecerPassword: (email, codigo, nueva) =>
    apiPedir("POST", "/api/restablecer", { email: email, codigo: codigo, nueva: nueva }),
  logout: () => apiPedir("POST", "/api/logout", {}),
  perfil: () => apiPedir("GET", "/api/perfil"),
  actualizarPerfil: (datos) => apiPedir("PATCH", "/api/perfil", datos),
  cambiarPassword: (actual, nueva) => apiPedir("POST", "/api/password", { actual: actual, nueva: nueva }),
  eliminarCuenta: (password) => apiPedir("DELETE", "/api/cuenta", { password: password }),
  ingresos: (mes) =>
    apiPedir("GET", "/api/ingresos" + (mes ? "?mes=" + encodeURIComponent(mes) : "")),
  agregarIngreso: (datos) => apiPedir("POST", "/api/ingresos", datos),
  eliminarIngreso: (id) => apiPedir("DELETE", "/api/ingresos/" + encodeURIComponent(id)),
  resumen: (mes) => apiPedir("GET", "/api/resumen?mes=" + encodeURIComponent(mes)),
  resumenAnual: (anio) => apiPedir("GET", "/api/resumen/anual?anio=" + encodeURIComponent(anio)),
};
