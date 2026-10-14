"use strict";

/* ============================================================
   GastaMejor — sesion.js
   Botón de sesión en el encabezado, visible en todas las páginas.

   - Sin sesión  -> "Iniciar sesión" (lleva a cuenta.html).
   - Con sesión  -> "Hola, <nombre>" + "Cerrar sesión".

   NO llama a la red al cargar: solo lee el token/nombre guardados en
   localStorage. Así la app arranca rápido y no molesta si el backend
   está dormido. Al cerrar sesión, avisa al backend (si se puede) y
   limpia localmente igual.
   ============================================================ */

(function () {
  var CLAVE_TOKEN = "gastamejor.token.v1";
  var CLAVE_NOMBRE = "gastamejor.nombre.v1";

  /* ---------- Persistencia del nombre ---------- */
  function guardarNombre(nombre) {
    try {
      localStorage.setItem(CLAVE_NOMBRE, nombre || "");
    } catch (_) {
      /* sin persistencia */
    }
  }

  function borrarNombre() {
    try {
      localStorage.removeItem(CLAVE_NOMBRE);
    } catch (_) {
      /* sin persistencia */
    }
  }

  function leerNombre() {
    try {
      return localStorage.getItem(CLAVE_NOMBRE) || "";
    } catch (_) {
      return "";
    }
  }

  function haySesion() {
    if (typeof apiToken === "function") return !!apiToken();
    try {
      return !!localStorage.getItem(CLAVE_TOKEN);
    } catch (_) {
      return false;
    }
  }

  function limpiarToken() {
    if (typeof apiBorrarToken === "function") {
      apiBorrarToken();
    } else {
      try {
        localStorage.removeItem(CLAVE_TOKEN);
      } catch (_) {
        /* sin persistencia */
      }
    }
  }

  /* ---------- Pintado del botón según el estado ---------- */
  function pintar() {
    var boton = document.getElementById("btn-sesion");
    if (!boton) return;
    var etiqueta = document.getElementById("sesion-nombre");

    if (haySesion()) {
      boton.textContent = "Cerrar sesión";
      boton.setAttribute("aria-label", "Cerrar sesión");
      if (etiqueta) {
        var nombre = leerNombre();
        etiqueta.textContent = nombre ? "Hola, " + nombre : "Hola";
        etiqueta.hidden = false;
      }
    } else {
      boton.textContent = "Iniciar sesión";
      boton.setAttribute("aria-label", "Iniciar sesión");
      if (etiqueta) {
        etiqueta.textContent = "";
        etiqueta.hidden = true;
      }
    }
  }

  /* ---------- Cerrar sesión ---------- */
  function cerrarSesion() {
    // Avisamos al backend, pero sin esperarlo: si el servidor está dormido
    // (Render free) igual cerramos la sesión al instante en este navegador.
    try {
      if (typeof API !== "undefined" && API && API.logout) {
        var pedido = API.logout();
        if (pedido && typeof pedido.catch === "function") {
          pedido.catch(function () {});
        }
      }
    } catch (_) {
      /* seguimos con la limpieza local */
    }

    limpiarToken();
    borrarNombre();
    pintar();
    // En la página de cuenta volvemos a mostrar el formulario de ingreso.
    if (document.getElementById("vista-auth")) {
      location.reload();
    }
  }

  /* ---------- Clic ---------- */
  function alHacerClic() {
    if (haySesion()) {
      cerrarSesion();
      return;
    }
    // Si ya estamos en la página de cuenta, enfocamos el formulario.
    var loginUsuario = document.getElementById("login-usuario");
    if (loginUsuario) {
      loginUsuario.focus();
      return;
    }
    location.href = "cuenta.html";
  }

  /* ---------- Inicio ---------- */
  function iniciar() {
    var boton = document.getElementById("btn-sesion");
    if (!boton) return;
    boton.addEventListener("click", alHacerClic);
    pintar();
  }

  // Expuestas para que cuenta.js actualice el nombre y el botón.
  window.gmGuardarNombre = guardarNombre;
  window.gmBorrarNombre = borrarNombre;
  window.gmActualizarSesion = pintar;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
