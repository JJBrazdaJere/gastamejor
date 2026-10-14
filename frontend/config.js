"use strict";

/* ============================================================
   GastaMejor — config.js
   Dirección del backend publicado (API de cuentas).

   - "" (vacío) = mismo origen: lo sirve el propio backend (local).
   - En GitHub Pages (sitio estático) hay que poner la URL pública
     del backend, porque Pages no ejecuta Python.

   Se completa una sola vez, cuando el backend esté publicado.
   ============================================================ */

(function () {
  // 👉 Pegá acá la URL del backend publicado (sin barra final).
  //    Ejemplo: "https://gastamejor-api.onrender.com"
  var URL_BACKEND = "";

  if (URL_BACKEND) {
    window.GASTAMEJOR_API = String(URL_BACKEND).replace(/\/+$/, "");
  }
})();
