/* GastaMejor - motor.js
   ------------------------------------------------------------
   MOTOR PURO: no toca el DOM, no usa `estado` ni `localStorage`.
   Todas las funciones reciben lo que necesitan por parametro y la
   cotizacion del dolar es SIEMPRE un 3er argumento opcional y
   explicito: si no viene, no se lee ningun estado global (las
   categorias en USD quedan en 0).

   Lo usan app.js (la app), encuesta.js (la encuesta de ingreso) y
   las pruebas (pruebas.js). Depende solo de storage.js
   (PERFILES, CATEGORIAS_POR_DEFECTO, MONEDAS, validarConfig).
   ------------------------------------------------------------ */
"use strict";

/* ============================================================
   Constantes
   ============================================================ */

const GRUPOS = ["necesidad", "deseo", "ahorro"];

const ETIQUETAS_GRUPO = {
  necesidad: "Necesidades",
  deseo: "Deseos",
  ahorro: "Ahorro",
};

/* Ideal 50/30/20: al que apunta el plan de evolucion. */
const IDEAL_GRUPO = { necesidad: 50, deseo: 30, ahorro: 20 };

/* ============================================================
   Utilidades (formato de texto y de montos)
   ============================================================ */

function esc(texto) {
  return String(texto).replace(/[&<>"']/g, function (ch) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
  });
}

function dinero(moneda, cantidad) {
  try {
    const locale = moneda === "ARS" ? "es-AR" : "es";
    return new Intl.NumberFormat(locale, { style: "currency", currency: moneda }).format(cantidad);
  } catch (_) {
    return "$ " + Number(cantidad).toFixed(2);
  }
}

/* Formato compacto, solo para el calendario del Historial.
   Ej.: 1.2M · 850K · 1.5K · 850. Sin simbolo de moneda. */
function dineroCorto(cantidad) {
  const n = Number(cantidad);
  if (!isFinite(n)) return "—";
  const abs = Math.abs(n);
  const signo = n < 0 ? "-" : "";
  const unDecimal = function (v) {
    return (Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, "");
  };
  if (abs >= 1000000) {
    return signo + unDecimal(abs / 1000000) + "M";
  }
  if (abs >= 1000) {
    const miles = abs / 1000;
    let v = miles >= 100 ? String(Math.round(miles)) : unDecimal(miles);
    if (Number(v) >= 1000) return signo + "1M"; // 999.999 -> 1M (no 1000K)
    return signo + v + "K";
  }
  return signo + String(Math.round(abs));
}

function fmtPct(p) {
  const n = Number(p === undefined || p === null ? 0 : p);
  return (Math.round(n * 10) / 10).toLocaleString("es") + "%";
}

/* ---------- Formato de montos (1.000.000,00) ----------
   Los puntos son separador de miles y la coma es decimal, como se
   escriben los numeros en Argentina. */

/* Separa lo escrito en parte entera y decimal (o null si no hay decimal). */
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

/* Formatea en vivo mientras se escribe: 1.000.000,00 */
function formatearEntradaMonto(texto) {
  const a = analizarEntrada(texto);
  const entero = a.entero.replace(/^0+(?=\d)/, "");
  const agrupado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  if (a.dec === null) return agrupado;
  return (agrupado === "" ? "0" : agrupado) + "," + a.dec;
}

/* Numero a partir de lo escrito. null si no hay ningun digito. */
function parsearEntradaMonto(texto) {
  const a = analizarEntrada(texto);
  if (a.entero === "" && (a.dec === null || a.dec === "")) return null;
  const n = Number((a.entero || "0") + "." + (a.dec || "0"));
  return isFinite(n) ? n : null;
}

/* Numero formateado con separador de miles y decimales fijos. */
function formatearNumeroMonto(n, decimales) {
  const dec = decimales === undefined ? 2 : decimales;
  const negativo = n < 0;
  const partes = Math.abs(Number(n) || 0).toFixed(dec).split(".");
  const entero = partes[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return (negativo ? "-" : "") + entero + (dec > 0 ? "," + partes[1] : "");
}

/* ---------- Montos escritos a mano ----------
   Un monto valido es SIEMPRE positivo: el signo menos no tiene lugar.
   OJO: parsearEntradaMonto ignora el "-", asi que "-500" se leeria como
   500; el signo hay que mirarlo en el TEXTO CRUDO, no en el numero. */

const MENSAJE_MONTO_NEGATIVO = "Escribí un monto mayor a cero, sin el signo menos.";

/* ¿El texto escrito trae un signo menos? PURO. */
function tieneSignoNegativo(texto) {
  return /-/.test(String(texto === undefined || texto === null ? "" : texto));
}

/* Valida lo escrito en un campo de monto (misma forma que el resto de
   las validaciones: { ok, error }). Rechaza el signo menos. PURO. */
function validarMontoEscrito(texto) {
  if (tieneSignoNegativo(texto)) return { ok: false, error: MENSAJE_MONTO_NEGATIVO };
  return { ok: true, error: "" };
}

/* ============================================================
   Cotizacion del dolar (ahorro en USD)
   ============================================================ */

/* Tasa a partir de una cotizacion explicita (0 si no hay). */
function tasaDeCotizacion(cotizacion) {
  return cotizacion && Number(cotizacion.valor) > 0 ? Number(cotizacion.valor) : 0;
}

/* Una categoria se carga en dolares solo si: ingreso en ARS, es fija y del grupo Ahorro. */
function categoriaEnUSD(cfg, c) {
  if (!cfg || cfg.moneda !== "ARS") return false;
  return c.modo === "fijo" && (c.grupo || "necesidad") === "ahorro" && c.monedaMonto === "USD";
}

function puedeCargarUSD(cfg, c) {
  if (!cfg || cfg.moneda !== "ARS") return false;
  return c.modo === "fijo" && (c.grupo || "necesidad") === "ahorro";
}

function hayAhorroUSD(cfg) {
  return !!cfg && cfg.categorias.some(function (c) { return categoriaEnUSD(cfg, c); });
}

/* ============================================================
   Logica de reparto
   ------------------------------------------------------------
   Regla: los montos fijos se reservan PRIMERO (son los gastos
   obligatorios). El dinero que queda se reparte entre las
   categorias porcentuales en proporcion a su %, se estira para
   usar todo el ingreso. Asi el total nunca supera el 100%
   (salvo que los fijos solos superen el ingreso).

   `cotizacion` es opcional y explicito: si no viene, las
   categorias en USD valen 0 (NO se lee ningun estado global).
   ============================================================ */

function calcularReparto(cfg, ingreso, cotizacion) {
  const tasa = tasaDeCotizacion(cotizacion);
  const valorDe = function (c) {
    const monto = Number(c.monto) || 0;
    return categoriaEnUSD(cfg, c) ? monto * tasa : monto;
  };
  const sumaFijos = cfg.categorias.reduce(function (acum, c) {
    return c.modo === "fijo" ? acum + valorDe(c) : acum;
  }, 0);
  const sumaPct = cfg.categorias.reduce(function (acum, c) {
    return c.modo === "porcentaje" ? acum + (Number(c.porcentaje) || 0) : acum;
  }, 0);
  const disponible = ingreso - sumaFijos;

  const montoCategoria = cfg.categorias.map(function (c) {
    if (c.modo === "fijo") return valorDe(c);
    if (disponible <= 0 || sumaPct <= 0) return 0;
    return disponible * ((Number(c.porcentaje) || 0) / sumaPct);
  });

  const asignado = montoCategoria.reduce(function (a, b) { return a + b; }, 0);
  return {
    montoCategoria: montoCategoria,
    sumaFijos: sumaFijos,
    sumaPct: sumaPct,
    disponible: disponible,
    asignado: asignado,
    restante: ingreso - asignado,
    pctTotal: ingreso > 0 ? (asignado / ingreso) * 100 : 0,
  };
}

/* Suma de montos por grupo. */
function calcularSubtotalesGrupo(reparto, cfg) {
  const porGrupo = { necesidad: 0, deseo: 0, ahorro: 0 };
  cfg.categorias.forEach(function (c, i) {
    porGrupo[c.grupo || "necesidad"] += reparto.montoCategoria[i];
  });
  return porGrupo;
}

/* ============================================================
   Consejero: consejos para llegar al objetivo
   ------------------------------------------------------------
   Compara el reparto real de cada grupo con el perfil objetivo
   elegido y sugiere, categoria por categoria, donde y como
   recortar. Los tips salen del nombre de la categoria (palabras
   clave), asi que funcionan aunque la categoria sea personalizada.
   ============================================================ */

const CONSEJOS_CATEGORIA = [
  { claves: ["alquiler", "vivienda", "expensas", "hipoteca", "departamento", "casa", "terreno"],
    accion: "negociá el alquiler o las expensas, compartí gastos con alguien o evaluá mudarte a algo más chico." },
  { claves: ["combustible", "nafta", "auto", "coche", "seguro", "patente", "estacionamiento", "peaje", "moto"],
    accion: "usá más transporte público, compartí viajes o combiná días de home office para no usar tanto el vehículo." },
  { claves: ["comida", "super", "supermercado", "almacen", "mercado", "verduleria", "carniceria", "almacén"],
    accion: "planificá el menú semanal, comprá con lista y aprovechá las ofertas; cociná más en casa." },
  { claves: ["delivery", "cafe", "café", "restaurante", "bar", "pedidos", "take away"],
    accion: "bajá los pedidos a domicilio y los cafés fuera de casa; reservalos para ocasiones especiales." },
  { claves: ["suscripcion", "suscripción", "streaming", "netflix", "spotify", "cable", "gimnasio", "app"],
    accion: "revisá cuáles usás de verdad y cancelá las que no; compartí cuentas familiares." },
  { claves: ["deuda", "tarjeta", "prestamo", "préstamo", "credito", "crédito", "cuota"],
    accion: "priorizá las deudas de mayor interés y evitá nuevas cuotas mientras las pagás." },
  { claves: ["ocio", "entretenimiento", "juego", "fiesta", "salida", "salidas"],
    accion: "buscá planes gratuitos o más baratos y ponete un tope semanal." },
  { claves: ["transporte", "colectivo", "sube", "tren", "subte", "taxi", "remis"],
    accion: "combiná el abono mensual y caminá o pedaleá los tramos cortos." },
  { claves: ["ropa", "compras", "calzado", "tecnologia", "tecnología", "electronica", "electrónica"],
    accion: "esperá las ofertas, comprá de segunda mano o repará antes de reemplazar." },
  { claves: ["viaje", "vacacion", "vacación", "turismo"],
    accion: "viajá fuera de temporada, en cuotas sin interés o elegí destinos más cercanos." },
  { claves: ["servicios", "luz", "gas", "agua", "internet", "telefono", "teléfono", "celular"],
    accion: "revisá el consumo, pasá a planes más bajos y pagá a tiempo para evitar recargos." },
  { claves: ["salud", "obra social", "prepaga", "farmacia", "medico", "médico"],
    accion: "compará planes, usá genéricos cuando puedas y aprovechá los reintegros." },
];

/* Normaliza para comparar (minusculas, sin acentos). */
function normalizarTexto(texto) {
  return String(texto || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function accionParaCategoria(nombre) {
  const n = normalizarTexto(nombre);
  for (let i = 0; i < CONSEJOS_CATEGORIA.length; i++) {
    const regla = CONSEJOS_CATEGORIA[i];
    for (let j = 0; j < regla.claves.length; j++) {
      if (n.indexOf(normalizarTexto(regla.claves[j])) !== -1) return regla.accion;
    }
  }
  return "revisá este gasto y buscá una alternativa más económica o negociá el precio.";
}

/* ============================================================
   Perfiles de reparto
   ============================================================ */

function buscarPerfil(id) {
  return PERFILES.filter(function (p) { return p.id === id; })[0] || null;
}

/* Suma de porcentajes por grupo (solo categorias porcentuales). */
function pesosNominalesGrupo(cfg) {
  const r = { necesidad: 0, deseo: 0, ahorro: 0 };
  cfg.categorias.forEach(function (c) {
    if (c.modo === "porcentaje") r[c.grupo || "necesidad"] += Number(c.porcentaje) || 0;
  });
  return r;
}

/* Distribucion real por grupo (sobre el ingreso). Si no hay ingreso,
   usa los porcentajes nominales normalizados. */
function distribucionActualGrupo(cfg, ingreso, cotizacion) {
  if (ingreso > 0) {
    const reparto = calcularReparto(cfg, ingreso, cotizacion);
    const g = calcularSubtotalesGrupo(reparto, cfg);
    return {
      necesidad: (g.necesidad / ingreso) * 100,
      deseo: (g.deseo / ingreso) * 100,
      ahorro: (g.ahorro / ingreso) * 100,
    };
  }
  const nom = pesosNominalesGrupo(cfg);
  const total = nom.necesidad + nom.deseo + nom.ahorro;
  return {
    necesidad: total > 0 ? (nom.necesidad / total) * 100 : 0,
    deseo: total > 0 ? (nom.deseo / total) * 100 : 0,
    ahorro: total > 0 ? (nom.ahorro / total) * 100 : 0,
  };
}

/* Clona una configuracion (y sus categorias) para no mutar la original. */
function clonarConfig(cfg) {
  return Object.assign({}, cfg, {
    planBase: cfg.planBase ? Object.assign({}, cfg.planBase) : null,
    categorias: (cfg.categorias || []).map(function (c) { return Object.assign({}, c); }),
  });
}

/* Reparte un objetivo (pesos por grupo) entre las categorias porcentuales de
   cada grupo. Las categorias fijas no se tocan. Muta el cfg recibido y lo
   devuelve (nucleo puro: sin estado global). */
function repartirPesosGrupo(cfg, objetivos) {
  GRUPOS.forEach(function (grupo) {
    const cats = cfg.categorias.filter(function (c) {
      return (c.grupo || "necesidad") === grupo && c.modo === "porcentaje";
    });
    if (!cats.length) return;
    const objetivo = Math.max(0, Number(objetivos[grupo]) || 0);
    const sumaActual = cats.reduce(function (a, c) { return a + (Number(c.porcentaje) || 0); }, 0);
    let acumulado = 0;
    cats.forEach(function (c, i) {
      let v;
      if (i === cats.length - 1) {
        v = objetivo - acumulado;
      } else {
        v = sumaActual > 0
          ? (objetivo * (Number(c.porcentaje) || 0)) / sumaActual
          : objetivo / cats.length;
      }
      v = Math.max(0, Math.round(v * 10) / 10);
      c.porcentaje = v;
      acumulado += v;
    });
  });
  return cfg;
}

/* Perfil mas parecido a la distribucion actual. */
function perfilActual(cfg, ingreso, cotizacion) {
  const dist = distribucionActualGrupo(cfg, ingreso, cotizacion);
  let mejor = null;
  let mejorDist = Infinity;
  PERFILES.forEach(function (p) {
    const d =
      Math.pow(dist.necesidad - p.grupos.necesidad, 2) +
      Math.pow(dist.deseo - p.grupos.deseo, 2) +
      Math.pow(dist.ahorro - p.grupos.ahorro, 2);
    if (d < mejorDist) { mejorDist = d; mejor = p; }
  });
  return mejor;
}

/* Suma los montos fijos (en pesos) de cada grupo. */
function fijosPorGrupo(cfg, cotizacion) {
  return calcularSubtotalesGrupo(calcularReparto(cfg, 0, cotizacion), cfg);
}

/* Punto de partida del plan (o la distribución actual si no hay plan activo). */
function planBaseActual(cfg, ingreso, meses, cotizacion) {
  const base = cfg.planBase;
  const paso = Math.round(Number(cfg.planPaso) || 0);
  const valido = base && typeof base === "object" &&
    GRUPOS.every(function (g) { return isFinite(Number(base[g])); }) &&
    paso >= 0 && paso <= meses;
  if (!valido) {
    return { base: distribucionActualGrupo(cfg, ingreso, cotizacion), paso: 0 };
  }
  return { base: base, paso: paso };
}

/* Reparte un objetivo (% REAL del ingreso por grupo) entre las categorías
   porcentuales, teniendo en cuenta los montos fijos ya reservados.
   Convierte el objetivo real a pesos "porcentuales" y normaliza a 100,
   así los % siguen siendo valores 0..100 como pide la app. */
function repartirObjetivoReal(cfg, objetivosPct, ingreso, cotizacion) {
  if (!(ingreso > 0)) {
    return repartirPesosGrupo(cfg, objetivosPct);
  }
  const fijos = fijosPorGrupo(cfg, cotizacion);
  const necesario = {};
  let totalNec = 0;
  GRUPOS.forEach(function (g) {
    necesario[g] = Math.max(0, ((Number(objetivosPct[g]) || 0) / 100) * ingreso - fijos[g]);
    totalNec += necesario[g];
  });
  if (totalNec <= 0) return cfg;

  GRUPOS.forEach(function (g) {
    const cats = cfg.categorias.filter(function (c) {
      return (c.grupo || "necesidad") === g && c.modo === "porcentaje";
    });
    if (!cats.length) return;
    const peso = (necesario[g] / totalNec) * 100; // % normalizado (0..100)
    const sumaActual = cats.reduce(function (a, c) { return a + (Number(c.porcentaje) || 0); }, 0);
    let acum = 0;
    cats.forEach(function (c, i) {
      let v;
      if (i === cats.length - 1) {
        v = peso - acum;
      } else {
        v = sumaActual > 0
          ? (peso * (Number(c.porcentaje) || 0)) / sumaActual
          : peso / cats.length;
      }
      v = Math.max(0, Math.round(v * 10) / 10);
      c.porcentaje = v;
      acum += v;
    });
  });
  return cfg;
}

/* Devuelve una lista de consejos para acercar el reparto al objetivo. */
function consejosConsejero(cfg, ingreso, cotizacion) {
  const moneda = cfg.moneda;
  const objetivo = buscarPerfil(cfg && cfg.objetivo) || buscarPerfil("equilibrado");
  const salida = [];

  if (ingreso <= 0) {
    salida.push({
      tipo: "aviso",
      titulo: "Falta tu ingreso",
      texto: "Escribí tu dinero del mes y el consejero te dirá cómo acercarte a <strong>" +
        esc(objetivo.nombre) + "</strong>.",
    });
    return salida;
  }

  const reparto = calcularReparto(cfg, ingreso, cotizacion);
  if (reparto.restante < -0.01) {
    salida.push({
      tipo: "error",
      titulo: "Te pasaste del ingreso",
      texto: "Tus gastos fijos superan tu ingreso por <strong>" + dinero(moneda, -reparto.restante) +
        "</strong>. Bajá esos montos o aumentá tu ingreso antes de buscar el objetivo.",
    });
    return salida;
  }

  const dist = distribucionActualGrupo(cfg, ingreso, cotizacion);
  const porGrupo = calcularSubtotalesGrupo(reparto, cfg);
  const actual = perfilActual(cfg, ingreso, cotizacion);

  salida.push({
    tipo: "objetivo",
    titulo: "Objetivo: " + objetivo.emoji + " " + objetivo.nombre,
    texto: "Hoy estás en <strong>" + esc(actual ? actual.emoji + " " + actual.nombre : "—") +
      "</strong>. Para llegar al objetivo, mirá estos consejos:",
  });

  if (reparto.restante > 0.01) {
    salida.push({
      tipo: "aviso",
      titulo: "Sin designar",
      texto: "Te quedan <strong>" + dinero(moneda, reparto.restante) +
        "</strong> sin repartir. Destinalos al ahorro para acercarte al objetivo.",
    });
  }

  let huboRecorte = false;

  GRUPOS.forEach(function (grupo) {
    const objetivoPct = objetivo.grupos[grupo];
    const brecha = objetivoPct - dist[grupo];

    // En ahorro nunca se recorta: ahorrar de más nunca es un problema.
    if (grupo === "ahorro") {
      if (brecha > 1) {
        const falta = (brecha / 100) * ingreso;
        salida.push({
          tipo: "ahorro",
          titulo: "Ahorrá más",
          texto: "Estás en <strong>" + fmtPct(dist.ahorro) + "</strong> de ahorro y tu objetivo es <strong>" +
            fmtPct(objetivoPct) + "</strong>. Te faltan <strong>" + dinero(moneda, falta) +
            "</strong>: automatizá una transferencia al ahorro apenas cobrás.",
        });
      }
      return;
    }

    if (brecha < -1) {
      // El grupo gasta más de lo que pide el objetivo: hay que recortar.
      const recorte = (-brecha / 100) * ingreso;
      const cats = cfg.categorias
        .map(function (c, i) { return { c: c, monto: reparto.montoCategoria[i] }; })
        .filter(function (x) { return (x.c.grupo || "necesidad") === grupo; })
        .sort(function (a, b) { return b.monto - a.monto; });
      const sumaGrupo = porGrupo[grupo] || cats.reduce(function (a, x) { return a + x.monto; }, 0);

      salida.push({
        tipo: "grupo",
        titulo: ETIQUETAS_GRUPO[grupo] + " · " + fmtPct(dist[grupo]) + " → " + fmtPct(objetivoPct),
        texto: "Gastás <strong>" + dinero(moneda, sumaGrupo) + "</strong> y tu objetivo es <strong>" +
          dinero(moneda, (objetivoPct / 100) * ingreso) + "</strong>. Recortá unos <strong>" +
          dinero(moneda, recorte) + "</strong>:",
      });

      cats.slice(0, 3).forEach(function (x) {
        const corte = sumaGrupo > 0 ? recorte * (x.monto / sumaGrupo) : 0;
        if (corte < 1) return;
        huboRecorte = true;
        salida.push({
          tipo: "recorte",
          titulo: x.c.nombre + " · " + fmtPct((x.monto / ingreso) * 100),
          texto: "Gastás <strong>" + dinero(moneda, x.monto) + "</strong>. Bajá unos <strong>" +
            dinero(moneda, corte) + "</strong>: " + accionParaCategoria(x.c.nombre),
        });
      });
    }
  });

  if (!huboRecorte && reparto.restante <= 0.01) {
    const faltaAhorro = objetivo.grupos.ahorro - dist.ahorro;
    if (Math.abs(faltaAhorro) <= 1) {
      salida.push({
        tipo: "ok",
        titulo: "¡Objetivo cumplido!",
        texto: "Tu reparto ya está en línea con <strong>" + objetivo.emoji + " " + esc(objetivo.nombre) +
          "</strong>. Mantenelo y sumá el excedente al ahorro 💪",
      });
    } else if (faltaAhorro < -1) {
      salida.push({
        tipo: "ok",
        titulo: "Vas mejor que el objetivo",
        texto: "Ahorrás <strong>" + fmtPct(dist.ahorro) + "</strong>, más que el objetivo <strong>" +
          objetivo.emoji + " " + esc(objetivo.nombre) + " (" + fmtPct(objetivo.grupos.ahorro) +
          ")</strong>. No hay recortes que hacer: mantené el hábito 💪",
      });
    }
  }

  return salida;
}

/* ============================================================
   Historial: registro de un mes (nucleo puro)
   ============================================================ */

function construirRegistroHistorial(cfg, ingreso, mes, cotizacion) {
  const monto = Number(ingreso) || 0;
  const reparto = calcularReparto(cfg, monto, cotizacion);
  const g = calcularSubtotalesGrupo(reparto, cfg);
  const pctGrupos = {};
  GRUPOS.forEach(function (grupo) { pctGrupos[grupo] = monto > 0 ? (g[grupo] / monto) * 100 : 0; });
  const p = perfilActual(cfg, monto, cotizacion);

  return {
    mes: mes,
    guardado: new Date().toISOString(),
    moneda: cfg.moneda,
    monto: monto,
    grupos: { necesidad: g.necesidad, deseo: g.deseo, ahorro: g.ahorro },
    pctGrupos: pctGrupos,
    categorias: cfg.categorias.map(function (c, i) {
      return { nombre: c.nombre, grupo: c.grupo || "necesidad", monto: reparto.montoCategoria[i] };
    }),
    perfil: p ? p.id : null,
  };
}

/* ============================================================
   Encuesta obligatoria de ingreso
   ------------------------------------------------------------
   Convierte las respuestas de la encuesta (nombre, ingreso,
   gastos fijos por categoria y una meta) en una configuracion
   lista para guardar y usar en la app.
   ============================================================ */

const METAS = [
  { tipo: "vacaciones", etiqueta: "Vacaciones",         emoji: "✈️", grupoSobrante: "ahorro",    perfil: "conservador" },
  { tipo: "comprar",    etiqueta: "Comprar algo",        emoji: "🛍️", grupoSobrante: "ahorro",    perfil: "conservador" },
  { tipo: "estudiar",   etiqueta: "Estudiar",            emoji: "🎓", grupoSobrante: "ahorro",    perfil: "conservador" },
  { tipo: "ahorrar",    etiqueta: "Ahorrar",             emoji: "💰", grupoSobrante: "ahorro",    perfil: "cauto" },
  { tipo: "fondo",      etiqueta: "Fondo de emergencia", emoji: "🛟", grupoSobrante: "ahorro",    perfil: "cauto" },
  { tipo: "deudas",     etiqueta: "Salir de deudas",     emoji: "💳", grupoSobrante: "necesidad", perfil: "equilibrado" },
  { tipo: "otro",       etiqueta: "Otro",                emoji: "🎯", grupoSobrante: "ahorro",    perfil: "equilibrado" },
];

function metaPorTipo(tipo) {
  return METAS.filter(function (m) { return m.tipo === tipo; })[0] || null;
}

/* Perfil objetivo sugerido por la meta. Nunca "gastador" (no queremos
   arrancar sugiriendo gastar mas): default "equilibrado". */
function perfilObjetivoParaMeta(tipo) {
  const m = metaPorTipo(tipo);
  const id = m ? m.perfil : "equilibrado";
  return id === "gastador" ? "equilibrado" : id;
}

/* Perfil EFECTIVO de la encuesta: la unica fuente de verdad del objetivo.
   - Si el usuario NO toco el paso "perfil", vale lo que mapea su meta.
   - Si lo toco, vale su eleccion (siempre que sea un perfil existente).
   - Nunca devuelve "gastador" (y si algo no cuadra, cae al mapeo de la meta).
   PURO: no lee estado global ni el DOM. */
function perfilEfectivoEncuesta(perfilTocado, perfil, metaTipo) {
  const porMeta = perfilObjetivoParaMeta(metaTipo);
  if (!perfilTocado) return porMeta;
  const p = buscarPerfil(perfil);
  if (!p || p.id === "gastador") return porMeta;
  return p.id;
}

/* Grupo que recibe el dinero que sobra despues de cubrir los gastos. */
function grupoSobranteParaMeta(tipo) {
  const m = metaPorTipo(tipo);
  return m ? m.grupoSobrante : "ahorro";
}

function sobranteDe(ingreso, totalGastos) {
  return (Number(ingreso) || 0) - (Number(totalGastos) || 0);
}

/* Cuantos meses hacen falta para juntar el objetivo con ese aporte mensual.
   `null` si no hay aporte; 0 si el objetivo ya esta cubierto. */
function aporteNecesarioParaMeta(monto, meses) {
  const m = Number(monto) || 0;
  const me = Number(meses) || 0;
  if (m <= 0 || me < 1) return 0;
  return m / me;
}

function mesesParaMeta(montoObjetivo, aporteMensual) {
  const aporte = Number(aporteMensual) || 0;
  if (aporte <= 0) return null;
  const objetivo = Number(montoObjetivo) || 0;
  if (objetivo <= 0) return 0;
  return Math.max(1, Math.ceil(objetivo / aporte));
}

/* Coloca el sobrante en la meta elegida. PURO: clona cfg y cfg.categorias
   (no muta el original) y devuelve { cfg, grupo, categoriaId, monto }. */
function repartirSobrante(cfg, sobrante, meta) {
  const clon = clonarConfig(cfg);
  const monto = Number(sobrante) || 0;
  if (monto <= 0.005) {
    return { cfg: clon, grupo: null, categoriaId: null, monto: 0 };
  }

  const grupo = grupoSobranteParaMeta(meta && meta.tipo);
  const idPreferido = grupo === "ahorro" ? "ahorro" : grupo === "necesidad" ? "deudas" : null;

  let cat = null;
  if (idPreferido) {
    cat = clon.categorias.filter(function (c) {
      return c.id === idPreferido && (c.grupo || "necesidad") === grupo && c.modo === "fijo";
    })[0] || null;
  }

  if (cat) {
    cat.porcentaje = 0;
    cat.monto = (Number(cat.monto) || 0) + monto;
    return { cfg: clon, grupo: grupo, categoriaId: cat.id, monto: monto };
  }

  const nueva = {
    id: "meta_" + grupo,
    nombre: grupo === "ahorro" ? "Ahorro para la meta" : "Pago de deudas",
    grupo: grupo,
    modo: "fijo",
    porcentaje: 0,
    monto: monto,
    monedaMonto: "ARS",
  };
  clon.categorias.push(nueva);
  return { cfg: clon, grupo: grupo, categoriaId: nueva.id, monto: monto };
}

/* ---------- Validaciones de la encuesta ----------
   Todas devuelven { ok: boolean, error: string }.
   El error es un mensaje claro, listo para mostrar en pantalla. */

function validarNombre(nombre) {
  const n = String(nombre === undefined || nombre === null ? "" : nombre).trim();
  if (n === "") return { ok: false, error: "Escribí tu nombre para continuar." };
  return { ok: true, error: "" };
}

function validarIngreso(ingreso, moneda) {
  const n = Number(ingreso);
  if (ingreso === "" || ingreso === null || !isFinite(n) || n <= 0) {
    return { ok: false, error: "Escribí cuánto dinero tenés este mes (un monto mayor a cero)." };
  }
  if (moneda && Array.isArray(MONEDAS) &&
      !MONEDAS.some(function (m) { return m.codigo === moneda; })) {
    return { ok: false, error: "Elegí una moneda válida." };
  }
  return { ok: true, error: "" };
}

function validarGastos(gastos) {
  if (!Array.isArray(gastos) || gastos.length === 0) {
    return { ok: false, error: "Cargá al menos un gasto." };
  }
  let total = 0;
  for (let i = 0; i < gastos.length; i++) {
    const monto = Number(gastos[i] && gastos[i].monto);
    if (!isFinite(monto) || monto < 0) {
      return { ok: false, error: "Los montos de los gastos deben ser números mayores o iguales a cero." };
    }
    total += monto;
  }
  if (total <= 0) {
    return { ok: false, error: "Cargá el monto de por lo menos un gasto (mayor a cero)." };
  }
  return { ok: true, error: "" };
}

function validarMeta(meta) {
  if (!meta || typeof meta !== "object") {
    return { ok: false, error: "Elegí tu meta." };
  }
  const m = metaPorTipo(meta.tipo);
  if (!m) return { ok: false, error: "Elegí una meta de la lista." };
  const monto = Number(meta.monto);
  if (!isFinite(monto) || monto < 0) {
    return { ok: false, error: "El monto de la meta debe ser un número mayor o igual a cero." };
  }
  const meses = Number(meta.meses);
  if (!isFinite(meses) || meses < 1 || Math.round(meses) !== meses) {
    return { ok: false, error: "Elegí un plazo en meses (1 o más)." };
  }
  if (meses > 120) {
    return { ok: false, error: "El plazo máximo es 120 meses (10 años)." };
  }
  return { ok: true, error: "" };
}

/* ---------- Construccion de la configuracion ---------- */

function construirConfigDesdeEncuesta(datos) {
  datos = datos || {};
  const meta = datos.meta || null;
  const gastos = Array.isArray(datos.gastos) ? datos.gastos : [];

  const cfg = {
    version: 3,
    moneda: datos.moneda || "ARS",
    dolarTipo: "bolsa",
    objetivo: perfilObjetivoParaMeta(meta && meta.tipo),
    planBase: null,
    planPaso: 0,
    categorias: gastos.map(function (g) {
      return {
        id: g.id,
        nombre: g.nombre,
        grupo: g.grupo,
        modo: "fijo",
        porcentaje: 0,
        monto: Number(g.monto) || 0,
        monedaMonto: "ARS",
      };
    }),
  };

  const total = gastos.reduce(function (a, g) { return a + (Number(g.monto) || 0); }, 0);
  return repartirSobrante(cfg, sobranteDe(datos.ingreso, total), meta).cfg;
}

/* Resumen completo de la encuesta para el paso "plan". */
function vistaPreviaEncuesta(datos, cotizacion) {
  datos = datos || {};
  const cfg = construirConfigDesdeEncuesta(datos);
  const gastos = Array.isArray(datos.gastos) ? datos.gastos : [];
  const ingreso = Number(datos.ingreso) || 0;
  const totalGastos = gastos.reduce(function (a, g) { return a + (Number(g.monto) || 0); }, 0);
  const sobrante = sobranteDe(ingreso, totalGastos);

  const reparto = calcularReparto(cfg, ingreso, cotizacion);
  const porGrupo = calcularSubtotalesGrupo(reparto, cfg);
  const perfil = perfilActual(cfg, ingreso, cotizacion);
  const objetivo = buscarPerfil(cfg.objetivo);
  const grupoSobrante = sobrante > 0.005 ? grupoSobranteParaMeta(datos.meta && datos.meta.tipo) : null;
  const meta = datos.meta || {};
  const aporte = sobrante > 0.005 ? sobrante : 0;
  const meses = mesesParaMeta(meta.monto, aporte);
  const consejos = consejosConsejero(cfg, ingreso, cotizacion);

  return {
    cfg: cfg,
    totalGastos: totalGastos,
    sobrante: sobrante,
    porGrupo: porGrupo,
    perfilActual: perfil,
    perfilObjetivo: objetivo,
    grupoSobrante: grupoSobrante,
    meses: meses,
    consejos: consejos,
  };
}
