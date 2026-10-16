/* GastaMejor - encuesta.js
   ------------------------------------------------------------
   ENCUESTA OBLIGATORIA de ingreso (primera vez).

   Es una pagina aparte (encuesta.html) que NO carga app.js ni
   portero.js. Solo usa:
     - storage.js  (categorias, monedas, perfiles, guardarConfig,
                    guardarMeta, guardarMesHistorial, guardarIngresoMes)
     - motor.js    (la logica pura: validaciones, reparto, metas)
     - api.js      (apiToken: si ya hay sesion, no pedimos el nombre)

   Al terminar guarda: la configuracion, la meta, el ingreso del mes
   (para que la app lo prellene) y el mes en curso en el historial, y
   lleva a la app (index.html). Tambien se puede guardar el mes sin
   salir (boton "Guardar este mes en el Historial") y, si ya existe una
   config guardada, se ofrece "Volver a la app" en el encabezado.
   ------------------------------------------------------------ */
"use strict";

/* Pasos de la encuesta, en orden. El paso "nombre" se saltea si el
   usuario ya tiene sesion iniciada (apiToken). */
const PASOS_ENCUESTA = ["nombre", "ingreso", "gastos", "perfil", "meta", "plan", "guardar"];

const GRUPO_ORDEN = ["necesidad", "deseo", "ahorro"];

/* Estado local de la encuesta (no toca el estado de la app). */
const encuesta = {
  paso: 0,
  nombre: "",
  ingreso: null,
  moneda: "ARS",
  gastos: [],
  perfil: "equilibrado",
  perfilTocado: false,
  metaTipo: "ahorrar",
  metaMonto: 0,
  metaMeses: 6,
  cotizacion: null,
};

function el(id) {
  return document.getElementById(id);
}

/* ---------- Toast ---------- */

let temporizadorEncuesta = null;
function encToast(mensaje) {
  const t = el("enc-toast");
  if (!t) return;
  t.textContent = mensaje;
  t.hidden = false;
  clearTimeout(temporizadorEncuesta);
  temporizadorEncuesta = setTimeout(function () { t.hidden = true; }, 2600);
}

/* ---------- Pasos y condiciones ---------- */

/* ¿Ya hay sesion? Entonces no pedimos el nombre. */
function haySesionEncuesta() {
  return typeof apiToken === "function" && !!apiToken();
}

/* ¿Ya hay una configuracion guardada en este dispositivo?
   OJO: encuesta.html NO carga portero.js, asi que chequeamos la clave
   directamente (con try/catch, como hace hayConfigGuardada). */
function hayConfigEncuesta() {
  try {
    return localStorage.getItem(CLAVE_CONFIG) !== null;
  } catch (_) {
    return false;
  }
}

/* El enlace "Volver a la app" solo tiene sentido si ya hay una app con
   config: en la primera vez la encuesta es obligatoria y NO se muestra. */
function mostrarSalidaEncuesta() {
  const volver = el("enc-volver-app");
  if (!volver) return;
  volver.hidden = !hayConfigEncuesta();
}

function pasosActivos() {
  return PASOS_ENCUESTA.filter(function (p) {
    return p !== "nombre" || !haySesionEncuesta();
  });
}

function pasoActual() {
  return pasosActivos()[encuesta.paso] || "guardar";
}

/* ---------- Formato de montos en los inputs ---------- */

function aplicarFormatoEncuesta(input) {
  const antes = input.value;
  const caret = input.selectionStart === null ? antes.length : input.selectionStart;
  let significativos = 0;
  for (let i = 0; i < caret && i < antes.length; i++) {
    if (/[\d,]/.test(antes[i])) significativos++;
  }
  const despues = formatearEntradaMonto(antes);
  if (despues === antes) return;
  input.value = despues;
  let pos = 0;
  let contados = 0;
  while (pos < despues.length && contados < significativos) {
    if (/[\d,]/.test(despues[pos])) contados++;
    pos++;
  }
  try { input.setSelectionRange(pos, pos); } catch (_) { /* sin seleccion */ }
}

function completarEncuesta(input) {
  const n = parsearEntradaMonto(input.value);
  input.value = n === null ? "" : formatearNumeroMonto(n, 2);
}

/* ---------- Construccion de los pasos ---------- */

function construirSelectsEncuesta() {
  const mon = el("enc-moneda");
  if (mon) {
    mon.innerHTML = MONEDAS.map(function (m) {
      return '<option value="' + m.codigo + '"' +
        (m.codigo === encuesta.moneda ? " selected" : "") + ">" + esc(m.nombre) + "</option>";
    }).join("");
  }

  const tipo = el("enc-meta-tipo");
  if (tipo) {
    tipo.innerHTML = METAS.map(function (m) {
      return '<option value="' + m.tipo + '"' +
        (m.tipo === encuesta.metaTipo ? " selected" : "") + ">" + esc(m.emoji + " " + m.etiqueta) + "</option>";
    }).join("");
  }

  const meses = el("enc-meta-meses");
  if (meses) meses.value = String(encuesta.metaMeses);
}

function asegurarGastosIniciales() {
  if (!encuesta.gastos || encuesta.gastos.length === 0) {
    encuesta.gastos = CATEGORIAS_POR_DEFECTO.map(function (c) {
      return { id: c.id, nombre: c.nombre, grupo: c.grupo, monto: 0 };
    });
  }
}

/* Sincroniza encuesta.gastos con todos los valores escritos en el DOM. */
function syncGastosFromDOM() {
  const cont = el("enc-gastos");
  if (!cont) return;
  const filas = cont.querySelectorAll(".encuesta-categoria");
  const nuevos = [];
  filas.forEach(function (fila) {
    const idx = parseInt(fila.dataset.idx, 10);
    if (isNaN(idx)) return;
    const g = encuesta.gastos[idx] || { id: "gasto-sync", nombre: "", grupo: "necesidad", monto: 0 };
    const inputMonto = fila.querySelector('[data-gasto-idx="' + idx + '"]');
    const inputNombre = fila.querySelector('[data-nombre-idx="' + idx + '"]');
    const selectGrupo = fila.querySelector('[data-grupo-idx="' + idx + '"]');
    const texto = inputMonto ? inputMonto.value : "";
    const n = parsearEntradaMonto(texto);
    const monto = tieneSignoNegativo(texto) || n === null ? 0 : Math.max(0, n);
    nuevos.push({
      id: g.id || ("gasto-" + Date.now() + "-" + Math.random().toString(36).slice(2, 6)),
      nombre: inputNombre && inputNombre.value ? inputNombre.value : (g.nombre || ""),
      grupo: selectGrupo && selectGrupo.value ? selectGrupo.value : (g.grupo || "necesidad"),
      monto: monto,
    });
  });
  encuesta.gastos = nuevos;
}

/* Crea una única fila de gasto y la devuelve. No toca el resto del DOM. */
function renderFilaGasto(idx, gasto) {
  const fila = document.createElement("div");
  fila.className = "encuesta-categoria";
  fila.dataset.idx = String(idx);
  fila.innerHTML =
    '<div class="encuesta-categoria-linea">' +
      '<input class="encuesta-gasto-nombre" type="text" data-nombre-idx="' + idx + '" value="' + esc(gasto.nombre || "") + '" placeholder="Nombre de categoría">' +
      '<select class="encuesta-gasto-grupo" data-grupo-idx="' + idx + '">' +
        '<option value="necesidad"' + (gasto.grupo === "necesidad" ? " selected" : "") + '>Necesidades</option>' +
        '<option value="deseo"' + (gasto.grupo === "deseo" ? " selected" : "") + '>Deseos</option>' +
        '<option value="ahorro"' + (gasto.grupo === "ahorro" ? " selected" : "") + '>Ahorro</option>' +
      '</select>' +
    '</div>' +
    '<div class="encuesta-categoria-linea">' +
      '<div class="campo-monto campo-monto-chico">' +
        '<span class="simbolo simbolo-chico" aria-hidden="true">$</span>' +
        '<input id="enc-gasto-' + idx + '" class="input-monto-chico" data-gasto-idx="' + idx +
        '" type="text" inputmode="decimal" placeholder="0,00" autocomplete="off" aria-label="' + esc(gasto.nombre || "") + '">' +
      '</div>' +
      '<button class="btn-eliminar-categoria" type="button" data-elim-idx="' + idx + '">🗑️ Eliminar</button>' +
    '</div>';
  return fila;
}

/* Renderiza toda la lista UNA SOLA VEZ (usado al entrar al paso). */
function renderGastosLista() {
  const cont = el("enc-gastos");
  if (!cont) return;
  cont.innerHTML = "";

  asegurarGastosIniciales();

  GRUPO_ORDEN.forEach(function (grupo) {
    const indices = [];
    encuesta.gastos.forEach(function (g, i) { if (g.grupo === grupo) indices.push(i); });
    if (!indices.length) return;

    const bloque = document.createElement("section");
    bloque.className = "encuesta-grupo";

    const titulo = document.createElement("h3");
    titulo.className = "encuesta-grupo-titulo";
    titulo.innerHTML =
      '<span class="chip chip-' + grupo + '" aria-hidden="true"></span>' + ETIQUETAS_GRUPO[grupo];
    bloque.appendChild(titulo);

    indices.forEach(function (i) {
      const g = encuesta.gastos[i];
      bloque.appendChild(renderFilaGasto(i, g));
    });

    cont.appendChild(bloque);
  });

  actualizarBotonesEliminar();
}

/* Actualiza el estado (disabled) de los botones eliminar según cantidad. */
function actualizarBotonesEliminar() {
  const cont = el("enc-gastos");
  if (!cont) return;
  const botones = cont.querySelectorAll(".btn-eliminar-categoria");
  botones.forEach(function (btn) {
    const idx = parseInt(btn.dataset.elimIdx, 10);
    if (!isNaN(idx)) {
      btn.disabled = encuesta.gastos.length <= 1;
    }
  });
}

/* Reindexa todas las filas del DOM para que coincidan con encuesta.gastos. */
function reindexarFilasGastos() {
  const cont = el("enc-gastos");
  if (!cont) return;
  const filas = cont.querySelectorAll(".encuesta-categoria");
  filas.forEach(function (fila, pos) {
    fila.dataset.idx = String(pos);
    const inputMonto = fila.querySelector(".input-monto-chico[data-gasto-idx]");
    if (inputMonto) inputMonto.dataset.gastoIdx = String(pos);
    if (inputMonto.id) inputMonto.id = "enc-gasto-" + pos;
    const inputNombre = fila.querySelector(".encuesta-gasto-nombre[data-nombre-idx]");
    if (inputNombre) inputNombre.dataset.nombreIdx = String(pos);
    const selectGrupo = fila.querySelector(".encuesta-gasto-grupo[data-grupo-idx]");
    if (selectGrupo) selectGrupo.dataset.grupoIdx = String(pos);
    const btn = fila.querySelector(".btn-eliminar-categoria[data-elim-idx]");
    if (btn) btn.dataset.elimIdx = String(pos);
  });
  actualizarBotonesEliminar();
}

/* Todos los gastos con su monto tal como están escritos (0 si vacío).
   Un monto escrito con signo menos NO vale: cuenta como 0 (el error se
   avisa al intentar avanzar) para no convertir nunca "-300" en 300. */
function leerGastos() {
  return encuesta.gastos.map(function (g, i) {
    const input = document.querySelector('[data-gasto-idx="' + i + '"]');
    const nombre = document.querySelector('[data-nombre-idx="' + i + '"]');
    const grupo = document.querySelector('[data-grupo-idx="' + i + '"]');
    const texto = input ? input.value : "";
    const n = parsearEntradaMonto(texto);
    const monto = tieneSignoNegativo(texto) || n === null ? 0 : Math.max(0, n);
    return {
      id: g.id,
      nombre: nombre && nombre.value ? nombre.value : (g.nombre || ""),
      grupo: grupo && grupo.value ? grupo.value : (g.grupo || "necesidad"),
      monto: monto,
    };
  });
}

/* Texto crudo de cada gasto, tal como lo escribió el usuario. */
function textosGastos() {
  return encuesta.gastos.map(function (g, i) {
    const input = document.querySelector('[data-gasto-idx="' + i + '"]');
    return input ? input.value : "";
  });
}

/* Valida los signos de una lista de textos de montos (rechaza el "-").
   Usa la función pura de motor.js; devuelve { ok, error }. */
function validarSignosEncuesta(textos) {
  for (let i = 0; i < textos.length; i++) {
    const v = validarMontoEscrito(textos[i]);
    if (!v.ok) return v;
  }
  return { ok: true, error: "" };
}

/* Solo los gastos cargados (para armar la configuración). */
function gastosConMonto() {
  return leerGastos().filter(function (g) { return g.monto > 0; });
}

function leerMetaEncuesta() {
  const sel = el("enc-meta-tipo");
  const montoInput = el("enc-meta-monto");
  const mesesInput = el("enc-meta-meses");
  const n = montoInput ? parsearEntradaMonto(montoInput.value) : null;
  const meses = mesesInput ? parseInt(mesesInput.value, 10) : NaN;
  return {
    tipo: sel ? sel.value : encuesta.metaTipo,
    monto: n === null ? 0 : Math.max(0, n),
    meses: isFinite(meses) ? meses : 0,
  };
}

/* ---------- Perfiles ---------- */

function renderEncuestaPerfiles() {
  const cont = el("enc-perfiles");
  if (!cont) return;
  cont.innerHTML = PERFILES.map(function (p) {
    const sel = p.id === encuesta.perfil;
    return '<button type="button" class="perfil-btn' + (sel ? " encuesta-perfil-sel" : "") +
      '" data-perfil="' + p.id + '" aria-pressed="' + sel + '">' +
      '<span class="perfil-emoji" aria-hidden="true">' + p.emoji + "</span>" +
      '<span class="perfil-info">' +
        '<span class="perfil-nombre">' + esc(p.nombre) + "</span>" +
        '<span class="perfil-pesos">' + p.grupos.necesidad + "/" + p.grupos.deseo + "/" + p.grupos.ahorro + "</span>" +
      "</span>" +
      '<span class="perfil-barra" aria-hidden="true">' +
        '<span class="perfil-barra-parte pb-necesidad" style="width:' + p.grupos.necesidad + '%"></span>' +
        '<span class="perfil-barra-parte pb-deseo" style="width:' + p.grupos.deseo + '%"></span>' +
        '<span class="perfil-barra-parte pb-ahorro" style="width:' + p.grupos.ahorro + '%"></span>' +
      "</span>" +
    "</button>";
  }).join("");
  renderPerfilHoy();
}

/* Perfil en el que hoy cae el usuario con los gastos que ya cargo
   (paso 4). Le avisa en que perfil recae su distribucion actual. */
function renderPerfilHoy() {
  const cont = el("enc-perfil-hoy");
  if (!cont) return;

  const ingreso = Number(encuesta.ingreso) || 0;
  const total = leerGastos().reduce(function (a, g) { return a + g.monto; }, 0);
  if (!(ingreso > 0) || total <= 0) {
    cont.innerHTML = '<p class="encuesta-perfil-hoy-texto">' +
      "Cargá tu ingreso y algún gasto para ver en qué perfil caés hoy. Tu objetivo es lo de abajo." +
    "</p>";
    return;
  }

  const cfg = configFinal();
  const p = perfilActual(cfg, ingreso, encuesta.cotizacion);
  const dist = distribucionActualGrupo(cfg, ingreso, encuesta.cotizacion);
  const reparto = calcularReparto(cfg, ingreso, encuesta.cotizacion);
  const montos = calcularSubtotalesGrupo(reparto, cfg);

  cont.innerHTML =
    '<p class="encuesta-perfil-hoy-texto">Con tus gastos de hoy caés en ' +
      "<strong>" + esc(p ? p.emoji + " " + p.nombre : "—") + "</strong>.</p>" +
    '<div class="encuesta-perfil-hoy-grupos">' +
      GRUPO_ORDEN.map(function (g) {
        return '<span class="encuesta-perfil-hoy-grupo">' +
          '<span class="chip chip-' + g + '" aria-hidden="true"></span>' +
          esc(ETIQUETAS_GRUPO[g]) + " " + fmtPct(dist[g]) +
          ' <span class="encuesta-perfil-hoy-monto">' + dinero(encuesta.moneda, montos[g] || 0) + "</span>" +
        "</span>";
      }).join("") +
    "</div>" +
    '<p class="encuesta-perfil-hoy-nota">Tu objetivo es lo de abajo.</p>';
}

/* ---------- Datos y validaciones ---------- */

function datosEncuesta() {
  return {
    nombre: encuesta.nombre,
    ingreso: Number(encuesta.ingreso) || 0,
    moneda: encuesta.moneda,
    gastos: gastosConMonto(),
    meta: { tipo: encuesta.metaTipo, monto: encuesta.metaMonto, meses: encuesta.metaMeses },
  };
}

function nombreActual() {
  const input = el("enc-nombre");
  return input ? input.value : encuesta.nombre;
}

function validarPaso(paso) {
  if (paso === "nombre") return validarNombre(nombreActual());
  if (paso === "ingreso") {
    const input = el("enc-ingreso");
    const v = validarSignosEncuesta([input ? input.value : ""]);
    if (!v.ok) return v;
    return validarIngreso(encuesta.ingreso, encuesta.moneda);
  }
  if (paso === "gastos") {
    syncGastosFromDOM();
    const v = validarSignosEncuesta(textosGastos());
    if (!v.ok) return v;
    return validarGastos(leerGastos());
  }
  if (paso === "meta") return validarMeta(leerMetaEncuesta());
  return { ok: true, error: "" };
}

function mostrarError(paso, mensaje) {
  const p = el("enc-error-" + paso);
  if (!p) return;
  p.textContent = mensaje;
  p.hidden = false;
}

function limpiarErrores() {
  document.querySelectorAll(".encuesta-error").forEach(function (p) {
    p.hidden = true;
    p.textContent = "";
  });
}

/* Lee lo escrito en el paso actual y lo pasa al estado local. */
function leerPasoActual() {
  const paso = pasoActual();
  if (paso === "nombre") {
    encuesta.nombre = nombreActual().trim();
  } else if (paso === "ingreso") {
    const input = el("enc-ingreso");
    const texto = input ? input.value : "";
    // Un monto con signo menos no vale (no lo convertimos en positivo).
    encuesta.ingreso = tieneSignoNegativo(texto) ? null : parsearEntradaMonto(texto);
    const sel = el("enc-moneda");
    if (sel) encuesta.moneda = sel.value;
  } else if (paso === "meta") {
    const m = leerMetaEncuesta();
    encuesta.metaTipo = m.tipo;
    encuesta.metaMonto = m.monto;
    encuesta.metaMeses = m.meses;
  }
  return paso;
}

/* ---------- Navegacion ---------- */

function irSiguiente() {
  const paso = leerPasoActual();
  const v = validarPaso(paso);
  if (!v.ok) {
    mostrarError(paso, v.error);
    return;
  }
  limpiarErrores();
  const pasos = pasosActivos();
  if (encuesta.paso >= pasos.length - 1) {
    guardarYEnviar();
    return;
  }
  encuesta.paso += 1;
  mostrarPaso();
}

function irAnterior() {
  leerPasoActual();
  limpiarErrores();
  encuesta.paso = Math.max(0, encuesta.paso - 1);
  mostrarPaso();
}

function mostrarPaso() {
  const pasos = pasosActivos();
  if (!pasos.length) return;
  if (encuesta.paso < 0) encuesta.paso = 0;
  if (encuesta.paso > pasos.length - 1) encuesta.paso = pasos.length - 1;

  const paso = pasos[encuesta.paso];
  document.querySelectorAll(".encuesta-paso").forEach(function (sec) {
    sec.hidden = sec.getAttribute("data-paso") !== paso;
  });

  const contador = el("enc-contador");
  if (contador) contador.textContent = "Paso " + (encuesta.paso + 1) + " de " + pasos.length;
  const barra = el("enc-barra");
  if (barra) barra.style.width = (((encuesta.paso + 1) / pasos.length) * 100).toFixed(1) + "%";

  if (paso === "gastos") {
    // Al entrar al paso, sincronizar valores desde DOM y renderizar lista incremental
    syncGastosFromDOM();
    renderGastosLista();
    refrescarResumenGastos();
  }
  if (paso === "perfil") {
    // Sincronizar gastos antes de calcular
    syncGastosFromDOM();
    if (!encuesta.perfilTocado) {
      encuesta.perfil = perfilEfectivoEncuesta(false, encuesta.perfil, encuesta.metaTipo);
    }
    renderEncuestaPerfiles();
  }
  if (paso === "meta") {
    syncGastosFromDOM();
    actualizarAyudaMeta();
  }
  if (paso === "plan") {
    syncGastosFromDOM();
    renderPlanEncuesta();
  }
  if (paso === "guardar") {
    syncGastosFromDOM();
    renderResumenFinal();
  }

  window.scrollTo({ top: 0 });
}

/* ---------- Ayudas visuales ---------- */

function simboloMoneda(codigo) {
  const m = MONEDAS.filter(function (x) { return x.codigo === codigo; })[0];
  return m && m.simbolo ? m.simbolo : "$";
}

function actualizarSimboloEncuesta() {
  const s = el("enc-simbolo");
  if (s) s.textContent = simboloMoneda(encuesta.moneda);
  const sm = el("enc-meta-simbolo");
  if (sm) sm.textContent = simboloMoneda(encuesta.moneda);
}

/* Cuánto queda después de los gastos (para el paso de la meta). */
function actualizarAyudaMeta() {
  const ayuda = el("enc-meta-ayuda");
  if (!ayuda) return;
  const ingreso = Number(encuesta.ingreso) || 0;
  const total = leerGastos().reduce(function (a, g) { return a + g.monto; }, 0);
  const sobrante = sobranteDe(ingreso, total);
  if (sobrante > 0.005) {
    ayuda.innerHTML = "Después de tus gastos te quedan <strong>" + dinero(encuesta.moneda, sobrante) +
      "</strong>. Eso lo destinamos a tu meta.";
  } else if (sobrante < -0.005) {
    ayuda.innerHTML = "⚠️ Tus gastos superan tu ingreso por <strong>" +
      dinero(encuesta.moneda, -sobrante) + "</strong>. Igual podés guardar y ajustarlo en la app.";
  } else {
    ayuda.textContent = "Tus gastos usan todo el ingreso: por ahora no queda nada para la meta.";
  }
}

/* Total en vivo del paso 3: gastos cargados y lo que queda para la meta.
   Se refresca al tipear cada monto y al entrar al paso. */
function refrescarResumenGastos() {
  const cont = el("enc-gastos-resumen");
  if (!cont) return;
  const ingreso = Number(encuesta.ingreso) || 0;
  const total = leerGastos().reduce(function (a, g) { return a + g.monto; }, 0);
  const sobrante = sobranteDe(ingreso, total);
  cont.innerHTML =
    '<div class="encuesta-resumen-fila"><span>Gastos cargados</span><strong>' +
      dinero(encuesta.moneda, total) + "</strong></div>" +
    '<div class="encuesta-resumen-fila encuesta-resumen-total"><span>' +
      (sobrante >= -0.005 ? "Para tu meta" : "Faltante") + "</span><strong>" +
      dinero(encuesta.moneda, Math.abs(sobrante)) + "</strong></div>";
}

/* ---------- Plan (paso 6) ---------- */

/* Perfil objetivo efectivo de la encuesta (UNICA fuente de verdad):
   si el usuario no tocó el paso "perfil" manda la meta; si lo tocó,
   manda su elección. La lógica vive en motor.js (probada). */
function perfilObjetivoEncuesta() {
  return perfilEfectivoEncuesta(encuesta.perfilTocado, encuesta.perfil, encuesta.metaTipo);
}

function configFinal() {
  const cfg = construirConfigDesdeEncuesta(datosEncuesta());
  const p = buscarPerfil(perfilObjetivoEncuesta());
  if (p) cfg.objetivo = p.id;
  return cfg;
}

function metaFinal() {
  const info = metaPorTipo(encuesta.metaTipo);
  return {
    tipo: encuesta.metaTipo,
    etiqueta: info ? info.etiqueta : "Mi meta",
    emoji: info ? info.emoji : "🎯",
    monto: Number(encuesta.metaMonto) || 0,
    meses: Number(encuesta.metaMeses) || 0,
    moneda: encuesta.moneda,
    guardado: new Date().toISOString(),
  };
}

function filaGrupoHTML(grupo, monto, ingreso) {
  const pct = ingreso > 0 ? (monto / ingreso) * 100 : 0;
  return '<div class="encuesta-grupo-fila">' +
    '<span class="chip chip-' + grupo + '" aria-hidden="true"></span>' +
    '<span class="encuesta-grupo-nombre">' + ETIQUETAS_GRUPO[grupo] + "</span>" +
    '<span class="encuesta-grupo-dato">' + fmtPct(pct) + " · " + dinero(encuesta.moneda, monto) + "</span>" +
  "</div>";
}

function textoMeses(meses) {
  if (meses === null) return "sin aporte mensual todavía";
  if (meses === 0) return "ya cubierto";
  return "≈ " + meses + (meses === 1 ? " mes" : " meses");
}

function renderPlanEncuesta() {
  const cont = el("enc-plan");
  if (!cont) return;

  const datos = datosEncuesta();
  const ingreso = Number(datos.ingreso) || 0;
  const previa = vistaPreviaEncuesta(datos, encuesta.cotizacion);
  const cfg = previa.cfg;
  const p = buscarPerfil(perfilObjetivoEncuesta());
  if (p) cfg.objetivo = p.id;
  const consejos = consejosConsejero(cfg, ingreso, encuesta.cotizacion);

  const totalGastos = previa.totalGastos;
  const sobrante = previa.sobrante;
  const porGrupo = previa.porGrupo;
  const meta = metaFinal();
  const meses = Number(meta.meses) || 0;
  const aporte = aporteNecesarioParaMeta(meta.monto, meses);
  const mesesEstimados = mesesParaMeta(meta.monto, sobrante > 0.005 ? sobrante : 0);
  // Sin monto en la meta no hay plazo que estimar (evita un "ya cubierto" falso).
  const tiempoTxt = meta.monto > 0 ? textoMeses(mesesEstimados) : "poné un monto para estimar el plazo";

  const perfilTxt = previa.perfilActual ? previa.perfilActual.emoji + " " + previa.perfilActual.nombre : "—";
  const objetivoTxt = p ? p.emoji + " " + p.nombre : "—";

  cont.innerHTML =
    '<div class="encuesta-resumen-fila"><span>Ingreso del mes</span><strong>' +
      dinero(encuesta.moneda, ingreso) + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Gastos cargados</span><strong>' +
      dinero(encuesta.moneda, totalGastos) + "</strong></div>" +
    '<div class="encuesta-resumen-fila encuesta-resumen-total"><span>' +
      (sobrante >= -0.005 ? "Para tu meta" : "Faltante") + "</span><strong>" +
      dinero(encuesta.moneda, Math.abs(sobrante)) + "</strong></div>" +
    '<div class="encuesta-bloque-grupos">' +
      GRUPO_ORDEN.map(function (g) { return filaGrupoHTML(g, porGrupo[g] || 0, ingreso); }).join("") +
    "</div>" +
    '<div class="encuesta-resumen-fila"><span>Perfil de hoy</span><strong>' + esc(perfilTxt) + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Tu objetivo</span><strong>' + esc(objetivoTxt) + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>' + esc(meta.emoji + " " + meta.etiqueta) + "</span><strong>" +
      (meta.monto > 0 ? dinero(encuesta.moneda, meta.monto) : "—") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Plazo propuesto</span><strong>' +
      (meses >= 1 ? meses + " meses" : "—") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Aporte mensual necesario</span><strong>' +
      (aporte > 0 ? dinero(encuesta.moneda, aporte) : "—") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Tiempo estimado con tu sobrante actual</span><strong>' +
      esc(tiempoTxt) + "</strong></div>";

  const contConsejos = el("enc-consejos");
  if (contConsejos) {
    contConsejos.innerHTML = consejos.length
      ? '<h3 class="titulo-seccion">🧭 Consejos para llegar</h3>' + consejos.map(function (s) {
          return '<div class="consejo consejo-' + s.tipo + '">' +
            (s.titulo ? '<span class="consejo-titulo">' + esc(s.titulo) + "</span>" : "") +
            '<span class="consejo-texto">' + s.texto + "</span>" +
          "</div>";
        }).join("")
      : "";
  }
}

/* ---------- Resumen final (paso 7) ---------- */

/* Nombre de la persona: el escrito en la encuesta o, si ya hay sesión,
   el que se guardó por fuera (gastamejor.nombre.v1). */
function nombreDisponibleEncuesta() {
  const escrito = String(encuesta.nombre || "").trim();
  if (escrito) return escrito;
  try {
    const guardado = localStorage.getItem("gastamejor.nombre.v1");
    if (guardado) return String(guardado).trim();
  } catch (_) {
    /* sin persistencia */
  }
  return "";
}

function renderResumenFinal() {
  const cont = el("enc-resumen-final");
  if (!cont) return;
  const datos = datosEncuesta();
  const ingreso = Number(datos.ingreso) || 0;
  const total = datos.gastos.reduce(function (a, g) { return a + g.monto; }, 0);
  const sobrante = sobranteDe(ingreso, total);
  const meta = metaFinal();
  const p = buscarPerfil(perfilObjetivoEncuesta());
  const meses = Number(meta.meses) || 0;
  const aporte = aporteNecesarioParaMeta(meta.monto, meses);

  const nombre = nombreDisponibleEncuesta();
  cont.innerHTML =
    (nombre ? '<div class="encuesta-resumen-fila"><span>Nombre</span><strong>' + esc(nombre) + "</strong></div>" : "") +
    '<div class="encuesta-resumen-fila"><span>Ingreso</span><strong>' + dinero(encuesta.moneda, ingreso) + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Gastos cargados</span><strong>' + dinero(encuesta.moneda, total) + "</strong></div>" +
    '<div class="encuesta-resumen-fila encuesta-resumen-total"><span>' +
      (sobrante >= -0.005 ? "Para tu meta" : "Faltante") + "</span><strong>" +
      dinero(encuesta.moneda, Math.abs(sobrante)) + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Objetivo</span><strong>' +
      esc(p ? p.emoji + " " + p.nombre : "—") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Meta</span><strong>' +
      esc(meta.emoji + " " + meta.etiqueta) + (meta.monto > 0 ? " · " + dinero(encuesta.moneda, meta.monto) : "") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Plazo propuesto</span><strong>' +
      (meses >= 1 ? meses + " meses" : "—") + "</strong></div>" +
    '<div class="encuesta-resumen-fila"><span>Aporte mensual necesario</span><strong>' +
      (aporte > 0 ? dinero(encuesta.moneda, aporte) : "—") + "</strong></div>";
}

/* ---------- Imagen PNG del plan ---------- */

const TIPOGRAFIA_ENC = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

function fuenteEnc(ctx, peso, tamano) {
  ctx.font = (peso ? peso + " " : "") + tamano + "px " + TIPOGRAFIA_ENC;
}

function textoEnc(ctx, str, x, y, opc) {
  opc = opc || {};
  fuenteEnc(ctx, opc.peso, opc.tamano || 16);
  ctx.fillStyle = opc.color || "#0f172a";
  ctx.textAlign = opc.align || "left";
  ctx.textBaseline = "middle";
  ctx.fillText(str, x, y);
}

function crearCanvasResumen() {
  const cfg = configFinal();
  const ingreso = Number(encuesta.ingreso) || 0;
  const moneda = encuesta.moneda;
  const reparto = calcularReparto(cfg, ingreso, encuesta.cotizacion);
  const porGrupo = calcularSubtotalesGrupo(reparto, cfg);
  const datos = datosEncuesta();
  const totalGastos = datos.gastos.reduce(function (a, g) { return a + (Number(g.monto) || 0); }, 0);
  const sobrante = sobranteDe(ingreso, totalGastos);
  const meta = metaFinal();
  const p = buscarPerfil(perfilObjetivoEncuesta());
  const meses = Number(meta.meses) || 0;
  const aporte = aporteNecesarioParaMeta(meta.monto, meses);

  const ESCALA = 2;
  const W = 540;
  const M = 40;
  const grupos = GRUPO_ORDEN.filter(function (g) { return (porGrupo[g] || 0) > 0.005; });
  let H = 132;                 // cabecera
  H += 34 * 4;                 // ingreso / gastos / meta / plazo
  H += 30;                     // barra de grupos
  H += grupos.length * 30;     // filas por grupo
  H += 34 * 3 + 20;            // perfil, meta, aporte
  H += 60;                     // pie

  const canvas = document.createElement("canvas");
  canvas.width = W * ESCALA;
  canvas.height = H * ESCALA;
  const ctx = canvas.getContext("2d");
  ctx.scale(ESCALA, ESCALA);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, W, H);

  let y = 46;
  ctx.fillStyle = "#10b981";
  ctx.beginPath();
  ctx.arc(W / 2 - 96, y - 4, 17, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#ffffff";
  fuenteEnc(ctx, 800, 20);
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText("$", W / 2 - 96, y - 3);
  textoEnc(ctx, "GastaMejor", W / 2 + 26, y - 4, { tamano: 30, peso: 800, align: "center" });
  textoEnc(ctx, "Mi plan de reparto", W / 2, y + 22, { tamano: 14, color: "#64748b", align: "center" });
  y += 56;

  function fila(etiqueta, valor, color) {
    textoEnc(ctx, etiqueta, M, y, { tamano: 17, color: "#64748b" });
    textoEnc(ctx, valor, W - M, y, { tamano: 20, peso: 800, align: "right", color: color || "#0f172a" });
    y += 34;
  }
  fila("Ingreso del mes", dinero(moneda, ingreso));
  fila("Gastos cargados", dinero(moneda, totalGastos));
  fila(sobrante >= -0.005 ? "Para tu meta" : "Faltante", dinero(moneda, Math.abs(sobrante)),
    sobrante < -0.005 ? "#dc2626" : "#047857");

  // Barra horizontal con la distribución por grupo.
  const barraX = M;
  const barraW = W - M * 2;
  const barraY = y + 4;
  const totalBase = ingreso > 0 ? ingreso : Math.max(1, reparto.asignado);
  let acc = 0;
  const colorGrupo = { necesidad: "#0284c7", deseo: "#d97706", ahorro: "#059669" };
  GRUPO_ORDEN.forEach(function (g) {
    const frac = Math.max(0, (porGrupo[g] || 0) / totalBase);
    if (frac <= 0) return;
    ctx.fillStyle = colorGrupo[g];
    ctx.fillRect(barraX + barraW * acc, barraY, Math.max(1, barraW * frac), 12);
    acc += frac;
  });
  y = barraY + 30;

  grupos.forEach(function (g) {
    const monto = porGrupo[g] || 0;
    const pct = ingreso > 0 ? (monto / ingreso) * 100 : 0;
    ctx.fillStyle = colorGrupo[g];
    ctx.beginPath();
    ctx.arc(M + 7, y, 7, 0, Math.PI * 2);
    ctx.fill();
    textoEnc(ctx, ETIQUETAS_GRUPO[g], M + 22, y, { tamano: 16, peso: 600 });
    textoEnc(ctx, fmtPct(pct) + " · " + dinero(moneda, monto), W - M, y,
      { tamano: 15, peso: 700, color: "#334155", align: "right" });
    y += 30;
  });

  y += 10;
  fila("Objetivo", p ? p.emoji + " " + p.nombre : "—");
  fila(meta.emoji + " " + meta.etiqueta, meta.monto > 0 ? dinero(moneda, meta.monto) : "—");
  fila("Plazo propuesto", meses >= 1 ? meses + " meses" : "—");
  fila("Aporte mensual necesario", aporte > 0 ? dinero(moneda, aporte) : "—");

  y += 14;
  ctx.strokeStyle = "#e2e8f0";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(M, y);
  ctx.lineTo(W - M, y);
  ctx.stroke();
  y += 26;
  textoEnc(ctx, "Hecho con GastaMejor", W / 2, y, { tamano: 13, color: "#94a3b8", align: "center" });

  return canvas;
}

function descargarBlobEnc(blob, nombre) {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre || "gastamejor-plan.png";
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
  setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
}

function exportarResumenPNG() {
  const canvas = crearCanvasResumen();
  canvas.toBlob(function (blob) {
    if (!blob) {
      encToast("No se pudo generar la imagen.");
      return;
    }
    descargarBlobEnc(blob, "gastamejor-plan.png");
    encToast("Imagen descargada ⬇");
  }, "image/png");
}

/* ---------- Guardar y abrir la app ---------- */

function mesActualClaveEncuesta() {
  const d = new Date();
  return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0");
}

/* Traslada el ingreso cargado en la encuesta a la app: al llegar a
   index.html el campo "Tu dinero de este mes" ya viene prellenado. */
function trasladarIngresoMes() {
  if (typeof guardarIngresoMes !== "function") return;
  guardarIngresoMes({
    mes: mesActualClaveEncuesta(),
    total: Number(encuesta.ingreso) || 0,
    moneda: encuesta.moneda,
    cantidad: 1,
  });
}

function guardarMesEncuesta(cfg) {
  const registro = construirRegistroHistorial(
    cfg,
    Number(encuesta.ingreso) || 0,
    mesActualClaveEncuesta(),
    encuesta.cotizacion
  );
  guardarMesHistorial(registro);
  return registro;
}

/* Guarda configuracion + meta + ingreso del mes + mes en el historial.
   Devuelve true si guardo (o false si falta completar algo: deja el
   paso con error visible). No navega: la navegacion la decide quien
   la llama ("Guardar y abrir la app" o el boton de guardar el mes). */
function guardarDatosEncuesta() {
  // Repasamos todos los pasos obligatorios antes de guardar.
  const pasos = pasosActivos();
  for (let i = 0; i < pasos.length - 1; i++) {
    const v = validarPaso(pasos[i]);
    if (!v.ok) {
      encuesta.paso = i;
      mostrarPaso();
      mostrarError(pasos[i], v.error);
      return false;
    }
  }

  const cfg = configFinal();
  if (!validarConfig(cfg)) {
    mostrarError("guardar", "Revisá los montos: falta completar algún dato.");
    return false;
  }

  guardarConfig(cfg);
  guardarMeta(metaFinal());
  guardarMesEncuesta(cfg);
  trasladarIngresoMes();

  if (encuesta.nombre && typeof window.gmGuardarNombre === "function") {
    window.gmGuardarNombre(encuesta.nombre);
    if (typeof window.gmActualizarSesion === "function") window.gmActualizarSesion();
  }

  // Ya hay config: el enlace "Volver a la app" deja de ser una trampa.
  mostrarSalidaEncuesta();
  return true;
}

/* Guardar y abrir la app (config + meta + mes + navegar). */
function guardarYEnviar() {
  if (!guardarDatosEncuesta()) return;
  encToast("¡Listo! Abriendo tu app…");
  location.href = "index.html";
}

/* Guardar el mes en el Historial sin salir de la encuesta. */
function guardarMesYQuedarse() {
  if (!guardarDatosEncuesta()) return;
  encToast("Mes guardado en tu historial ✔");
}

/* ---------- Eventos ---------- */

function iniciarEventosEncuesta() {
  document.querySelectorAll(".encuesta-nav").forEach(function (nav) {
    nav.addEventListener("click", function (e) {
      const boton = e.target.closest("[data-nav]");
      if (!boton) return;
      if (boton.dataset.nav === "anterior") irAnterior();
      else irSiguiente();
    });
  });

  const perfiles = el("enc-perfiles");
  if (perfiles) {
    perfiles.addEventListener("click", function (e) {
      const boton = e.target.closest("[data-perfil]");
      if (!boton) return;
      encuesta.perfil = boton.dataset.perfil;
      encuesta.perfilTocado = true;
      renderEncuestaPerfiles();
    });
  }

  const gastos = el("enc-gastos");
  if (gastos) {
    gastos.addEventListener("input", function (e) {
      if (e.target.dataset && e.target.dataset.gastoIdx !== undefined) {
        aplicarFormatoEncuesta(e.target);
        // No reconstruir DOM aquí para no perder foco; solo refrescar resumen
        refrescarResumenGastos();
      }
    });
    gastos.addEventListener("focusout", function (e) {
      if (e.target.dataset && e.target.dataset.gastoIdx !== undefined) {
        completarEncuesta(e.target);
        refrescarResumenGastos();
      }
    });
  }

  const agregar = el("enc-agregar-gasto");
  if (agregar) {
    agregar.addEventListener("click", function () {
      if (!encuesta.gastos) encuesta.gastos = [];
      syncGastosFromDOM();
      const nuevo = {
        id: "gasto-" + Date.now() + "-" + Math.random().toString(36).slice(2, 6),
        nombre: "Nueva categoría",
        grupo: "necesidad",
        monto: 0,
      };
      encuesta.gastos.push(nuevo);
      const cont = el("enc-gastos");
      if (cont) {
        // Agregar al bloque del mismo grupo si existe; si no, crear bloque
        const bloques = cont.querySelectorAll(".encuesta-grupo");
        let agregado = false;
        for (let i = bloques.length - 1; i >= 0; i--) {
          if (bloques[i].querySelector(".chip-" + nuevo.grupo)) {
            bloques[i].appendChild(renderFilaGasto(encuesta.gastos.length - 1, nuevo));
            agregado = true;
            break;
          }
        }
        if (!agregado) {
          const bloque = document.createElement("section");
          bloque.className = "encuesta-grupo";
          const titulo = document.createElement("h3");
          titulo.className = "encuesta-grupo-titulo";
          titulo.innerHTML = '<span class="chip chip-' + nuevo.grupo + '" aria-hidden="true"></span>' + ETIQUETAS_GRUPO[nuevo.grupo];
          bloque.appendChild(titulo);
          bloque.appendChild(renderFilaGasto(encuesta.gastos.length - 1, nuevo));
          cont.appendChild(bloque);
        }
        actualizarBotonesEliminar();
      } else {
        renderGastosLista();
      }
      refrescarResumenGastos();
      setTimeout(function () {
        const input = document.querySelector('[data-nombre-idx="' + (encuesta.gastos.length - 1) + '"]');
        if (input) input.focus();
      }, 0);
    });
  }

  if (gastos) {
    gastos.addEventListener("click", function (e) {
      const btn = e.target.closest(".btn-eliminar-categoria");
      if (!btn) return;
      const idx = parseInt(btn.dataset.elimIdx, 10);
      if (isNaN(idx)) return;
      syncGastosFromDOM();
      if (encuesta.gastos.length <= 1) {
        encToast("Debe quedar al menos 1 categoría.");
        return;
      }
      const fila = btn.closest(".encuesta-categoria");
      if (fila) {
        const bloque = fila.closest(".encuesta-grupo");
        fila.remove();
        // Si el bloque queda vacío, lo removemos
        if (bloque && bloque.querySelectorAll(".encuesta-categoria").length === 0) {
          bloque.remove();
        }
      }
      // Eliminar del array
      encuesta.gastos.splice(idx, 1);
      // Reindexar filas en el DOM para mantener coherencia
      reindexarFilasGastos();
      refrescarResumenGastos();
    });
    gastos.addEventListener("change", function (e) {
      if (e.target.classList && e.target.classList.contains("encuesta-gasto-grupo")) {
        const idx = parseInt(e.target.dataset.grupoIdx, 10);
        if (!isNaN(idx)) {
          syncGastosFromDOM();
          if (encuesta.gastos[idx]) encuesta.gastos[idx].grupo = e.target.value;
          // Re-renderizar lista para reagrupar por grupo sin perder valores
          renderGastosLista();
          refrescarResumenGastos();
        }
      }
    });
    gastos.addEventListener("input", function (e) {
      if (e.target.classList && e.target.classList.contains("encuesta-gasto-nombre")) {
        const idx = parseInt(e.target.dataset.nombreIdx, 10);
        if (!isNaN(idx)) {
          syncGastosFromDOM();
        }
      }
    });
  }

  const ingreso = el("enc-ingreso");
  if (ingreso) {
    ingreso.addEventListener("input", function () { aplicarFormatoEncuesta(this); });
    ingreso.addEventListener("blur", function () { completarEncuesta(this); });
  }

  const moneda = el("enc-moneda");
  if (moneda) {
    moneda.addEventListener("change", function () {
      encuesta.moneda = moneda.value;
      actualizarSimboloEncuesta();
    });
  }

  const metaMonto = el("enc-meta-monto");
  if (metaMonto) {
    metaMonto.addEventListener("input", function () { aplicarFormatoEncuesta(this); });
    metaMonto.addEventListener("blur", function () { completarEncuesta(this); });
  }

  const metaTipo = el("enc-meta-tipo");
  if (metaTipo) {
    metaTipo.addEventListener("change", function () {
      if (!encuesta.perfilTocado) {
        encuesta.perfil = perfilEfectivoEncuesta(false, encuesta.perfil, metaTipo.value);
      }
    });
  }

  const btnPng = el("enc-png");
  if (btnPng) btnPng.addEventListener("click", exportarResumenPNG);

  const btnGuardar = el("enc-guardar");
  if (btnGuardar) {
    btnGuardar.addEventListener("click", function () {
      leerPasoActual();
      guardarYEnviar();
    });
  }

  const btnGuardarMes = el("enc-guardar-mes");
  if (btnGuardarMes) {
    btnGuardarMes.addEventListener("click", function () {
      leerPasoActual();
      guardarMesYQuedarse();
    });
  }
}

/* ---------- Arranque ---------- */

function iniciarEncuesta() {
  encuesta.cotizacion = typeof cotizacionGuardada === "function" ? cotizacionGuardada("bolsa") : null;
  encuesta.moneda = "ARS";
  encuesta.metaTipo = "ahorrar";
  encuesta.metaMeses = 6;
  encuesta.perfil = "equilibrado";
  encuesta.perfilTocado = false;

  construirSelectsEncuesta();
  // Inicializar array vacío para que renderGastosLista use defaults
  encuesta.gastos = [];
  renderGastosLista();
  renderEncuestaPerfiles();
  iniciarEventosEncuesta();
  actualizarSimboloEncuesta();
  mostrarSalidaEncuesta();

  if (!pasosActivos().length) return;
  mostrarPaso();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", iniciarEncuesta);
} else {
  iniciarEncuesta();
}
