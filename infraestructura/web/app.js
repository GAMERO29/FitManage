// Recepción de FitManage (Guía 16, ADR N.° 16). Consume la API /api/v1 del mismo origen.
// El token de acceso vive solo en esta variable (ADR N.° 06: nunca en localStorage). Si vence,
// se renueva una vez con la cookie HttpOnly; si no se puede, se vuelve a pedir la sesión.
// Todo dato que llega de la API se escribe con textContent, nunca como HTML.

const API = "/api/v1";
let token = null;
let planes = [];
let consultado = null; // { tipo, numero }
let clavePago = null; // Idempotency-Key del pago en curso: un doble clic no cobra dos veces

const $ = (id) => document.getElementById(id);
const fecha = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const pesos = new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 });
const legible = (iso) => fecha.format(new Date(`${iso}T00:00:00Z`));
const ROLES = { RECEPCIONISTA: "Recepción", ADMINISTRADOR: "Administración", ENTRENADOR: "Entrenador" };

async function llamar(ruta, { metodo = "GET", cuerpo, cabeceras = {}, renovar = true } = {}) {
  const respuesta = await fetch(API + ruta, {
    method: metodo,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(cuerpo ? { "Content-Type": "application/json" } : {}),
      ...cabeceras,
    },
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  if (respuesta.status === 401 && token && renovar) {
    if (await renovarSesion()) return llamar(ruta, { metodo, cuerpo, cabeceras, renovar: false });
    cerrarSesion("La sesión venció. Vuelve a iniciar sesión.");
  }
  const datos = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
  return { estado: respuesta.status, datos };
}

async function renovarSesion() {
  const r = await fetch(`${API}/auth/renovacion`, { method: "POST", credentials: "same-origin" });
  if (!r.ok) return false;
  token = (await r.json()).tokenAcceso;
  return true;
}

function mensajeDe({ estado, datos }) {
  if (!datos) return `El servidor respondió ${estado}. Intenta de nuevo.`;
  const detalle = (datos.errores || []).map((e) => e.mensaje).join(" ");
  return [datos.title, detalle || datos.detail].filter(Boolean).join(". ");
}

function mostrarError(elemento, texto) {
  elemento.textContent = texto || "";
}

function ocupado(form, si) {
  for (const boton of form.querySelectorAll("button")) boton.disabled = si;
}

// --- Sesión -----------------------------------------------------------------------------
$("form-ingreso").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.currentTarget;
  const error = form.querySelector("[data-error]");
  if (!form.reportValidity()) return;
  ocupado(form, true);
  mostrarError(error, "");
  try {
    const r = await llamar("/auth/token", {
      metodo: "POST",
      cuerpo: { correo: form.correo.value.trim(), contrasena: form.contrasena.value },
      renovar: false,
    });
    if (r.estado !== 200) return mostrarError(error, mensajeDe(r));
    token = r.datos.tokenAcceso;
    form.reset();
    $("rol").textContent = ROLES[r.datos.rol] || r.datos.rol;
    $("sesion").hidden = false;
    $("pantalla-ingreso").hidden = true;
    $("pantalla-recepcion").hidden = false;
    $("form-consulta").numero.focus();
    const p = await llamar("/planes");
    planes = p.estado === 200 ? p.datos : [];
  } catch {
    mostrarError(error, "No hay conexión con FitManage. Revisa el internet de recepción.");
  } finally {
    ocupado(form, false);
  }
});

function cerrarSesion(motivo) {
  token = null;
  consultado = null;
  $("resultado").replaceChildren();
  cerrarPaneles();
  $("sesion").hidden = true;
  $("pantalla-recepcion").hidden = true;
  $("pantalla-ingreso").hidden = false;
  mostrarError($("form-ingreso").querySelector("[data-error]"), motivo || "");
}
$("salir").addEventListener("click", () => cerrarSesion());

// --- Consulta de estado (CU-03) ----------------------------------------------------------
async function consultar(tipo, numero) {
  const error = $("error-consulta");
  mostrarError(error, "");
  cerrarPaneles();
  const r = await llamar(`/estados/${encodeURIComponent(tipo)}/${encodeURIComponent(numero)}`);
  consultado = { tipo, numero };
  if (r.estado === 200) return pintarEstado(r.datos);
  $("resultado").replaceChildren();
  if (r.estado === 404) return pintarNoEncontrado(tipo, numero);
  if (r.estado !== 401) mostrarError(error, mensajeDe(r));
}

$("form-consulta").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.currentTarget;
  if (!form.reportValidity()) return;
  ocupado(form, true);
  try {
    await consultar(form.tipo.value, form.numero.value.trim());
  } catch {
    mostrarError($("error-consulta"), "No hay conexión con FitManage. Revisa el internet de recepción.");
  } finally {
    ocupado(form, false);
  }
});

const VEREDICTOS = { ACTIVO: "Puede entrar", VENCIDO: "Membresía vencida", SIN_MEMBRESIA: "Sin membresía" };

function tarjeta(estado) {
  const nodo = $("plantilla-estado").content.firstElementChild.cloneNode(true);
  nodo.dataset.estado = estado;
  nodo.querySelector(".estado-veredicto").textContent = VEREDICTOS[estado] || estado;
  return nodo;
}

function boton(texto, clase, alHacerClic) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = clase;
  b.textContent = texto;
  b.addEventListener("click", alHacerClic);
  return b;
}

function pintarEstado(e) {
  const nodo = tarjeta(e.estado);
  nodo.querySelector(".estado-nombre").textContent = e.nombreCorto;
  nodo.querySelector(".estado-documento").textContent = e.documentoEnmascarado;
  const detalle = nodo.querySelector(".estado-detalle");
  if (e.estado === "ACTIVO") {
    const dias = e.diasRestantes === 1 ? "Hoy es su último día" : `Le quedan ${e.diasRestantes} días`;
    detalle.textContent = `${dias}: vence el ${legible(e.venceEl)}.`;
  } else if (e.estado === "VENCIDO") {
    detalle.textContent = `Venció el ${legible(e.venceEl)} (${e.diasMora} ${e.diasMora === 1 ? "día" : "días"} de mora).`;
  } else {
    detalle.textContent = "Todavía no tiene ningún pago registrado.";
  }
  const etiqueta = e.estado === "ACTIVO" ? "Renovar" : "Registrar pago";
  nodo.querySelector(".acciones").append(boton(etiqueta, e.estado === "ACTIVO" ? "secundario" : "principal", abrirPago));
  $("resultado").replaceChildren(nodo);
}

function pintarNoEncontrado(tipo, numero) {
  const nodo = tarjeta("NO_ENCONTRADO");
  nodo.querySelector(".estado-veredicto").textContent = "No está registrado";
  nodo.querySelector(".estado-documento").textContent = `${tipo} ${numero}`;
  nodo.querySelector(".estado-detalle").textContent = "No hay ningún socio con ese documento.";
  nodo.querySelector(".acciones").append(boton("Registrar socio", "principal", abrirSocio));
  $("resultado").replaceChildren(nodo);
}

// --- Registro de pago (CU-04) ------------------------------------------------------------
function cerrarPaneles() {
  $("panel-pago").hidden = true;
  $("panel-socio").hidden = true;
}
for (const b of document.querySelectorAll("[data-cerrar]")) b.addEventListener("click", cerrarPaneles);

function abrirPago() {
  const form = $("form-pago");
  form.reset();
  mostrarError(form.querySelector("[data-error]"), "");
  const opciones = planes.map((p) => {
    const o = document.createElement("option");
    o.value = p.id;
    o.textContent = `${p.nombre} · ${pesos.format(p.precio)} · ${p.duracionDias} ${p.duracionDias === 1 ? "día" : "días"}`;
    return o;
  });
  form.planId.replaceChildren(...opciones);
  actualizarReferencia();
  clavePago = crypto.randomUUID();
  $("panel-socio").hidden = true;
  $("panel-pago").hidden = false;
  form.planId.focus();
}

function actualizarReferencia() {
  const form = $("form-pago");
  const enEfectivo = form.medio.value === "EFECTIVO";
  $("campo-referencia").hidden = enEfectivo;
  form.referencia.required = !enEfectivo;
}
$("form-pago").medio.addEventListener("change", actualizarReferencia);

$("form-pago").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.currentTarget;
  const error = form.querySelector("[data-error]");
  if (!form.reportValidity() || !consultado) return;
  ocupado(form, true);
  mostrarError(error, "");
  const cuerpo = {
    tipoDocumento: consultado.tipo,
    numeroDocumento: consultado.numero,
    planId: form.planId.value,
    medio: form.medio.value,
  };
  if (form.medio.value !== "EFECTIVO") cuerpo.referencia = form.referencia.value.trim();
  try {
    const r = await llamar("/pagos", { metodo: "POST", cuerpo, cabeceras: { "Idempotency-Key": clavePago } });
    if (r.estado !== 201) return mostrarError(error, mensajeDe(r));
    clavePago = null;
    await consultar(consultado.tipo, consultado.numero);
    const nota = document.createElement("p");
    nota.className = "nota";
    nota.textContent = `Pago registrado: ${r.datos.plan} por ${pesos.format(r.datos.valor)}, del ${legible(r.datos.inicia)} al ${legible(r.datos.vence)}.`;
    $("resultado").append(nota);
  } catch {
    mostrarError(error, "No hay conexión. El pago no quedó confirmado: vuelve a intentar con el mismo botón.");
  } finally {
    ocupado(form, false);
  }
});

// --- Registro de socio (CU-02) -----------------------------------------------------------
function abrirSocio() {
  const form = $("form-socio");
  form.reset();
  mostrarError(form.querySelector("[data-error]"), "");
  $("documento-socio").textContent = `Documento: ${consultado.tipo} ${consultado.numero}`;
  $("panel-pago").hidden = true;
  $("panel-socio").hidden = false;
  form.nombres.focus();
}

$("form-socio").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const form = evento.currentTarget;
  const error = form.querySelector("[data-error]");
  if (!form.reportValidity() || !consultado) return;
  ocupado(form, true);
  mostrarError(error, "");
  try {
    const r = await llamar("/socios", {
      metodo: "POST",
      cuerpo: {
        tipoDocumento: consultado.tipo,
        numeroDocumento: consultado.numero,
        nombres: form.nombres.value.trim(),
        apellidos: form.apellidos.value.trim(),
        telefono: form.telefono.value.trim(),
        autorizaTratamientoDatos: form.autoriza.checked,
      },
    });
    if (r.estado !== 201) return mostrarError(error, mensajeDe(r));
    await consultar(consultado.tipo, consultado.numero);
  } catch {
    mostrarError(error, "No hay conexión con FitManage. Revisa el internet de recepción.");
  } finally {
    ocupado(form, false);
  }
});
