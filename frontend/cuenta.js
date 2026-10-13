"use strict";

/* ============================================================
   GastaMejor — Ingresos diarios y cuenta (cuenta.js)
   Depende de: storage.js (MONEDAS, guardarIngresoMes) y api.js (API).
   ============================================================ */

function $(sel) {
  return document.querySelector(sel);
}

let temporizadorToast = null;
function toast(mensaje) {
  const t = $("#toast");
  if (!t) return;
  t.textContent = mensaje;
  t.hidden = false;
  clearTimeout(temporizadorToast);
  temporizadorToast = setTimeout(function () {
    t.hidden = true;
  }, 2600);
}

function esc(texto) {
  return String(texto == null ? "" : texto)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* ---------- Formato de montos (1.000.000,00), igual que app.js ---------- */
function analizarEntrada(texto) {
  const s = String(texto).replace(/[^\d.,]/g, "");
  const iComa = s.lastIndexOf(",");
  if (iComa !== -1) {
    return {
      entero: s.slice(0, iComa).replace(/\D/g, ""),
      dec: s.slice(iComa + 1).replace(/\D/g, "").slice(0, 2),
    };
  }
  const iDot = s.lastIndexOf(".");
  if (iDot !== -1) {
    const cola = s.slice(iDot + 1);
    const puntos = (s.match(/\./g) || []).length;
    if (puntos === 1 && cola.length <= 2) {
      return { entero: s.slice(0, iDot).replace(/\D/g, ""), dec: cola.replace(/\D/g, "") };
    }
    return { entero: s.replace(/\D/g, ""), dec: null };
  }
  return { entero: s.replace(/\D/g, ""), dec: null };
}

function formatearEntradaMonto(texto) {
  const a = analizarEntrada(texto);
  const entero = a.entero.replace(/^0+(?=\d)/, "");
  const agrupado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  if (a.dec === null) return agrupado;
  return (agrupado === "" ? "0" : agrupado) + "," + a.dec;
}

function parsearEntradaMonto(texto) {
  const a = analizarEntrada(texto);
  if (a.entero === "" && (a.dec === null || a.dec === "")) return null;
  const n = Number((a.entero || "0") + "." + (a.dec || "0"));
  return isFinite(n) ? n : null;
}

function formatearNumeroMonto(n, decimales) {
  const dec = decimales === undefined ? 2 : decimales;
  const negativo = n < 0;
  const partes = Math.abs(Number(n) || 0).toFixed(dec).split(".");
  const entero = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return (negativo ? "-" : "") + entero + (dec > 0 ? "," + partes[1] : "");
}

/* Valor limpio para mandar a la API: "1.234,50" -> "1234.50" */
function montoParaApi(texto) {
  const n = parsearEntradaMonto(texto);
  return n === null ? "" : String(n);
}

/* Dinero formateado para mostrar, con el símbolo de la moneda. */
function plata(valor, moneda) {
  const n = Number(valor) || 0;
  try {
    return new Intl.NumberFormat("es-AR", {
      style: "currency",
      currency: moneda || "ARS",
      maximumFractionDigits: 2,
    }).format(n);
  } catch (_) {
    return "$ " + formatearNumeroMonto(n, 2);
  }
}

/* ---------- Estado ---------- */
const estadoCuenta = {
  cliente: null,
  mes: "",
  resumen: null,
  ingresos: [],
  emailRegistro: "",
  codigoTest: "",
};

function mesDeHoy() {
  const ahora = new Date();
  return ahora.getFullYear() + "-" + String(ahora.getMonth() + 1).padStart(2, "0");
}

function diaDeHoy() {
  const ahora = new Date();
  return (
    ahora.getFullYear() +
    "-" +
    String(ahora.getMonth() + 1).padStart(2, "0") +
    "-" +
    String(ahora.getDate()).padStart(2, "0")
  );
}

function mostrarVista(nombre) {
  $("#vista-cargando").hidden = nombre !== "cargando";
  $("#vista-auth").hidden = nombre !== "auth";
  $("#vista-panel").hidden = nombre !== "panel";
}

function mostrarError(id, mensaje) {
  const el = $(id);
  if (!el) return;
  if (mensaje) {
    el.textContent = mensaje;
    el.hidden = false;
  } else {
    el.hidden = true;
  }
}

/* ---------- Sesión ---------- */
async function iniciar() {
  // Rellenar el selector de moneda y el input de mes.
  const selMoneda = $("#perfil-moneda");
  selMoneda.innerHTML = MONEDAS.map(function (m) {
    return '<option value="' + m.codigo + '">' + esc(m.nombre) + "</option>";
  }).join("");

  $("#api-url").value = (function () {
    try {
      return localStorage.getItem("gastamejor.apiUrl.v1") || "";
    } catch (_) {
      return "";
    }
  })();

  conectarEventos();

  estadoCuenta.mes = mesDeHoy();
  $("#mes").value = estadoCuenta.mes;
  $("#ing-fecha").value = diaDeHoy();

  if (API.hayToken()) {
    mostrarVista("cargando");
    try {
      await cargarPanel();
      return;
    } catch (error) {
      if (error.status === 401) {
        apiBorrarToken();
      } else {
        toast(error.message);
      }
    }
  }
  mostrarVista("auth");
  comprobarBackend();
}

/* Avisa (con contexto) si la dirección actual no responde como la API de
   GastaMejor; por ejemplo, si es un servidor de archivos estáticos o Pages. */
async function comprobarBackend() {
  const aviso = $("#aviso-backend");
  if (!aviso) return;
  try {
    await API.salud();
    aviso.hidden = true;
    aviso.textContent = "";
  } catch (error) {
    // Solo ofrecemos el modo invitado cuando el backend no está (no ante un
    // error puntual de la API con un backend que sí responde).
    const extra =
      error.sinBackend || error.conexion
        ? " Mientras tanto podés usar la app como invitado."
        : "";
    aviso.textContent = error.message + extra;
    aviso.hidden = false;
  }
}

async function cargarPanel() {
  const datos = await API.perfil();
  estadoCuenta.cliente = datos.cliente;
  pintarPerfil();
  mostrarVista("panel");
  await cargarMes(estadoCuenta.mes);
}

function pintarPerfil() {
  const c = estadoCuenta.cliente;
  $("#saludo").textContent = "Hola, " + (c.nombre || c.usuario);
  $("#saludo-email").textContent = c.email + (c.email_verificado ? " ✔" : "");
  $("#perfil-fijo").value = Number(c.ingreso_fijo_mensual) > 0
    ? formatearNumeroMonto(Number(c.ingreso_fijo_mensual), 2)
    : "";
  $("#perfil-moneda").value = c.moneda || "ARS";
  $("#perfil-telefono").value = c.telefono || "";
}

/* ---------- Mes / ingresos ---------- */
async function cargarMes(mes) {
  estadoCuenta.mes = mes || mesDeHoy();
  $("#mes").value = estadoCuenta.mes;
  try {
    const resumen = await API.resumen(estadoCuenta.mes);
    const lista = await API.ingresos(estadoCuenta.mes);
    estadoCuenta.resumen = resumen;
    estadoCuenta.ingresos = lista.ingresos || [];
    pintarResumen();
    pintarLista();
  } catch (error) {
    toast(error.message);
  }
}

function pintarResumen() {
  const r = estadoCuenta.resumen;
  if (!r) return;
  const moneda = r.moneda || "ARS";
  $("#res-diario").textContent = plata(r.total_diario, moneda);
  $("#res-fijo").textContent = plata(r.ingreso_fijo, moneda);
  $("#res-total").textContent = plata(r.total, moneda);
  $("#btn-usar").disabled = Number(r.total) <= 0;
}

function pintarLista() {
  const lista = $("#lista-ingresos");
  if (!estadoCuenta.ingresos.length) {
    lista.innerHTML = "";
    $("#sin-ingresos").hidden = false;
    return;
  }
  $("#sin-ingresos").hidden = true;
  const moneda = (estadoCuenta.resumen && estadoCuenta.resumen.moneda) || "ARS";
  lista.innerHTML = estadoCuenta.ingresos
    .map(function (ing) {
      const partes = String(ing.fecha).split("-");
      const fecha = partes.length === 3 ? partes[2] + "/" + partes[1] + "/" + partes[0] : ing.fecha;
      const desc = ing.descripcion ? esc(ing.descripcion) : '<span class="nota">Sin descripción</span>';
      return (
        '<li class="item-ingreso">' +
        '<span class="datos"><span class="fecha">' + esc(fecha) + "</span>" + desc + "</span>" +
        '<span class="monto">' + esc(plata(ing.monto, moneda)) + "</span>" +
        '<button class="btn-borrar" type="button" data-id="' + esc(ing.id) + '" aria-label="Eliminar">🗑️</button>' +
        "</li>"
      );
    })
    .join("");
}

async function agregarIngreso() {
  mostrarError("#error-ingreso", "");
  const monto = montoParaApi($("#ing-monto").value);
  const fecha = $("#ing-fecha").value || diaDeHoy();
  const descripcion = $("#ing-desc").value.trim();

  if (!monto || Number(monto) <= 0) {
    mostrarError("#error-ingreso", "Escribí un monto mayor a cero.");
    $("#ing-monto").focus();
    return;
  }
  try {
    await API.agregarIngreso({ monto: monto, fecha: fecha, descripcion: descripcion || null });
    $("#ing-monto").value = "";
    $("#ing-desc").value = "";
    // Si el ingreso es de otro mes, nos movemos a ese mes para verlo.
    const mesDelIngreso = fecha.slice(0, 7);
    await cargarMes(mesDelIngreso);
    toast("Ingreso agregado ✔");
  } catch (error) {
    mostrarError("#error-ingreso", error.message);
  }
}

async function eliminarIngreso(id) {
  try {
    await API.eliminarIngreso(id);
    await cargarMes(estadoCuenta.mes);
    toast("Ingreso eliminado");
  } catch (error) {
    toast(error.message);
  }
}

function usarTotal() {
  const r = estadoCuenta.resumen;
  if (!r || Number(r.total) <= 0) return;
  guardarIngresoMes({
    mes: r.mes,
    total: Number(r.total),
    moneda: r.moneda || "ARS",
    cantidad: r.cantidad,
  });
  window.location.href = "index.html";
}

async function guardarPerfil() {
  mostrarError("#ok-perfil", "");
  const fijo = montoParaApi($("#perfil-fijo").value);
  const datos = {
    moneda: $("#perfil-moneda").value,
    telefono: $("#perfil-telefono").value.trim(),
  };
  if (fijo !== "") datos.ingreso_fijo_mensual = fijo;
  else datos.ingreso_fijo_mensual = "0";

  try {
    const res = await API.actualizarPerfil(datos);
    estadoCuenta.cliente = res.cliente;
    pintarPerfil();
    await cargarMes(estadoCuenta.mes);
    const ok = $("#ok-perfil");
    ok.textContent = "Datos guardados ✔";
    ok.hidden = false;
    setTimeout(function () {
      ok.hidden = true;
    }, 2600);
  } catch (error) {
    toast(error.message);
  }
}

/* ---------- Autenticación ---------- */
function mostrarTab(cual) {
  $("#tab-login").classList.toggle("activo", cual === "login");
  $("#tab-registro").classList.toggle("activo", cual === "registro");
  $("#panel-login").hidden = cual !== "login";
  $("#panel-registro").hidden = cual !== "registro";
  $("#panel-verificar").hidden = true;
  mostrarError("#error-auth", "");
}

async function hacerLogin() {
  mostrarError("#error-auth", "");
  const usuario = $("#login-usuario").value.trim();
  const password = $("#login-password").value;
  if (!usuario || !password) {
    mostrarError("#error-auth", "Completá usuario y contraseña.");
    return;
  }
  try {
    const res = await API.login(usuario, password);
    apiGuardarToken(res.token);
    estadoCuenta.cliente = res.cliente;
    $("#login-password").value = "";
    pintarPerfil();
    mostrarVista("panel");
    await cargarMes(mesDeHoy());
    toast("¡Hola de nuevo! 👋");
  } catch (error) {
    mostrarError("#error-auth", error.message);
  }
}

async function hacerRegistro() {
  mostrarError("#error-auth", "");
  const datos = {
    nombre: $("#reg-nombre").value.trim(),
    usuario: $("#reg-usuario").value.trim(),
    email: $("#reg-email").value.trim(),
    telefono: $("#reg-telefono").value.trim() || null,
    password: $("#reg-password").value,
  };
  if (!datos.nombre || !datos.usuario || !datos.email || !datos.password) {
    mostrarError("#error-auth", "Completá nombre, usuario, email y contraseña.");
    return;
  }
  try {
    const res = await API.registro(datos);
    estadoCuenta.emailRegistro = res.email;
    estadoCuenta.codigoTest = res.codigo_test || "";
    $("#verif-email").textContent = res.email;
    $("#verif-codigo").value = "";
    const aviso = $("#aviso-test");
    if (res.codigo_test) {
      aviso.textContent =
        "🔧 Modo prueba (no se envía email real): tu código es " + res.codigo_test;
      aviso.hidden = false;
      $("#verif-codigo").value = res.codigo_test;
    } else {
      aviso.hidden = true;
    }
    $("#panel-login").hidden = true;
    $("#panel-registro").hidden = true;
    $("#panel-verificar").hidden = false;
    toast("Cuenta creada. Verificá tu email.");
  } catch (error) {
    mostrarError("#error-auth", error.message);
  }
}

async function hacerVerificacion() {
  mostrarError("#error-auth", "");
  const codigo = $("#verif-codigo").value.trim();
  if (!codigo) {
    mostrarError("#error-auth", "Escribí el código que te llegó.");
    return;
  }
  try {
    await API.verificar(estadoCuenta.emailRegistro, codigo);
  } catch (error) {
    mostrarError("#error-auth", error.message);
    return;
  }

  toast("Email verificado ✔ Iniciando sesión…");
  // Auto-login con los datos del registro (si seguimos teniendo la contraseña).
  const usuario = $("#reg-usuario").value.trim() || estadoCuenta.emailRegistro;
  const password = $("#reg-password").value;
  if (password) {
    try {
      const res = await API.login(usuario, password);
      apiGuardarToken(res.token);
      estadoCuenta.cliente = res.cliente;
      $("#reg-password").value = "";
      pintarPerfil();
      mostrarVista("panel");
      await cargarMes(mesDeHoy());
      return;
    } catch (_) {
      /* si falla, lo mandamos al login a mano */
    }
  }
  mostrarTab("login");
  $("#login-usuario").value = usuario;
  mostrarError("#error-auth", "Cuenta verificada. Ingresá tu contraseña para entrar.");
}

async function reenviarCodigo() {
  mostrarError("#error-auth", "");
  try {
    const res = await API.reenviar(estadoCuenta.emailRegistro);
    if (res.codigo_test) {
      const aviso = $("#aviso-test");
      aviso.textContent = "🔧 Modo prueba: tu código es " + res.codigo_test;
      aviso.hidden = false;
      $("#verif-codigo").value = res.codigo_test;
    }
    toast("Código reenviado.");
  } catch (error) {
    mostrarError("#error-auth", error.message);
  }
}

async function salir() {
  try {
    await API.logout();
  } catch (_) {
    /* aunque falle, cerramos localmente */
  }
  apiBorrarToken();
  estadoCuenta.cliente = null;
  mostrarTab("login");
  mostrarVista("auth");
  toast("Sesión cerrada.");
}

/* Borra la cuenta del usuario. Pide la contraseña y una confirmación extra
   porque es una acción irreversible (se borran tambien todos los ingresos). */
async function borrarCuenta() {
  mostrarError("#error-borrar", "");
  const password = $("#borrar-password").value;
  if (!password) {
    mostrarError("#error-borrar", "Escribí tu contraseña para confirmar.");
    $("#borrar-password").focus();
    return;
  }
  const seguro = window.confirm(
    "¿Seguro que querés borrar tu cuenta?\n\n" +
      "Se van a eliminar tu cuenta y TODOS tus ingresos. " +
      "Esta acción no se puede deshacer."
  );
  if (!seguro) return;

  const boton = $("#btn-borrar-cuenta");
  boton.disabled = true;
  try {
    await API.eliminarCuenta(password);
    apiBorrarToken();
    estadoCuenta.cliente = null;
    $("#borrar-password").value = "";
    mostrarTab("login");
    mostrarVista("auth");
    toast("Tu cuenta fue eliminada.");
  } catch (error) {
    mostrarError("#error-borrar", error.message);
  } finally {
    boton.disabled = false;
  }
}

/* ---------- Servidor (avanzado) ---------- */
async function guardarUrl() {
  apiGuardarUrl($("#api-url").value.trim());
  const estado = $("#api-estado");
  estado.textContent = "Probando conexión…";
  try {
    await API.salud();
    estado.textContent = "✅ Conexión OK con " + (apiBase() || "este mismo sitio") + ".";
  } catch (error) {
    estado.textContent = "❌ " + error.message;
  }
  comprobarBackend();
}

/* ---------- Eventos ---------- */
function conectarEventos() {
  $("#tab-login").addEventListener("click", function () { mostrarTab("login"); });
  $("#tab-registro").addEventListener("click", function () { mostrarTab("registro"); });
  $("#btn-login").addEventListener("click", hacerLogin);
  $("#btn-registro").addEventListener("click", hacerRegistro);
  $("#btn-verificar").addEventListener("click", hacerVerificacion);
  $("#btn-reenviar").addEventListener("click", reenviarCodigo);
  $("#btn-logout").addEventListener("click", salir);
  $("#btn-borrar-cuenta").addEventListener("click", borrarCuenta);
  $("#btn-api-url").addEventListener("click", guardarUrl);

  $("#login-password").addEventListener("keydown", function (e) {
    if (e.key === "Enter") hacerLogin();
  });

  $("#ing-monto").addEventListener("input", function () {
    this.value = formatearEntradaMonto(this.value);
  });
  $("#perfil-fijo").addEventListener("input", function () {
    this.value = formatearEntradaMonto(this.value);
  });

  $("#btn-agregar-ingreso").addEventListener("click", agregarIngreso);
  $("#btn-guardar-perfil").addEventListener("click", guardarPerfil);
  $("#btn-usar").addEventListener("click", usarTotal);
  $("#mes").addEventListener("change", function () {
    cargarMes(this.value || mesDeHoy());
  });

  $("#lista-ingresos").addEventListener("click", function (e) {
    const boton = e.target.closest(".btn-borrar");
    if (boton) eliminarIngreso(boton.getAttribute("data-id"));
  });
}

document.addEventListener("DOMContentLoaded", iniciar);
