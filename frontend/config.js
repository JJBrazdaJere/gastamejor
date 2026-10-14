"use strict";

/* ============================================================
   GastaMejor — config.js
   Dirección del backend publicado (API de cuentas).

   - En local (localhost / 127.0.0.1 / file://) NO se toca nada:
     se usa el mismo origen (el backend que corre en tu PC).
   - En un sitio estático publicado (GitHub Pages) se apunta al
     backend de Render, porque Pages no ejecuta Python.

   Se completa una sola vez, con la URL del backend publicado.
   ============================================================ */

(function () {
  // 👉 URL del backend publicado (sin barra final).
  var URL_BACKEND = "https://gastamejor-api.onrender.com";

  var host = (window.location && window.location.hostname) || "";
  var esLocal =
    host === "" || host === "localhost" || host === "127.0.0.1" || host === "::1";

  if (!esLocal && URL_BACKEND) {
    window.GASTAMEJOR_API = String(URL_BACKEND).replace(/\/+$/, "");
  }
})();
