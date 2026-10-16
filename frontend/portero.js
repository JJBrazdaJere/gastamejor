/* GastaMejor - portero.js
   ------------------------------------------------------------
   PORTERO de entrada: decide si hay que pasar por la encuesta
   obligatoria de ingreso (encuesta.html) antes de usar la app.

   Reglas (fail-open: ante cualquier duda, NO redirigimos):
     - En un iframe (pruebas, tutorial, previsualizaciones) NO se
       redirige: seria un bucle o romperia la pagina que lo embebe.
     - Con el ejemplo de Ana cargado NO se redirige.
     - Con un enlace compartido en la URL NO se redirige.
     - Con una configuracion ya guardada NO se redirige.

   `debeHacerEncuesta` es una funcion PURA (recibe los datos y
   decide); `aplicarPortero` arma esos datos y redirige si toca.
   ------------------------------------------------------------ */
"use strict";

function estaEnIframe() {
  try {
    return window.top !== window.self;
  } catch (_) {
    return true;
  }
}

/* ¿Hay una configuracion guardada en este dispositivo? (fail-open) */
function hayConfigGuardada() {
  try {
    return localStorage.getItem(CLAVE_CONFIG) !== null;
  } catch (_) {
    return true;
  }
}

/* ¿Esta cargado el ejemplo de Ana? (fail-open: false) */
function hayEjemploGuardado() {
  try {
    return localStorage.getItem(CLAVE_EJEMPLO) === "1";
  } catch (_) {
    return false;
  }
}

/* PURA: ¿el usuario tiene que hacer la encuesta? */
function debeHacerEncuesta(datos) {
  datos = datos || {};
  return !datos.esIframe && !datos.ejemplo && !datos.enlaceCompartido && !datos.config;
}

/* Arma los datos del portero y, si corresponde, manda a la encuesta.
   Devuelve true si redirigio (para cortar el arranque de la app). */
function aplicarPortero() {
  let enlaceCompartido = false;
  try {
    enlaceCompartido = typeof configDesdeEnlace === "function" && !!configDesdeEnlace();
  } catch (_) {
    enlaceCompartido = false;
  }

  const datos = {
    esIframe: estaEnIframe(),
    ejemplo: hayEjemploGuardado(),
    enlaceCompartido: enlaceCompartido,
    config: hayConfigGuardada(),
  };

  if (debeHacerEncuesta(datos)) {
    location.replace("encuesta.html");
    return true;
  }
  return false;
}
