// FitManage · aplicativo del personal (ADR N.° 17).
// Es el prototipo de la Guía 4 de Software I conectado a la API real (/api/v1, mismo origen):
// ya no trae socios, precios ni reglas propias (DT-04, DT-05 y DT-06). Las fechas, los valores y los
// estados los calcula el servidor; esta página solo los muestra.
// - El token de acceso vive solo en memoria (ADR N.° 06). Si vence, se renueva una vez con la cookie
//   HttpOnly; si no se puede, se vuelve a pedir la sesión.
// - Nada de lo que llega de la API se escribe como HTML: todo pasa por textContent (función h).
// - La política de contenido no permite estilos en línea; los tamaños calculados van por el CSSOM.
"use strict";

const API = "/api/v1";
let sesion = null; // { token, rol, nombre }
let planes = [];

const ESTADO = () => ({
  consulta: { tipo: "CC", numero: "", resultado: null },
  socio: { tipo: "CC", numero: "", nombres: "", apellidos: "", telefono: "", autoriza: false, error: null, ok: false, falta: false },
  pago: { socio: null, planId: null, medio: "EFECTIVO", referencia: "", previa: null, error: null, ok: null, clave: null, enviando: false },
  hist: { tipo: "CC", numero: "", datos: null, error: null, confirmando: false, motivo: "", falta: false, aviso: null, cambio: null, cambiado: null },
  reporte: { desde: null, hasta: null, datos: null, error: null },
  venc: { dias: 3, filas: null, error: null },
  planes: { todos: null, aviso: null, error: null, creando: false },
  personal: { cuentas: null, error: null, aviso: null, creando: false },
  pagoBusqueda: { tipo: "CC", numero: "" },
});
let S = ESTADO();
let llevarDatos = false;

const TIPOS = [["CC", "CC · Cédula de ciudadanía"], ["CE", "CE · Cédula de extranjería"], ["PPT", "PPT · Permiso por protección temporal"], ["PASAPORTE", "Pasaporte"]];
const MEDIOS = [["EFECTIVO", "Efectivo"], ["NEQUI", "Nequi"], ["DAVIPLATA", "Daviplata"], ["TRANSFERENCIA", "Transferencia"]];
const ROLES = { RECEPCIONISTA: "Recepcionista", ADMINISTRADOR: "Administrador", ENTRENADOR: "Entrenador" };
const DIAS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const RUTAS_ADMIN = ["historial", "reportes", "planes", "personal"];
const TITULOS = { login: "Iniciar sesión", recepcion: "Recepción", pago: "Registrar pago", socio: "Registrar socio", vencimientos: "Vencimientos", historial: "Socios e historial", reportes: "Reportes", planes: "Planes", personal: "Personal" };
const COLOR = { ok: "#1E8A4C", aviso: "#B45309", mal: "#B42318", neutro: "#77738A", plan: "#5B3A99" };
const MEDIO_COLOR = { EFECTIVO: "#23005A", NEQUI: "#5B3A99", DAVIPLATA: "#9A84C7", TRANSFERENCIA: "#1E8A4C" };
const SIN_CONEXION = "No hay conexión con FitManage. Revise el internet de la recepción.";

/* --- Construcción del DOM sin HTML --------------------------------------------------------- */
function h(tag, props, ...hijos) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props || {})) {
    if (v === false || v == null) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "value") el.value = v;
    else if (k === "checked") el.checked = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  poner(el, hijos);
  return el;
}
function poner(el, hijos) {
  for (const hijo of hijos.flat(Infinity)) {
    if (hijo == null || hijo === false) continue;
    el.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  }
  return el;
}
const SVG = "http://www.w3.org/2000/svg";
function s(tag, attrs, ...hijos) {
  const el = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs || {})) if (v != null) el.setAttribute(k, v);
  for (const hijo of hijos.flat()) if (hijo) el.append(hijo);
  return el;
}

/* Iconos del prototipo: trazo 1.8, 20 px */
const ICO = {"recepcion":[["circle",{"cx":"11","cy":"11","r":"6.5"}],["path",{"d":"m16 16 4 4"}]],"socio":[["circle",{"cx":"10","cy":"8","r":"3.5"}],["path",{"d":"M3.5 19c.8-3.4 3.4-5 6.5-5s5.7 1.6 6.5 5M18 7v6M15 10h6"}]],"pago":[["rect",{"x":"3","y":"6","width":"18","height":"12","rx":"2.5"}],["path",{"d":"M3 10h18M7 14.5h3"}]],"vencimientos":[["rect",{"x":"4","y":"5","width":"16","height":"15","rx":"2.5"}],["path",{"d":"M4 10h16M9 3v4M15 3v4M9 14.5l2 2 4-4"}]],"historial":[["path",{"d":"M4 6h11M4 12h11M4 18h7"}],["circle",{"cx":"18.5","cy":"17","r":"2.5"}],["path",{"d":"M18.5 6v8"}]],"reportes":[["path",{"d":"M4 20V10M10 20V4M16 20v-7M21 20H3"}]],"planes":[["path",{"d":"M12 3 4 7l8 4 8-4-8-4ZM4 12l8 4 8-4M4 17l8 4 8-4"}]],"personal":[["circle",{"cx":"9","cy":"8","r":"3"}],["circle",{"cx":"17","cy":"9","r":"2.5"}],["path",{"d":"M3 19c.6-3 3-4.5 6-4.5s5.4 1.5 6 4.5M15.5 14.6c2.6-.3 4.8.9 5.5 3.4"}]],"salir":[["path",{"d":"M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16l-4-4 4-4M6 12h10"}]],"volver":[["path",{"d":"M15 6l-6 6 6 6"}]],"alerta":[["circle",{"cx":"12","cy":"12","r":"9"}],["path",{"d":"M12 7.5v5.5M12 16.5v.01"}]],"ok":[["circle",{"cx":"12","cy":"12","r":"9"}],["path",{"class":"check","pathLength":"1","d":"m8 12.5 2.8 2.8L16 10"}]],"wa":[["path",{"d":"M4 20l1.3-4A8 8 0 1 1 8.2 19z"}],["path",{"d":"M9 9.5c.3 2.3 2.2 4.3 4.6 4.8l1-1.2 2 .9c-.3 1.3-1.4 2-2.6 1.8A7 7 0 0 1 8.2 10c-.2-1.2.5-2.3 1.8-2.6l.9 2z"}]]};
function ico(nombre, t = 20) {
  return s("svg", { width: t, height: t, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8", "stroke-linecap": "round", "stroke-linejoin": "round", "aria-hidden": "true" },
    ICO[nombre].map(([tag, a]) => s(tag, a)));
}
function marcaSvg(t) {
  const anilloMarca = (color, dash, offset) => s("circle", { cx: 60, cy: 60, r: 46, fill: "none", stroke: color, "stroke-width": 10, "stroke-linecap": "round", "stroke-dasharray": dash, "stroke-dashoffset": offset, transform: "rotate(-90 60 60)" });
  return s("svg", { width: t, height: t, viewBox: "0 0 120 120", "aria-hidden": "true" },
    s("circle", { cx: 60, cy: 60, r: 46, fill: "none", stroke: "#4A2C7A", "stroke-width": 10 }),
    anilloMarca("#fff", "200 289"), anilloMarca("#5EE08F", "44 289", "-218"),
    s("rect", { x: 36, y: 56, width: 48, height: 8, rx: 4, fill: "#fff" }), s("rect", { x: 30, y: 44, width: 9, height: 32, rx: 3, fill: "#fff" }),
    s("rect", { x: 23, y: 49, width: 7, height: 22, rx: 2.5, fill: "#fff" }), s("rect", { x: 81, y: 44, width: 9, height: 32, rx: 3, fill: "#fff" }),
    s("rect", { x: 90, y: 49, width: 7, height: 22, rx: 2.5, fill: "#fff" }));
}

/* --- Fechas y montos: solo para mostrar lo que manda el servidor ---------------------------- */
const p2 = (n) => String(n).padStart(2, "0");
const deISO = (iso) => { const [a, m, d] = iso.slice(0, 10).split("-").map(Number); return new Date(a, m - 1, d); };
const aISO = (d) => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`;
const corta = (iso) => { const d = deISO(iso); return `${p2(d.getDate())}/${p2(d.getMonth() + 1)}/${d.getFullYear()}`; };
const larga = (iso) => { const d = deISO(iso); return `${DIAS[d.getDay()]} ${d.getDate()} de ${MESES[d.getMonth()]}`; };
const horaDe = (iso) => new Date(iso).toLocaleString("es-CO", { timeZone: "America/Bogota", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false });
const hoyISO = () => aISO(new Date());
const pesos = (n) => "$ " + Number(n).toLocaleString("es-CO");
const diasHasta = (iso) => Math.round((deISO(iso) - deISO(hoyISO())) / 864e5);
const cuando = (iso) => { const n = diasHasta(iso); return n === 0 ? "Hoy" : n === 1 ? "Mañana" : `${DIAS[deISO(iso).getDay()].slice(0, 3)} ${deISO(iso).getDate()}`; };
const mayuscula = (t) => t.charAt(0).toUpperCase() + t.slice(1);
const nombrePlan = (id) => (planes.find((p) => p.id === id) || {}).nombre;
const esAdmin = () => sesion && sesion.rol === "ADMINISTRADOR";

/* --- API ---------------------------------------------------------------------------------- */
async function llamar(ruta, { metodo = "GET", cuerpo, cabeceras = {}, renovar = true } = {}) {
  let respuesta;
  try {
    respuesta = await fetch(API + ruta, {
      method: metodo,
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        ...(sesion ? { Authorization: `Bearer ${sesion.token}` } : {}),
        ...(cuerpo ? { "Content-Type": "application/json" } : {}),
        ...cabeceras,
      },
      body: cuerpo ? JSON.stringify(cuerpo) : undefined,
    });
  } catch {
    return { estado: 0, datos: null };
  }
  if (respuesta.status === 401 && sesion && renovar) {
    if (await renovarSesion()) return llamar(ruta, { metodo, cuerpo, cabeceras, renovar: false });
    cerrarSesion("La sesión venció. Vuelva a iniciar sesión.");
  }
  const datos = await respuesta.json().catch(() => null);
  return { estado: respuesta.status, datos };
}
async function renovarSesion() {
  try {
    const r = await fetch(`${API}/auth/renovacion`, { method: "POST", credentials: "same-origin" });
    if (!r.ok) return false;
    const d = await r.json();
    sesion = { token: d.tokenAcceso, rol: d.rol, nombre: d.nombre };
    return true;
  } catch {
    return false;
  }
}
function mensajeDe({ estado, datos }) {
  if (estado === 0) return SIN_CONEXION;
  if (!datos) return `El servidor respondió ${estado}. Intente de nuevo.`;
  const detalle = (datos.errores || []).map((e) => e.mensaje).join(" ");
  return [datos.title, detalle || datos.detail].filter(Boolean).join(". ");
}
const ruta = (t, n) => `/${encodeURIComponent(t)}/${encodeURIComponent(n)}`;
// Una pantalla puede pintarse varias veces mientras espera una respuesta: cada carga sale una sola vez.
const enCurso = new Set();
function una(clave, cargar) {
  if (enCurso.has(clave)) return;
  enCurso.add(clave);
  void cargar().finally(() => enCurso.delete(clave));
}
async function cargarPlanes() {
  const r = await llamar("/planes");
  if (r.estado === 200) planes = r.datos;
}

/* --- Anillo de vigencia -------------------------------------------------------------------- */
const QUIETO = window.matchMedia("(prefers-reduced-motion: reduce)");
function anillo(segs, total, opc) {
  const t = opc.t || 180, g = opc.g || Math.round(t * 0.09), r = (t - g) / 2, c = 2 * Math.PI * r;
  let acum = 0;
  const lista = segs.length ? segs : [{ v: 0, color: opc.vacio || COLOR.neutro }];
  const arcos = lista.map((sg) => {
    const largo = sg.v > 0 ? Math.max(0, (Math.min(sg.v, total) / total) * c - (lista.length > 1 ? 3 : 0)) : 0;
    const arco = s("circle", { class: "arco", cx: t / 2, cy: t / 2, r, fill: "none", stroke: sg.color, "stroke-width": g, "stroke-linecap": sg.v >= total ? "butt" : "round", "stroke-dasharray": `${largo} ${c}`, "stroke-dashoffset": -acum, opacity: largo > 0 ? 1 : 0 });
    arco.dataset.l = largo; arco.dataset.c = c;
    acum += (sg.v / total) * c;
    return arco;
  });
  const pista = s("circle", { cx: t / 2, cy: t / 2, r, fill: "none", stroke: opc.pista || "rgba(35,0,90,.1)", "stroke-width": g, "stroke-dasharray": opc.punteada ? `${g * 0.35} ${g * 0.9}` : null });
  const caja = h("div", { class: "anillo" + (opc.clase ? " " + opc.clase : ""), role: opc.etiqueta ? "img" : null, "aria-label": opc.etiqueta || null, "aria-hidden": opc.etiqueta ? null : "true" },
    s("svg", { width: t, height: t, viewBox: `0 0 ${t} ${t}` }, pista, arcos),
    h("div", { class: "centro" }, opc.centro || null));
  caja.style.setProperty("width", `${t}px`);
  caja.style.setProperty("height", `${t}px`);
  caja.dataset.anillo = "1";
  return caja;
}
function numeroAnillo(n, t, texto) {
  const b = h("b", { "data-n": n }, String(n));
  b.style.setProperty("font-size", `${Math.round(t * 0.3)}px`);
  return [b, h("span", {}, texto)];
}
function anilloEstado(e, t) {
  if (!e || e.estado === "SIN_MEMBRESIA") return anillo([], 1, { t, punteada: true, pista: "rgba(61,58,77,.35)", centro: numeroAnillo(0, t, "días"), etiqueta: "Sin membresía" });
  if (e.estado === "VENCIDO") return anillo([], 1, { t, vacio: COLOR.mal, pista: "rgba(180,35,24,.22)", centro: numeroAnillo(e.diasMora, t, e.diasMora === 1 ? "día de mora" : "días de mora"), etiqueta: `Vencido hace ${e.diasMora} días` });
  const clave = e.diasRestantes <= 3 ? "aviso" : "ok";
  const total = Math.max(30, e.diasRestantes);
  return anillo([{ v: e.diasRestantes, color: COLOR[clave] }], total, { t, pista: clave === "ok" ? "rgba(30,138,76,.16)" : "rgba(180,83,9,.16)", centro: numeroAnillo(e.diasRestantes, t, e.diasRestantes === 1 ? "día" : "días"), etiqueta: `Le quedan ${e.diasRestantes} días` });
}
function animarAnillos(raiz) {
  if (QUIETO.matches) return;
  raiz.querySelectorAll("[data-anillo] .arco").forEach((arco, i) => {
    const l = +arco.dataset.l, c = +arco.dataset.c;
    if (arco.animate) arco.animate([{ strokeDasharray: `0 ${c}` }, { strokeDasharray: `${l} ${c}` }], { duration: 900, delay: 80 + i * 120, easing: "cubic-bezier(.16,1,.3,1)", fill: "backwards" });
  });
  raiz.querySelectorAll("[data-anillo] [data-n]").forEach((el) => {
    const fin = +el.dataset.n, t0 = performance.now();
    const paso = (ahora) => { const x = Math.min(1, (ahora - t0) / 900); el.textContent = String(Math.round(fin * (1 - Math.pow(2, -10 * x)))); if (x < 1 && el.isConnected) requestAnimationFrame(paso); };
    requestAnimationFrame(paso);
  });
}

/* --- Piezas comunes ------------------------------------------------------------------------ */
const aviso = (tipo, ...contenido) => h("div", { class: `aviso a-${tipo}`, role: tipo === "mal" ? "alert" : "status" }, ico(tipo === "ok" ? "ok" : "alerta"), h("div", {}, contenido));
const pastilla = (tipo, texto, clase = "") => h("span", { class: `pastilla p-${tipo} ${clase}`.trim() }, texto);
const campo = (id, etiqueta, control, ayuda) => h("div", { class: "campo" }, h("label", { class: "et", for: id }, etiqueta), control, ayuda ? h("span", { class: "ayuda" }, ayuda) : null);
const selectTipo = (id, valor, alCambiar, corto = false) => h("select", { id, "aria-label": "Tipo de documento", onchange: (e) => alCambiar(e.target.value) },
  TIPOS.map(([v, t]) => h("option", { value: v, selected: v === valor }, corto ? (v === "PASAPORTE" ? "Pasaporte" : v) : t)));
const volver = () => h("a", { class: "volver", href: "#recepcion" }, ico("volver", 18), "Volver a recepción");
const tabla = (cabeceras, filas, clase) => h("div", { class: "tabla-caja" }, h("table", { class: clase || null },
  h("thead", {}, h("tr", {}, cabeceras.map((c) => h("th", { scope: "col", class: c.startsWith(">") ? "der" : null }, c.replace(/^>/, ""))))),
  h("tbody", {}, filas)));
function ocupado(boton, si) { if (boton) boton.disabled = si; }
function buscadorDoc(estado, alBuscar, texto = "Buscar") {
  return h("form", { class: "hoja consulta", novalidate: true, onsubmit: (e) => { e.preventDefault(); if (estado.numero.trim()) alBuscar(); } },
    h("label", { class: "et", for: "doc-b" }, "Documento del socio"),
    h("div", { class: "buscador" },
      selectTipo("tipo-b", estado.tipo, (v) => { estado.tipo = v; }, true),
      h("input", { id: "doc-b", type: "text", inputmode: "numeric", autocomplete: "off", placeholder: "1090123456", value: estado.numero, oninput: (e) => { estado.numero = e.target.value; } }),
      h("button", { class: "btn", type: "submit" }, texto)));
}

/* --- Marco con riel ------------------------------------------------------------------------ */
function enlace(r, texto) {
  // Volver a la misma sección desde el menú también la deja en blanco.
  const mismo = (ev) => { if (rutaActual() === r) { ev.preventDefault(); S = ESTADO(); render(); } };
  return h("a", { href: `#${r}`, "aria-current": rutaActual() === r ? "page" : null, onclick: mismo }, ico(r), h("span", {}, texto));
}
function marco(...contenido) {
  const nombre = sesion.nombre || "Personal";
  return h("div", { class: "app" },
    h("aside", { class: "riel" },
      h("a", { class: "marca", href: "#recepcion", "aria-label": "FitManage, ir a recepción" }, marcaSvg(36), h("b", {}, "Fit", h("span", {}, "Manage"))),
      h("nav", { "aria-label": "Menú principal" },
        h("div", { class: "grupo" }, enlace("recepcion", "Recepción"), enlace("socio", "Registrar socio"), enlace("pago", "Registrar pago"), enlace("vencimientos", "Vencimientos")),
        esAdmin() ? h("div", { class: "grupo" }, h("div", { class: "grupo-t" }, "Administración"), enlace("historial", "Socios e historial"), enlace("reportes", "Reportes"), enlace("planes", "Planes"), enlace("personal", "Personal")) : null),
      h("div", { class: "conexion" + (navigator.onLine ? "" : " caida") }, h("i", {}), h("span", {}, navigator.onLine ? "En línea con el servidor" : "Sin conexión: la consulta necesita internet")),
      h("div", { class: "usuario" }, h("span", { class: "avatar" }, nombre.charAt(0).toUpperCase()), h("div", {}, h("strong", {}, nombre), h("small", {}, ROLES[sesion.rol] || sesion.rol)),
        h("button", { type: "button", class: "salir", "aria-label": "Cerrar sesión", title: "Cerrar sesión", onclick: () => cerrarSesion() }, ico("salir"))),
      h("div", { class: "demo" }, "Solo datos de prueba hasta que se apruebe el aviso de privacidad (DT-10).")),
    h("main", { id: "contenido", tabindex: "-1" }, contenido));
}

/* --- Iniciar sesión ------------------------------------------------------------------------ */
function pLogin(motivo) {
  const error = h("div", { class: "msg-error", role: "alert" }, motivo || "");
  const boton = h("button", { class: "btn btn-grande", type: "submit" }, "Entrar");
  const correo = h("input", { id: "correo", type: "email", autocomplete: "username", required: true });
  const clave = h("input", { id: "clave", type: "password", autocomplete: "current-password", required: true });
  const form = h("form", { novalidate: true, onsubmit: async (e) => {
    e.preventDefault();
    if (!correo.value.trim() || !clave.value) { error.textContent = "Escriba el correo y la contraseña."; return; }
    ocupado(boton, true); error.textContent = "";
    const r = await llamar("/auth/token", { metodo: "POST", cuerpo: { correo: correo.value.trim(), contrasena: clave.value }, renovar: false });
    ocupado(boton, false);
    if (r.estado !== 200) { error.textContent = mensajeDe(r); clave.value = ""; clave.focus(); return; }
    sesion = { token: r.datos.tokenAcceso, rol: r.datos.rol, nombre: r.datos.nombre };
    await cargarPlanes();
    ir("recepcion");
  } },
    h("h1", {}, "Iniciar sesión"),
    campo("correo", "Correo", correo),
    campo("clave", "Contraseña", clave, "Después de 5 intentos fallidos la cuenta se bloquea 15 minutos."),
    boton, error,
    h("div", { class: "sub peq" }, "Si la cuenta se bloquea, el administrador puede desbloquearla desde Personal."));
  return h("div", { class: "login" },
    h("section", { class: "panel-marca" },
      h("div", { class: "marca" }, marcaSvg(44), h("b", {}, "Fit", h("span", {}, "Manage"))),
      h("div", {}, h("div", { class: "lema" }, "Membresías, pagos y acceso en un solo lugar."), h("p", {}, "Para el personal del gimnasio. Todo lo que se registra queda a nombre de quien lo hizo.")),
      h("div", { class: "pie" }, "Ingeniería de Software II · Universidad de Pamplona"),
      h("div", { class: "grande" }, anillo([{ v: 22, color: "#FFFFFF" }, { v: 6, color: "#5EE08F" }], 30, { t: 260, g: 26, pista: "#34106E" }))),
    h("section", { class: "panel-form" }, form));
}

/* --- Recepción (CU-02) --------------------------------------------------------------------- */
async function consultar() {
  const c = S.consulta;
  const numero = c.numero.trim();
  if (!numero) return;
  const r = await llamar(`/estados${ruta(c.tipo, numero)}`);
  c.resultado = { tipo: c.tipo, numero, ...r };
  render();
  const i = document.getElementById("doc");
  if (i) i.focus();
}
function irAPago(tipo, numero, estado) { llevarDatos = true; S.pago = { ...ESTADO().pago, socio: { tipo, numero, estado } }; ir("pago"); }
function resultadoConsulta() {
  const res = S.consulta.resultado;
  if (!res) return h("div", { class: "resultado r-vacio" }, anillo([], 1, { t: 96, punteada: true, pista: "#C9BCE0" }),
    h("div", { class: "resultado-texto" }, h("b", {}, "Digite el documento y presione Enter."), h("div", { class: "sub" }, "El estado del socio aparece aquí con los días que le quedan.")));
  if (res.estado === 404) return h("div", { class: "resultado r-neutro", role: "status" },
    anillo([], 1, { t: 140, punteada: true, pista: "rgba(61,58,77,.35)", centro: h("b", { class: "estado-grande" }, "?") }),
    h("div", {}, h("div", { class: "estado estado-grande" }, "No registrado"), h("div", { class: "estado-sub" }, `Nadie tiene el documento ${res.tipo} ${res.numero}`),
      h("div", { class: "acciones" }, h("a", { class: "btn", href: "#socio", onclick: () => { llevarDatos = true; Object.assign(S.socio, { ...ESTADO().socio, tipo: res.tipo, numero: res.numero }); } }, "Registrar socio"))));
  if (res.estado !== 200) return aviso("mal", mensajeDe(res));
  const e = res.datos;
  const datos = (extra) => h("div", { class: "datos" }, h("div", { class: "dato" }, h("span", {}, "Socio"), h("strong", {}, e.nombreCorto)),
    h("div", { class: "dato" }, h("span", {}, "Documento"), h("strong", { class: "tab" }, e.documentoEnmascarado)), extra);
  const historial = esAdmin() ? h("a", { class: "btn-sec", href: "#historial", onclick: () => { llevarDatos = true; Object.assign(S.hist, { ...ESTADO().hist, tipo: res.tipo, numero: res.numero }); } }, "Ver historial") : null;
  const pagar = (clase, texto) => h("a", { class: clase, href: "#pago", onclick: (ev) => { ev.preventDefault(); irAPago(res.tipo, res.numero, e); } }, texto);
  if (e.estado === "ACTIVO") {
    const clave = e.diasRestantes <= 3 ? "aviso" : "ok";
    return h("div", { class: `resultado r-${clave}`, role: "status" }, anilloEstado(e, 188),
      h("div", {}, h("div", { class: "estado" }, "ACTIVO"), h("div", { class: "estado-sub" }, clave === "aviso" ? "Puede ingresar · vence pronto" : "Puede ingresar"),
        datos(h("div", { class: "dato" }, h("span", {}, "Vence"), h("strong", {}, larga(e.venceEl)))),
        h("div", { class: "acciones" }, pagar("btn-sec", "Renovar antes de que venza"), historial)));
  }
  if (e.estado === "VENCIDO") return h("div", { class: "resultado r-mal", role: "status" }, anilloEstado(e, 188),
    h("div", {}, h("div", { class: "estado" }, "VENCIDO"), h("div", { class: "estado-sub" }, "No puede ingresar sin pagar"),
      datos(h("div", { class: "dato" }, h("span", {}, "Venció"), h("strong", {}, corta(e.venceEl)))),
      h("div", { class: "acciones" }, pagar("btn btn-peligro", "Registrar pago"), historial)));
  return h("div", { class: "resultado r-neutro", role: "status" }, anilloEstado(e, 188),
    h("div", {}, h("div", { class: "estado" }, "SIN MEMBRESÍA"), h("div", { class: "estado-sub" }, "Está registrado pero no tiene pagos vigentes"),
      datos(null), h("div", { class: "acciones" }, pagar("btn", "Registrar primer pago"), historial)));
}
async function cargarVencimientos() {
  const r = await llamar(`/vencimientos?dias=${S.venc.dias}`);
  S.venc.filas = r.estado === 200 ? r.datos : null;
  S.venc.error = r.estado === 200 ? null : mensajeDe(r);
}
function vencimientosLista() {
  if (S.venc.error) return h("p", { class: "msg-error" }, S.venc.error);
  if (!S.venc.filas) return h("p", { class: "vacio" }, "Cargando…");
  if (!S.venc.filas.length) return h("p", { class: "vacio" }, "Nadie vence en los próximos días.");
  return h("div", { class: "venc" }, S.venc.filas.slice(0, 6).map((f) => {
    const quedan = diasHasta(f.venceEl) + 1;
    return h("div", { class: "venc-fila" }, anillo([{ v: quedan, color: COLOR.aviso }], Math.max(quedan, 4), { t: 40, g: 5, pista: "rgba(180,83,9,.16)" }),
      h("div", {}, h("b", {}, f.nombreCorto), h("span", { class: "mpeq sub" }, `${f.plan} · ${quedan === 1 ? "último día" : "quedan " + quedan + " días"}`)),
      h("span", { class: "cuando" }, cuando(f.venceEl)));
  }));
}
function pRecepcion() {
  const c = S.consulta;
  const hoy = larga(hoyISO());
  if (!S.venc.filas && !S.venc.error) una("venc", () => cargarVencimientos().then(render));
  return marco(
    h("div", { class: "cabecera" }, h("div", {}, h("h1", {}, "Recepción"), h("div", { class: "sub" }, `${mayuscula(hoy)} · hora de Colombia`))),
    h("div", { class: "dos" },
      h("section", { class: "pila", "aria-label": "Consulta de estado" },
        h("form", { class: "hoja consulta", novalidate: true, onsubmit: (e) => { e.preventDefault(); void consultar(); } },
          h("label", { class: "et", for: "doc" }, "Documento del socio"),
          h("div", { class: "buscador" },
            selectTipo("tipo", c.tipo, (v) => { c.tipo = v; }, true),
            h("input", { id: "doc", type: "text", inputmode: "numeric", autocomplete: "off", placeholder: "1090123456", value: c.numero, oninput: (e) => { c.numero = e.target.value; } }),
            h("button", { class: "btn", type: "submit" }, "Consultar"))),
        resultadoConsulta()),
      h("aside", { class: "hoja", "aria-labelledby": "t-venc" }, h("h2", { id: "t-venc" }, "Vencen en los próximos días"), vencimientosLista(),
        h("a", { href: "#vencimientos", class: "btn-sec ancho mt-12" }, "Ver vencimientos y avisar"))));
}

/* --- Registrar socio (CU-04) --------------------------------------------------------------- */
function pSocio() {
  const X = S.socio;
  const guarda = (clave) => (e) => { X[clave] = e.target.type === "checkbox" ? e.target.checked : e.target.value; };
  const nombres = h("input", { id: "nom", type: "text", maxlength: "60", autocomplete: "off", value: X.nombres, oninput: guarda("nombres") });
  const apellidos = h("input", { id: "ape", type: "text", maxlength: "60", autocomplete: "off", value: X.apellidos, oninput: guarda("apellidos") });
  const telefono = h("input", { id: "tel", type: "tel", inputmode: "numeric", maxlength: "10", autocomplete: "off", class: "tab-num", value: X.telefono, oninput: guarda("telefono") });
  const autoriza = h("input", { type: "checkbox", id: "autoriza", checked: X.autoriza, onchange: guarda("autoriza") });
  const boton = h("button", { class: "btn", type: "submit" }, "Guardar socio");
  const enviar = async (e) => {
    e.preventDefault();
    X.falta = !autoriza.checked;
    const numero = X.numero.trim();
    const faltan = [!numero && "el número de documento", !nombres.value.trim() && "los nombres", !apellidos.value.trim() && "los apellidos", !/^3\d{9}$/.test(telefono.value.trim()) && "un celular de 10 dígitos que empiece por 3"].filter(Boolean);
    if (faltan.length || X.falta) { X.error = faltan.length ? `Falta ${faltan.join(", ")}.` : null; X.ok = false; return render(); }
    ocupado(boton, true);
    const r = await llamar("/socios", { metodo: "POST", cuerpo: { tipoDocumento: X.tipo, numeroDocumento: numero, nombres: nombres.value.trim(), apellidos: apellidos.value.trim(), telefono: telefono.value.trim(), autorizaTratamientoDatos: true } });
    if (r.estado === 201) { X.ok = r.datos; X.error = null; } else { X.ok = false; X.error = r.estado === 409 ? "duplicado" : mensajeDe(r); }
    render();
  };
  const dup = X.error === "duplicado";
  return marco(
    h("div", {}, volver(), h("h1", {}, "Registrar socio"), h("div", { class: "sub mt-6" }, "Todos los campos son obligatorios.")),
    h("form", { class: "hoja pila form-ancho", novalidate: true, onsubmit: enviar },
      h("div", { class: "rejilla r2" },
        campo("tipo-s", "Tipo de documento", selectTipo("tipo-s", X.tipo, (v) => { X.tipo = v; })),
        h("div", { class: "campo" }, h("label", { class: "et", for: "num" }, "Número de documento"),
          h("input", { id: "num", type: "text", inputmode: "numeric", autocomplete: "off", value: X.numero, class: "tab-num" + (dup ? " error-campo" : ""), oninput: (e) => { X.numero = e.target.value; } }),
          dup ? h("div", { class: "msg-error", role: "alert" }, ico("alerta", 18), h("span", {}, "Ese documento ya está registrado. ", h("a", { href: "#recepcion", onclick: () => { llevarDatos = true; Object.assign(S.consulta, { tipo: X.tipo, numero: X.numero.trim() }); void consultar(); } }, "Ver su estado"))) : null),
        campo("nom", "Nombres", nombres), campo("ape", "Apellidos", apellidos),
        campo("tel", "Celular (10 dígitos)", telefono, "Se usa para el recordatorio por WhatsApp.")),
      h("div", { class: "autorizacion" + (X.falta ? " falta" : "") },
        h("h3", {}, "Autorización de tratamiento de datos"),
        h("p", { class: "peq" }, "Autorizo al gimnasio a guardar mi nombre, documento y celular para administrar mi membresía y enviarme recordatorios de vencimiento por WhatsApp. Puedo pedir en la recepción que consulten, corrijan o borren mis datos (Ley 1581 de 2012)."),
        h("p", { class: "nota-pendiente" }, "El texto legal definitivo del aviso de privacidad todavía no está aprobado (DT-10). Hasta el hito H2 del roadmap, registre solo datos de prueba."),
        h("label", { class: "casilla" }, autoriza, "El socio leyó y acepta la autorización"),
        X.falta ? h("div", { class: "msg-error", role: "alert" }, ico("alerta", 18), "Sin la autorización del socio no se puede guardar el registro.") : null),
      X.error && !dup ? aviso("mal", X.error) : null,
      X.ok ? h("div", { class: "aviso a-ok aviso-ok-accion", role: "status" }, ico("ok"), h("span", {}, h("b", {}, "Socio registrado. "), `${X.ok.nombreCorto} todavía no tiene membresía.`),
        h("a", { class: "btn", href: "#pago", onclick: (ev) => { ev.preventDefault(); irAPago(X.tipo, X.numero.trim(), { estado: "SIN_MEMBRESIA", nombreCorto: X.ok.nombreCorto, documentoEnmascarado: X.ok.documentoEnmascarado }); } }, "Registrar su primer pago")) : null,
      h("div", { class: "fila" }, boton)));
}

/* --- Registrar pago (CU-01) ---------------------------------------------------------------- */
async function cargarPrevia() {
  const P = S.pago;
  if (!P.socio || !P.planId) return;
  const q = new URLSearchParams({ tipoDocumento: P.socio.tipo, numeroDocumento: P.socio.numero, planId: P.planId });
  const r = await llamar(`/pagos/vista-previa?${q}`);
  P.previa = r.estado === 200 ? r.datos : null;
  if (r.estado !== 200) P.error = mensajeDe(r);
  render();
}
async function buscarSocioPago() {
  const P = S.pago, b = S.pagoBusqueda;
  const r = await llamar(`/estados${ruta(b.tipo, b.numero.trim())}`);
  if (r.estado === 200) { P.socio = { tipo: b.tipo, numero: b.numero.trim(), estado: r.datos }; P.error = null; if (P.planId) await cargarPrevia(); }
  else P.error = r.estado === 404 ? "No hay ningún socio con ese documento. Regístrelo primero." : mensajeDe(r);
  render();
}
async function confirmarPago(boton) {
  const P = S.pago;
  if (P.ok || P.enviando) return;
  const pide = P.medio !== "EFECTIVO";
  if (pide && !P.referencia.trim()) { P.error = "vacia"; return render(); }
  P.enviando = true; ocupado(boton, true);
  P.clave = P.clave || crypto.randomUUID();
  const cuerpo = { tipoDocumento: P.socio.tipo, numeroDocumento: P.socio.numero, planId: P.planId, medio: P.medio, ...(pide ? { referencia: P.referencia.trim() } : {}) };
  const r = await llamar("/pagos", { metodo: "POST", cuerpo, cabeceras: { "Idempotency-Key": P.clave } });
  P.enviando = false;
  if (r.estado === 201) { P.ok = r.datos; P.error = null; P.clave = null; S.venc.filas = null; S.consulta.resultado = null; }
  else if (r.estado === 0) P.error = "No hay conexión. El pago no quedó confirmado: vuelva a intentar con el mismo botón.";
  else P.error = r.datos && r.datos.codigo === "COMPROBANTE_DUPLICADO" ? "dup" : mensajeDe(r);
  render();
}
function pPago() {
  const P = S.pago;
  if (!P.socio) {
    return marco(h("div", {}, volver(), h("h1", {}, "Registrar pago")),
      h("p", { class: "sub sin-margen" }, "Busque primero al socio por su documento."),
      buscadorDoc(S.pagoBusqueda, buscarSocioPago), P.error ? aviso("mal", P.error) : null);
  }
  if (!P.planId && planes.length) { P.planId = (planes.find((p) => p.nombre === "Mensual") || planes[0]).id; una("previa", cargarPrevia); }
  const e = P.socio.estado || {};
  const renov = e.estado === "ACTIVO";
  const pv = P.previa;
  const duracion = pv ? pv.plan.duracionDias : 0;
  const quedanHoy = renov ? e.diasRestantes : 0;
  const total = pv ? pv.diasDesdeHoy : 1;
  const segs = pv ? (renov ? [{ v: quedanHoy, color: COLOR.ok }, { v: duracion, color: COLOR.plan }] : [{ v: duracion, color: COLOR.plan }]) : [];
  const deshabilitado = !!P.ok;
  const boton = h("button", { type: "button", class: "btn btn-confirmar", disabled: deshabilitado || !pv, onclick: (ev) => confirmarPago(ev.currentTarget) }, P.ok ? "Pago registrado" : pv ? `Registrar pago de ${pesos(pv.valor)}` : "Registrar pago");
  const elegirPlan = (id) => { if (P.ok) return; P.planId = id; P.error = null; P.previa = null; render(); void cargarPrevia(); };
  return marco(
    h("div", {}, volver(), h("h1", {}, "Registrar pago")),
    h("div", { class: "hoja socio-cab" },
      h("div", { class: "datos-socio" }, h("div", { class: "nombre" }, e.nombreCorto || `${P.socio.tipo} ${P.socio.numero}`), h("div", { class: "sub tab" }, e.documentoEnmascarado || "")),
      renov ? pastilla("ok", `Activo hasta el ${corta(e.venceEl)}`) : e.estado === "VENCIDO" ? pastilla("mal", `Vencido desde el ${corta(e.venceEl)}`) : pastilla("neutro", "Sin membresía"),
      h("button", { type: "button", class: "btn-sec", onclick: () => { S.pago = ESTADO().pago; S.pagoBusqueda = { tipo: "CC", numero: "" }; render(); } }, "Cambiar socio")),
    h("section", { class: "pila", "aria-labelledby": "t-plan" }, h("h2", { id: "t-plan", class: "paso" }, h("em", {}, "1"), "Plan"),
      h("div", { class: "rejilla r4" }, planes.map((p) => h("button", { type: "button", class: "opcion", "aria-pressed": String(P.planId === p.id), disabled: deshabilitado, onclick: () => elegirPlan(p.id) },
        h("b", {}, p.nombre), h("span", { class: "peq sub" }, `${p.duracionDias} ${p.duracionDias === 1 ? "día" : "días"}`), h("span", { class: "precio" }, pesos(p.precio)))))),
    h("section", { class: "pila", "aria-labelledby": "t-medio" }, h("h2", { id: "t-medio", class: "paso" }, h("em", {}, "2"), "Medio de pago"),
      h("div", { class: "fila" }, MEDIOS.map(([v, t]) => h("button", { type: "button", class: "chip", "aria-pressed": String(P.medio === v), disabled: deshabilitado, onclick: () => { P.medio = v; P.error = null; render(); } }, t))),
      P.medio !== "EFECTIVO" ? h("div", { class: "campo campo-ref" }, h("label", { class: "et", for: "ref" }, "Referencia del comprobante"),
        h("input", { id: "ref", type: "text", autocomplete: "off", placeholder: "El número que muestra el celular del socio", value: P.referencia, class: P.error === "vacia" || P.error === "dup" ? "error-campo" : null, disabled: deshabilitado, oninput: (ev) => { P.referencia = ev.target.value; } }),
        h("span", { class: "ayuda" }, "Letras, números o guiones (4 a 30). No puede repetirse en otro pago vigente.")) : null),
    h("section", { class: "hoja", "aria-labelledby": "t-f" }, h("h2", { id: "t-f", class: "paso" }, h("em", {}, "3"), "Así queda la membresía"),
      pv ? h("div", { class: "periodo mt-16" },
        anillo(segs, total, { t: 168, clase: P.ok ? "confirma entra" : "", centro: [h("b", { "data-n": total, class: "estado-grande" }, String(total)), h("span", {}, "días desde hoy")], etiqueta: `Quedará activo ${total} días, hasta el ${corta(pv.vence)}` }),
        h("div", { class: "pila" },
          h("div", { class: "linea-fechas" }, h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Inicia"), h("strong", {}, corta(pv.inicia))),
            h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Vence"), h("strong", {}, corta(pv.vence))),
            h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Valor"), h("strong", {}, pesos(pv.valor)))),
          h("div", { class: "leyenda" }, renov ? h("span", {}, leyendaColor(COLOR.ok), `${quedanHoy} días que ya tenía`) : null, h("span", {}, leyendaColor(COLOR.plan), `${duracion} ${duracion === 1 ? "día" : "días"} del plan ${pv.plan.nombre}`)),
          h("div", { class: "sub peq" }, renov ? `Sigue activo hasta el ${corta(e.venceEl)}, así que el plan nuevo empieza al día siguiente y no pierde días (RN-04).` : "El plan empieza hoy.", " Las fechas y el valor los calcula el servidor con el plan vigente."))) : h("p", { class: "vacio" }, "Calculando con el servidor…")),
    P.error === "dup" ? aviso("mal", h("b", {}, "Ese comprobante ya se usó. "), "La referencia pertenece a otro pago vigente. Pida al socio el comprobante correcto.") : null,
    P.error === "vacia" ? aviso("mal", h("b", {}, "Falta la referencia. "), "Para pagos que no son en efectivo escriba el número del comprobante.") : null,
    P.error && P.error !== "dup" && P.error !== "vacia" ? aviso("mal", P.error) : null,
    P.ok ? aviso("ok", h("b", {}, "Pago registrado. "), `${P.ok.plan} por ${pesos(P.ok.valor)}: queda activo hasta el ${larga(P.ok.vence)}.`) : null,
    h("div", { class: "fila" }, boton, h("a", { class: "btn-sec", href: "#recepcion" }, P.ok ? "Volver a recepción" : "Cancelar"),
      h("span", { class: "sub mpeq" }, "El botón se desactiva mientras se registra; si se envía dos veces, el servidor guarda un solo pago.")));
}
function leyendaColor(color) { const i = h("i", {}); i.style.setProperty("background", color); return i; }

/* --- Vencimientos (CU-08, RF-06) ------------------------------------------------------------------ */
function vencimientosTabla() {
  if (S.venc.error) return aviso("mal", S.venc.error);
  if (!S.venc.filas) return h("p", { class: "vacio" }, "Cargando…");
  if (!S.venc.filas.length) return h("p", { class: "vacio" }, "Nadie vence en este rango.");
  return tabla(["Socio", "Plan", "Vence", "Teléfono", "Recordatorio"], S.venc.filas.map((f) => h("tr", {},
    h("td", {}, h("b", {}, f.nombreCorto)), h("td", {}, f.plan), h("td", {}, pastilla("aviso", `${cuando(f.venceEl)} · ${corta(f.venceEl).slice(0, 5)}`)), h("td", { class: "tab" }, f.telefono),
    h("td", {}, f.enlaceWhatsApp ? h("a", { class: "btn-sec", target: "_blank", rel: "noopener noreferrer", href: f.enlaceWhatsApp }, ico("wa", 18), "Abrir WhatsApp")
      : h("span", { class: "msg-error" }, ico("alerta", 18), `Teléfono inválido: tiene ${f.telefono.length} dígitos`)))));
}
function pVencimientos() {
  if (!S.venc.filas && !S.venc.error) una("venc", () => cargarVencimientos().then(render));
  const hasta = new Date(); hasta.setDate(hasta.getDate() + S.venc.dias);
  return marco(
    h("div", { class: "cabecera" }, h("div", {}, h("h1", {}, "Próximos vencimientos"), h("div", { class: "sub" }, `De hoy, ${corta(hoyISO()).slice(0, 5)}, al ${corta(aISO(hasta)).slice(0, 5)}, ambos incluidos.`)),
      h("div", { class: "campo" }, h("label", { class: "et", for: "dias" }, "Días hacia adelante"),
        h("select", { id: "dias", onchange: (e) => { S.venc.dias = Number(e.target.value); S.venc.filas = null; render(); } }, [0, 3, 7, 15].map((d) => h("option", { value: d, selected: d === S.venc.dias }, d === 0 ? "Solo hoy" : `${d} días`))))),
    h("section", { class: "hoja" }, vencimientosTabla()),
    h("p", { class: "sub peq sin-margen" }, "El botón abre WhatsApp con el mensaje escrito; quien lo envía es la recepcionista (RF-06). Esta pantalla no muestra ingresos."));
}

/* --- Socios e historial (CU-03, RF-10) ----------------------------------------------------- */
async function cargarHistorial() {
  const H = S.hist;
  const r = await llamar(`/socios${ruta(H.tipo, H.numero.trim())}/pagos`);
  H.datos = r.estado === 200 ? r.datos : null;
  H.error = r.estado === 200 ? null : r.estado === 404 ? "No hay ningún socio con ese documento." : mensajeDe(r);
  render();
}
async function anularUltimo(pago) {
  const H = S.hist;
  if (H.motivo.trim().length < 5) { H.falta = true; return render(); }
  const r = await llamar(`/pagos/${encodeURIComponent(pago.id)}`, { metodo: "PATCH", cuerpo: { estado: "ANULADO", motivo: H.motivo.trim() } });
  if (r.estado === 200) { H.confirmando = false; H.motivo = ""; H.falta = false; H.aviso = r.datos; S.venc.filas = null; await cargarHistorial(); }
  else { H.error = mensajeDe(r); render(); }
}
/* Cambio de plan: anula el último pago y registra el plan nuevo desde el mismo día (un solo paso). */
function abrirCambio(ultimo) {
  const H = S.hist;
  H.confirmando = false; H.aviso = null; H.cambiado = null; H.error = null;
  H.cambio = { pago: ultimo, planId: null, medio: ultimo.medio, referencia: ultimo.referencia || "", motivo: "", motivoEditado: false, previa: null, error: null, enviando: false };
  render();
}
async function previaCambio() {
  const C = S.hist.cambio;
  const r = await llamar(`/pagos/${encodeURIComponent(C.pago.id)}/cambio-de-plan?${new URLSearchParams({ planId: C.planId })}`);
  C.previa = r.estado === 200 ? r.datos : null;
  C.error = r.estado === 200 ? null : mensajeDe(r);
  render();
}
async function confirmarCambio(boton) {
  const H = S.hist, C = H.cambio;
  if (C.enviando) return;
  const pide = C.medio !== "EFECTIVO";
  if (pide && !C.referencia.trim()) { C.error = "Para pagos que no son en efectivo escriba el número del comprobante."; return render(); }
  if (C.motivo.trim().length < 5) { C.error = "Escriba el motivo del cambio (al menos 5 caracteres)."; return render(); }
  C.enviando = true; ocupado(boton, true);
  const cuerpo = { planId: C.planId, medio: C.medio, motivo: C.motivo.trim(), ...(pide ? { referencia: C.referencia.trim() } : {}) };
  const r = await llamar(`/pagos/${encodeURIComponent(C.pago.id)}/cambio-de-plan`, { metodo: "POST", cuerpo });
  C.enviando = false;
  if (r.estado === 201) { H.cambio = null; H.cambiado = r.datos; S.venc.filas = null; await cargarHistorial(); return; }
  C.error = r.datos && r.datos.codigo === "COMPROBANTE_DUPLICADO" ? "Ese comprobante ya está en otro pago vigente. No se cambió nada." : mensajeDe(r);
  render();
}
function diferenciaTexto(d) {
  if (d > 0) return `Cobre ${pesos(d)} adicionales al socio.`;
  if (d < 0) return `Devuelva ${pesos(-d)} al socio.`;
  return "Sin diferencia de dinero.";
}
function panelCambio() {
  const C = S.hist.cambio, P = C.pago;
  const otros = planes.filter((p) => p.nombre !== P.plan);
  const elegir = (p) => {
    C.planId = p.id; C.previa = null; C.error = null;
    if (!C.motivoEditado) C.motivo = `El socio pidió cambiar de ${P.plan} a ${p.nombre}`;
    render(); void previaCambio();
  };
  const pv = C.previa;
  return h("section", { class: "hoja pila", "aria-labelledby": "t-cp" },
    h("h2", { id: "t-cp" }, "Cambiar el plan"),
    h("p", { class: "sub peq sin-margen" }, `Plan actual: ${P.plan}, del ${corta(P.inicia)} al ${corta(P.vence)} (${pesos(P.valor)}). El plan nuevo empieza el mismo día y el pago actual queda anulado con el motivo.`),
    h("div", { class: "rejilla r4" }, otros.map((p) => h("button", { type: "button", class: "opcion", "aria-pressed": String(C.planId === p.id), onclick: () => elegir(p) },
      h("b", {}, p.nombre), h("span", { class: "peq sub" }, `${p.duracionDias} ${p.duracionDias === 1 ? "día" : "días"}`), h("span", { class: "precio" }, pesos(p.precio))))),
    C.planId ? [
      h("div", { class: "fila" }, MEDIOS.map(([v, t]) => h("button", { type: "button", class: "chip", "aria-pressed": String(C.medio === v), onclick: () => { C.medio = v; C.error = null; render(); } }, t))),
      C.medio !== "EFECTIVO" ? h("div", { class: "campo campo-ref" }, h("label", { class: "et", for: "ref-c" }, "Referencia del comprobante"),
        h("input", { id: "ref-c", type: "text", autocomplete: "off", value: C.referencia, oninput: (ev) => { C.referencia = ev.target.value; } }),
        h("span", { class: "ayuda" }, "Puede ser la misma del pago actual: al anularlo queda libre.")) : null,
      pv ? h("div", { class: "linea-fechas" }, h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Inicia"), h("strong", {}, corta(pv.inicia))),
        h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Vence"), h("strong", {}, corta(pv.vence))),
        h("div", { class: "dato" }, h("span", { class: "sub peq" }, "Valor"), h("strong", {}, pesos(pv.valor)))) : h("p", { class: "vacio" }, "Calculando con el servidor…"),
      pv ? aviso("aviso", h("b", {}, diferenciaTexto(pv.diferencia)), " Lo calculó el servidor: precio del plan nuevo menos lo que ya pagó.") : null,
      h("div", { class: "campo" }, h("label", { class: "et", for: "motivo-c" }, "Motivo del cambio"),
        h("textarea", { id: "motivo-c", oninput: (ev) => { C.motivo = ev.target.value; C.motivoEditado = true; } }, C.motivo))] : null,
    C.error ? aviso("mal", C.error) : null,
    h("div", { class: "fila" },
      h("button", { type: "button", class: "btn btn-confirmar", disabled: !pv, onclick: (ev) => confirmarCambio(ev.currentTarget) }, pv ? `Cambiar a ${pv.plan.nombre}` : "Elija el plan nuevo"),
      h("button", { type: "button", class: "btn-sec", onclick: () => { S.hist.cambio = null; render(); } }, "Cancelar")));
}
function pHistorial() {
  const H = S.hist;
  if (H.numero && !H.datos && !H.error) una("hist", cargarHistorial);
  const buscar = buscadorDoc(H, () => { H.datos = null; H.error = null; H.aviso = null; void cargarHistorial(); }, "Ver historial");
  if (!H.datos) return marco(h("div", {}, h("h1", {}, "Socios e historial"), h("div", { class: "sub mt-6" }, "Pagos vigentes y anulados de un socio. Solo el administrador lo ve.")), buscar, H.error ? aviso("mal", H.error) : null);
  const d = H.datos, e = d.estado;
  const vigentes = d.pagos.filter((p) => p.estado === "VIGENTE");
  const ultimo = vigentes.slice().sort((a, b) => (a.inicia < b.inicia ? 1 : a.inicia > b.inicia ? -1 : a.registradoEl < b.registradoEl ? 1 : -1))[0];
  const estadoPastilla = e.estado === "ACTIVO" ? pastilla("ok", `Activo hasta el ${corta(e.venceEl)}`, "pastilla-grande") : e.estado === "VENCIDO" ? pastilla("mal", `Vencido desde el ${corta(e.venceEl)}`, "pastilla-grande") : pastilla("neutro", "Sin membresía", "pastilla-grande");
  const filas = d.pagos.map((p) => h("tr", { class: p.estado === "VIGENTE" ? null : "anulada" },
    h("td", {}, h("b", {}, p.plan)), h("td", {}, `${corta(p.inicia)} – ${corta(p.vence)}`), h("td", {}, (MEDIOS.find(([v]) => v === p.medio) || [p.medio, p.medio])[1]), h("td", {}, p.referencia || "—"),
    h("td", { class: "der" }, pesos(p.valor)), h("td", {}, `${p.registradoPor} · ${horaDe(p.registradoEl)}`),
    h("td", {}, pastilla(p.estado === "VIGENTE" ? "ok" : "neutro", p.estado === "VIGENTE" ? "Vigente" : "Anulado"), p.anulacion ? h("div", { class: "mpeq sub mt-6" }, `Anuló ${p.anulacion.anuladoPor}: ${p.anulacion.motivo}`) : null)));
  const motivo = h("textarea", { id: "motivo", placeholder: "Ej.: se registró Mensual y el socio pagó Quincenal", class: H.falta ? "error-campo" : null, oninput: (ev) => { H.motivo = ev.target.value; } }, H.motivo);
  return marco(
    buscar,
    h("div", { class: "hoja cab-historial" }, anilloEstado(e, 112),
      h("div", { class: "datos-socio" }, h("h1", {}, d.socio.nombreCompleto), h("div", { class: "sub tab mt-6" }, d.socio.documentoEnmascarado), h("div", { class: "sub peq" }, `Autorizó el tratamiento de datos el ${horaDe(d.socio.autorizoEl)}`)),
      estadoPastilla),
    h("section", { class: "hoja", "aria-labelledby": "t-h" },
      h("div", { class: "cabecera hoja-centro" }, h("h2", { id: "t-h" }, "Historial de pagos"),
        h("div", { class: "fila" },
          h("button", { type: "button", class: "btn-sec", disabled: !ultimo || !!H.cambio, onclick: () => abrirCambio(ultimo) }, "Cambiar plan"),
          h("button", { type: "button", class: "btn-sec peligro", disabled: !ultimo || H.confirmando, onclick: () => { H.confirmando = true; H.cambio = null; H.aviso = null; H.cambiado = null; render(); const t = document.getElementById("motivo"); if (t) t.focus(); } }, "Anular último pago"))),
      d.pagos.length ? h("div", { class: "mt-12" }, tabla(["Plan", "Periodo", "Medio", "Referencia", ">Valor", "Registró", "Estado"], filas)) : h("p", { class: "vacio" }, "Todavía no tiene pagos.")),
    H.cambio && ultimo ? panelCambio() : null,
    H.confirmando && ultimo ? h("section", { class: "hoja pila anular", "aria-labelledby": "t-an" },
      h("h2", { id: "t-an" }, `¿Anular el pago ${ultimo.plan} del ${corta(ultimo.inicia)} al ${corta(ultimo.vence)}?`),
      h("p", { class: "sub peq sin-margen" }, "El pago no se borra. Queda anulado con el motivo, quién lo anuló y la fecha; deja de sumar en los ingresos y la membresía se recalcula. Solo se puede anular el último pago vigente (RN-07)."),
      h("div", { class: "campo" }, h("label", { class: "et", for: "motivo" }, "Motivo de la anulación"), motivo,
        H.falta ? h("div", { class: "msg-error", role: "alert" }, ico("alerta", 18), "Escriba el motivo (al menos 5 caracteres) para poder anular.") : null),
      h("div", { class: "fila" }, h("button", { type: "button", class: "btn btn-peligro", onclick: () => anularUltimo(ultimo) }, "Anular pago"),
        h("button", { type: "button", class: "btn-sec", onclick: () => { H.confirmando = false; H.falta = false; render(); } }, "No anular"))) : null,
    H.error ? aviso("mal", H.error) : null,
    H.aviso ? aviso("aviso", "Pago anulado y guardado con el motivo. La membresía ya se recalculó; si hace falta, registre el plan correcto.") : null,
    H.cambiado ? aviso("ok", h("b", {}, `Plan cambiado a ${H.cambiado.nuevo.plan}. `), `Queda activo del ${corta(H.cambiado.nuevo.inicia)} al ${corta(H.cambiado.nuevo.vence)}. ${diferenciaTexto(H.cambiado.diferencia)}`) : null);
}

/* --- Reportes (CU-07, RF-05) ---------------------------------------------------------------------- */
async function cargarReporte() {
  const R = S.reporte;
  const r = await llamar(`/reportes/ingresos?${new URLSearchParams({ desde: R.desde, hasta: R.hasta })}`);
  R.datos = r.estado === 200 ? r.datos : null;
  R.error = r.estado === 200 ? null : mensajeDe(r);
  render();
}
function pReportes() {
  const R = S.reporte;
  if (!R.desde) { const hoy = new Date(); R.desde = aISO(new Date(hoy.getFullYear(), hoy.getMonth(), 1)); R.hasta = hoyISO(); una("reporte", cargarReporte); }
  if (!S.venc.filas && !S.venc.error) una("venc", () => cargarVencimientos().then(render));
  const d = R.datos;
  const desde = h("input", { id: "desde", type: "date", value: R.desde });
  const hasta = h("input", { id: "hasta", type: "date", value: R.hasta });
  let contenido = h("p", { class: "vacio" }, "Cargando…");
  if (R.error) contenido = aviso("mal", R.error);
  else if (d) {
    const barra = h("div", { class: "barra", role: "img", "aria-label": "Reparto de ingresos por medio de pago" }, d.porMedio.filter((m) => m.total > 0).map((m) => {
      const seg = h("span", {}); seg.style.setProperty("flex", String(m.total)); seg.style.setProperty("background", MEDIO_COLOR[m.medio]); return seg;
    }));
    contenido = [
      h("div", { class: "resumen" }, h("div", {}, h("div", { class: "sub peq" }, `Ingresos del ${corta(d.desde)} al ${corta(d.hasta)}`), h("div", { class: "total" }, pesos(d.total))),
        h("div", { class: "sub" }, `${d.pagos} ${d.pagos === 1 ? "pago" : "pagos"}${d.anulados === 1 ? " · 1 anulado que no se cuenta" : d.anulados ? ` · ${d.anulados} anulados que no se cuentan` : ""}`)),
      d.total > 0 ? barra : null,
      h("div", { class: "mt-14" }, tabla(["Medio de pago", ">Pagos", ">Total", ">Parte"], d.porMedio.map((m) => h("tr", {},
        h("td", {}, leyendaPunto(MEDIO_COLOR[m.medio]), h("b", {}, MEDIOS.find(([v]) => v === m.medio)[1])), h("td", { class: "der" }, m.pagos), h("td", { class: "der" }, pesos(m.total)),
        h("td", { class: "der" }, d.total ? `${(m.total / d.total * 100).toLocaleString("es-CO", { maximumFractionDigits: 1 })} %` : "—"))), "tabla-520"))];
  }
  return marco(
    h("div", { class: "cabecera" }, h("div", {}, h("h1", {}, "Reporte de ingresos"), h("div", { class: "sub" }, "Solo el administrador lo ve. Los pagos anulados no suman.")),
      h("form", { class: "fila fila-abajo", novalidate: true, onsubmit: (e) => { e.preventDefault(); R.desde = desde.value; R.hasta = hasta.value; R.datos = null; R.error = null; render(); void cargarReporte(); } },
        campo("desde", "Desde", desde), campo("hasta", "Hasta", hasta), h("button", { class: "btn", type: "submit" }, "Ver reporte"))),
    h("section", { class: "hoja", "aria-label": "Totales del periodo" }, contenido),
    h("section", { class: "hoja", "aria-labelledby": "t-v" }, h("div", { class: "cabecera hoja-centro" }, h("h2", { id: "t-v" }, "Próximos vencimientos")), vencimientosTabla()));
}
function leyendaPunto(color) { const i = h("span", { class: "punto" }); i.style.setProperty("background", color); return i; }

/* --- Planes (CU-05, RN-08, RN-09) ------------------------------------------------------------------------ */
async function cargarTodosLosPlanes() {
  const G = S.planes;
  const r = await llamar("/planes?todos=true");
  G.todos = r.estado === 200 ? r.datos : null;
  G.error = r.estado === 200 ? null : mensajeDe(r);
  render();
}
async function trasCambiarPlanes() { S.planes.todos = null; await cargarPlanes(); await cargarTodosLosPlanes(); }
async function activarPlan(plan, activo) {
  const G = S.planes;
  G.aviso = null; G.error = null;
  const r = await llamar(`/planes/${encodeURIComponent(plan.id)}`, { metodo: "PATCH", cuerpo: { activo } });
  if (r.estado === 200) G.aviso = activo ? `${plan.nombre} vuelve a ofrecerse en Registrar pago.` : `${plan.nombre} quedó desactivado: ya no se ofrece en Registrar pago. Las membresías que ya lo pagaron no cambian.`;
  else G.error = r.datos && r.datos.codigo === "ULTIMO_PLAN_ACTIVO" ? "No se puede desactivar el único plan activo: sin planes activos no se puede cobrar." : `${plan.nombre}: ${mensajeDe(r)}`;
  await trasCambiarPlanes();
}
function formPlan() {
  const G = S.planes;
  const nombre = h("input", { id: "p-nombre", type: "text", maxlength: "40", autocomplete: "off", placeholder: "Semestral" });
  const dias = h("input", { id: "p-dias", type: "text", inputmode: "numeric", autocomplete: "off", placeholder: "180", class: "tab-num" });
  const precio = h("input", { id: "p-precio", type: "text", inputmode: "numeric", autocomplete: "off", placeholder: "380.000", class: "tab-num" });
  const boton = h("button", { class: "btn", type: "submit" }, "Crear plan");
  return h("form", { class: "hoja pila form-cuenta", novalidate: true, onsubmit: async (e) => {
    e.preventDefault();
    const duracionDias = Number(dias.value.replace(/\D/g, "")), valor = Number(precio.value.replace(/\D/g, ""));
    if (nombre.value.trim().length < 2 || !duracionDias || !valor) { G.error = "Escriba el nombre, la duración en días y el precio. La duración y el precio deben ser mayores que cero."; return render(); }
    ocupado(boton, true);
    const r = await llamar("/planes", { metodo: "POST", cuerpo: { nombre: nombre.value.trim(), duracionDias, precio: valor } });
    if (r.estado === 201) { G.creando = false; G.error = null; G.aviso = `Se creó el plan ${r.datos.nombre} y ya se ofrece en Registrar pago.`; await trasCambiarPlanes(); }
    else { G.error = r.estado === 409 ? "Ya hay un plan con ese nombre." : mensajeDe(r); render(); }
  } },
    h("h2", {}, "Plan nuevo"),
    h("div", { class: "rejilla r3" }, campo("p-nombre", "Nombre", nombre), campo("p-dias", "Duración (días)", dias), campo("p-precio", "Precio", precio)),
    h("div", { class: "fila" }, boton, h("button", { type: "button", class: "btn-sec", onclick: () => { G.creando = false; G.error = null; render(); } }, "Cancelar")));
}
function pPlanes() {
  const G = S.planes;
  if (!G.todos && !G.error) una("planes", cargarTodosLosPlanes);
  const lista = G.todos || [];
  const entradas = lista.map((p) => h("input", { type: "text", inputmode: "numeric", "aria-label": `Precio del plan ${p.nombre}`, value: Number(p.precio).toLocaleString("es-CO"), "data-plan": p.id }));
  const boton = h("button", { class: "btn", type: "submit" }, "Guardar precios");
  const guardar = async (e) => {
    e.preventDefault();
    ocupado(boton, true); G.aviso = null; G.error = null;
    let cambiados = 0;
    for (const entrada of entradas) {
      const plan = lista.find((p) => p.id === entrada.dataset.plan);
      const precio = Number(entrada.value.replace(/\D/g, ""));
      if (!precio || precio === plan.precio) continue;
      const r = await llamar(`/planes/${encodeURIComponent(plan.id)}`, { metodo: "PATCH", cuerpo: { precio } });
      if (r.estado !== 200) { G.error = `${plan.nombre}: ${mensajeDe(r)}`; break; }
      cambiados += 1;
    }
    if (!G.error) G.aviso = cambiados === 1 ? "Se guardó 1 precio." : cambiados ? `Se guardaron ${cambiados} precios.` : "No había precios distintos para guardar.";
    await trasCambiarPlanes();
  };
  const filas = lista.map((p, i) => h("tr", { class: p.activo ? null : "anulada" },
    h("td", {}, h("b", {}, p.nombre)), h("td", {}, `${p.duracionDias} ${p.duracionDias === 1 ? "día" : "días"}`),
    h("td", {}, h("div", { class: "precio-celda" }, h("span", { class: "sub" }, "$"), entradas[i])),
    h("td", {}, p.activo ? pastilla("ok", "Activo") : pastilla("neutro", "Desactivado")),
    h("td", { class: "der" }, h("button", { type: "button", class: "btn-sec" + (p.activo ? " peligro" : ""), onclick: () => activarPlan(p, !p.activo) }, p.activo ? "Desactivar" : "Activar"))));
  return marco(
    h("div", { class: "cabecera" }, h("div", {}, h("h1", {}, "Planes"), h("div", { class: "sub" }, "Los cambios solo afectan los pagos nuevos; las membresías ya pagadas no cambian (RN-08).")),
      G.creando ? null : h("button", { type: "button", class: "btn", onclick: () => { G.creando = true; G.aviso = null; G.error = null; render(); const i = document.getElementById("p-nombre"); if (i) i.focus(); } }, "Crear plan")),
    G.creando ? formPlan() : null,
    h("form", { class: "hoja", novalidate: true, onsubmit: guardar },
      G.todos ? tabla(["Plan", "Duración", "Precio", "Estado", ">Acciones"], filas, "tabla-600") : h("p", { class: "vacio" }, "Cargando…"),
      h("div", { class: "fila mt-16" }, boton),
      G.aviso ? h("div", { class: "mt-12" }, aviso("ok", G.aviso)) : null,
      G.error ? h("div", { class: "mt-12" }, aviso("mal", G.error)) : null),
    h("p", { class: "sub peq sin-margen" }, "Un plan no se borra: se desactiva (RN-09). Deja de ofrecerse en Registrar pago y se puede volver a activar. Siempre debe quedar al menos un plan activo."));
}

/* --- Personal (CU-06, RF-09) ---------------------------------------------------------------------- */
async function cargarPersonal() {
  const X = S.personal;
  const r = await llamar("/personal");
  X.cuentas = r.estado === 200 ? r.datos : null;
  X.error = r.estado === 200 ? null : mensajeDe(r);
  render();
}
function formCuenta() {
  const X = S.personal;
  const nombre = h("input", { id: "c-nombre", type: "text", maxlength: "80", autocomplete: "off" });
  const correo = h("input", { id: "c-correo", type: "email", autocomplete: "off" });
  const rol = h("select", { id: "c-rol" }, h("option", { value: "RECEPCIONISTA" }, "Recepcionista"), h("option", { value: "ADMINISTRADOR" }, "Administrador"));
  const clave = h("input", { id: "c-clave", type: "password", autocomplete: "new-password", minlength: "12" });
  const boton = h("button", { class: "btn", type: "submit" }, "Crear cuenta");
  return h("form", { class: "hoja pila form-cuenta", novalidate: true, onsubmit: async (e) => {
    e.preventDefault();
    if (nombre.value.trim().length < 2 || !correo.value.includes("@") || clave.value.length < 12) { X.error = "Escriba el nombre, un correo válido y una contraseña inicial de al menos 12 caracteres."; return render(); }
    ocupado(boton, true);
    const r = await llamar("/personal", { metodo: "POST", cuerpo: { nombre: nombre.value.trim(), correo: correo.value.trim(), rol: rol.value, contrasena: clave.value } });
    if (r.estado === 201) { X.aviso = `Se creó la cuenta de ${r.datos.nombre}. Entréguele la contraseña inicial en persona.`; X.creando = false; X.error = null; await cargarPersonal(); }
    else { X.error = r.estado === 409 ? "Ya hay una cuenta con ese correo." : mensajeDe(r); render(); }
  } },
    h("h2", {}, "Cuenta nueva"),
    h("div", { class: "rejilla r2" }, campo("c-nombre", "Nombre", nombre), campo("c-correo", "Correo", correo), campo("c-rol", "Rol", rol),
      campo("c-clave", "Contraseña inicial", clave, "Mínimo 12 caracteres. Se guarda cifrada; nadie la puede volver a ver.")),
    h("div", { class: "fila" }, boton, h("button", { type: "button", class: "btn-sec", onclick: () => { X.creando = false; X.error = null; render(); } }, "Cancelar")));
}
function pPersonal() {
  const X = S.personal;
  if (!X.cuentas && !X.error) una("personal", cargarPersonal);
  const desbloquear = async (c) => {
    const r = await llamar(`/personal/${encodeURIComponent(c.id)}/desbloqueo`, { metodo: "POST" });
    if (r.estado === 200) { X.aviso = `La cuenta de ${c.nombre} quedó desbloqueada.`; await cargarPersonal(); }
    else { X.error = mensajeDe(r); render(); }
  };
  const filas = (X.cuentas || []).map((c) => h("tr", {},
    h("td", {}, h("div", { class: "con-avatar" }, h("span", { class: "avatar avatar-p" }, c.nombre.charAt(0).toUpperCase()), h("b", {}, c.nombre))), h("td", {}, c.correo), h("td", {}, ROLES[c.rol] || c.rol),
    h("td", {}, c.bloqueada ? pastilla("mal", "Bloqueada") : c.activa ? pastilla("ok", "Activa") : pastilla("neutro", "Inactiva"), c.bloqueada ? h("div", { class: "mpeq sub mt-6" }, `5 intentos fallidos · se desbloquea sola a las ${horaDe(c.bloqueadaHasta).slice(-5)}`) : null),
    h("td", { class: "der" }, c.bloqueada ? h("button", { type: "button", class: "btn-sec", onclick: () => desbloquear(c) }, "Desbloquear") : null)));
  return marco(
    h("div", { class: "cabecera" }, h("div", {}, h("h1", {}, "Cuentas del personal"), h("div", { class: "sub" }, "Cada persona tiene su propia cuenta. Las contraseñas nunca se muestran.")),
      X.creando ? null : h("button", { type: "button", class: "btn", onclick: () => { X.creando = true; X.aviso = null; render(); const i = document.getElementById("c-nombre"); if (i) i.focus(); } }, "Crear cuenta")),
    X.creando ? formCuenta() : null,
    h("section", { class: "hoja" }, X.cuentas ? tabla(["Nombre", "Correo", "Rol", "Estado", ">Acciones"], filas) : h("p", { class: "vacio" }, "Cargando…")),
    X.error ? aviso("mal", X.error) : null,
    X.aviso ? aviso("ok", X.aviso) : null);
}

/* --- Acceso denegado y enrutador ------------------------------------------------------------ */
function pDenegado() {
  return marco(h("div", { class: "hoja pila form-cuenta" }, pastilla("mal", "Acceso denegado · 403"), h("h1", {}, "Esta sección es solo para el administrador"),
    h("p", { class: "sub sin-margen" }, `«${TITULOS[rutaActual()]}» no está disponible para su cuenta. El servidor también la bloquea si se escribe la dirección a mano (RNF-05).`),
    h("div", {}, h("a", { class: "btn", href: "#recepcion" }, "Volver a recepción"))));
}
const PANTALLAS = { recepcion: pRecepcion, pago: pPago, socio: pSocio, vencimientos: pVencimientos, historial: pHistorial, reportes: pReportes, planes: pPlanes, personal: pPersonal };
const rutaActual = () => (location.hash || "#recepcion").slice(1);
function ir(r) { if (rutaActual() === r) render(); else location.hash = r; }
let mensajeLogin = "";
function render() {
  const raiz = document.getElementById("app");
  let r = rutaActual();
  if (!sesion) { raiz.replaceChildren(pLogin(mensajeLogin)); document.title = "FitManage · Iniciar sesión"; return; }
  if (!PANTALLAS[r]) r = "recepcion";
  const vista = RUTAS_ADMIN.includes(r) && !esAdmin() ? pDenegado() : PANTALLAS[r]();
  raiz.replaceChildren(vista);
  document.title = `FitManage · ${TITULOS[r]}`;
  animarAnillos(raiz);
}
function cerrarSesion(motivo) {
  sesion = null;
  planes = [];
  S = ESTADO();
  mensajeLogin = motivo || "";
  history.replaceState(null, "", location.pathname);
  render();
}
window.addEventListener("hashchange", () => {
  // Al cambiar de sección los campos quedan en blanco, salvo cuando un botón lleva el socio a la
  // siguiente pantalla (Registrar socio, Registrar pago o Ver historial desde una consulta).
  if (!llevarDatos) S = ESTADO();
  llevarDatos = false;
  mensajeLogin = ""; render(); window.scrollTo(0, 0); const m = document.getElementById("contenido"); if (m) m.focus({ preventScroll: true }); });
window.addEventListener("online", render);
window.addEventListener("offline", render);
render();
