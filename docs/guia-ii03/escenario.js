// Guía II-03 · Escenario reproducible del incremento de auditoría sobre el aplicativo real.
// Servidor local (gunicorn + PostgreSQL 16, base nueva) con datos ficticios.
// Uso: node escenario.js [url]. Imprime una línea por comprobación (A1…A8) y guarda capturas.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
const DOC = '1090000011';
const CLAVE = 'clave-de-demo-local';
const res = [];
const anotar = (id, ok, detalle) => { res.push(ok); console.log(`${id} ${ok ? 'PASA' : 'FALLA'} · ${detalle}`); };
async function api(ruta, { metodo = 'GET', token, cuerpo, clave } = {}) {
  const c = { 'Content-Type': 'application/json' };
  if (token) c.Authorization = `Bearer ${token}`;
  if (clave) c['Idempotency-Key'] = clave;
  const r = await fetch(URL + '/api/v1' + ruta, { method: metodo, headers: c, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  let json = null; try { json = await r.json(); } catch { /* sin cuerpo */ }
  return { estado: r.status, json };
}
const token = async (correo) => (await api('/auth/token', { metodo: 'POST', cuerpo: { correo, contrasena: CLAVE } })).json.tokenAcceso;
const hoy = new Date().toLocaleDateString('en-CA', { timeZone: 'America/Bogota' });

(async () => {
  const admin = await token('admin@demo.local');
  for (const [nombre, correo] of [['Laura Demo', 'laura@demo.local'], ['Diana Demo', 'diana@demo.local']]) {
    await api('/personal', { metodo: 'POST', token: admin, cuerpo: { nombre, correo, rol: 'RECEPCIONISTA', contrasena: CLAVE } });
  }
  const laura = await token('laura@demo.local');
  const diana = await token('diana@demo.local');
  const planes = (await api('/planes', { token: admin })).json;
  const mensual = planes.find((p) => p.nombre === 'Mensual');
  const diario = planes.find((p) => p.nombre === 'Diario');

  // A1 · Las cuatro operaciones de dinero del día, cada una con su actor.
  await api('/socios', { metodo: 'POST', token: laura, cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, nombres: 'Ana', apellidos: 'Prueba Demo', telefono: '3001234567', autorizaTratamientoDatos: true } });
  const p1 = await api('/pagos', { metodo: 'POST', token: laura, clave: crypto.randomUUID(), cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, planId: mensual.id, medio: 'NEQUI', referencia: 'M123456' } });
  const cambio = await api(`/pagos/${p1.json.id}/cambio-de-plan`, { metodo: 'POST', token: diana, cuerpo: { planId: diario.id, medio: 'EFECTIVO', motivo: 'La socia pidió un plan más corto' } });
  const anula = await api(`/pagos/${cambio.json.nuevo.id}`, { metodo: 'PATCH', token: admin, cuerpo: { estado: 'ANULADO', motivo: 'Prueba del escenario de auditoría' } });
  const precio = await api(`/planes/${diario.id}`, { metodo: 'PATCH', token: admin, cuerpo: { precio: 9000 } });
  const a = (await api(`/auditoria?desde=${hoy}&hasta=${hoy}`, { token: admin })).json;
  const tipos = a.eventos.map((e) => `${e.tipo}(${e.actor})`).reverse().join(', ');
  anotar('A1', [p1.estado, cambio.estado, anula.estado, precio.estado].join() === '201,201,200,200' && a.total === 4, `${a.total} eventos: ${tipos}`);

  // A2 · El evento no lleva el documento ni el teléfono; el socio llega enmascarado al consultar.
  const crudo = JSON.stringify(a.eventos.map((e) => e.detalle));
  anotar('A2', !crudo.includes(DOC) && !crudo.includes('3001234567') && a.eventos.filter((e) => e.socio).every((e) => e.socio.documentoEnmascarado === 'CC ******0011'), `socio en la consulta: ${JSON.stringify(a.eventos.find((e) => e.socio)?.socio)}`);

  // A3 · La recepcionista no consulta la auditoría, ni por la API ni por la pantalla.
  const r3 = await api(`/auditoria?desde=${hoy}&hasta=${hoy}`, { token: laura });
  anotar('A3', r3.estado === 403, `GET /auditoria con el token de Laura: ${r3.estado}`);

  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 860 } });
  const p = await ctx.newPage();
  const errores = []; p.on('pageerror', (e) => errores.push(String(e)));
  const entrar = async (pag, correo) => { await pag.goto(URL + '/'); await pag.fill('#correo', correo); await pag.fill('#clave', CLAVE); await pag.click('button:has-text("Entrar")'); await pag.waitForSelector('h1:has-text("Recepción")'); };

  // A4 · El administrador ve la pantalla, con la devolución sobre un pago ajeno señalada.
  await entrar(p, 'admin@demo.local');
  await p.click('a:has-text("Auditoría")');
  await p.waitForSelector('h1:has-text("Auditoría")');
  await p.waitForSelector('tbody tr');
  const filas = await p.$$eval('tbody tr', (trs) => trs.length);
  const marca = await p.$('text=conviene revisarla');
  anotar('A4', filas === 4 && Boolean(marca), `filas en pantalla: ${filas}; devolución señalada: ${Boolean(marca)}`);
  await p.waitForTimeout(500); await p.screenshot({ path: './a04-pantalla-auditoria.png', fullPage: true });

  // A5 · A 360 px la pantalla no se desplaza de lado (la tabla se desplaza en su caja).
  await p.setViewportSize({ width: 360, height: 780 }); await p.waitForTimeout(400);
  const ancho = await p.evaluate(() => document.documentElement.scrollWidth);
  anotar('A5', ancho <= 360, `ancho del documento: ${ancho} px`);
  await p.screenshot({ path: './a05-auditoria-360px.png', fullPage: true });
  await p.setViewportSize({ width: 1366, height: 860 });

  // A6 · La recepcionista no ve la opción y, si escribe la ruta, ve la pantalla de permiso denegado.
  const p2 = await ctx.newPage();
  await entrar(p2, 'laura@demo.local');
  const enMenu = await p2.$('a:has-text("Auditoría")');
  await p2.goto(URL + '/#auditoria'); await p2.waitForSelector('h1');
  anotar('A6', !enMenu && !(await p2.$('h1:has-text("Auditoría")')), `opción en el menú: ${Boolean(enMenu)}; título al entrar por la ruta: «${(await p2.textContent('h1')).trim()}»`);

  // A7 · D-07: un doble clic en «Anular pago» envía un solo PATCH.
  const p3 = await api('/pagos', { metodo: 'POST', token: laura, clave: crypto.randomUUID(), cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, planId: mensual.id, medio: 'EFECTIVO' } });
  const parches = []; p.on('request', (r) => { if (r.method() === 'PATCH') parches.push(r.url()); });
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('h2:has-text("Historial de pagos")');
  await p.click('button:has-text("Anular último pago")'); await p.fill('#motivo', 'Doble clic del escenario');
  await p.dblclick('button:has-text("Anular pago")'); await p.waitForTimeout(1500);
  anotar('A7', p3.estado === 201 && parches.length === 1, `PATCH enviados: ${parches.length}`);

  anotar('A8', errores.length === 0, errores.length ? errores.join(' | ') : 'sin errores de JavaScript');
  console.log(`\nResumen: ${res.filter(Boolean).length} de ${res.length} comprobaciones pasan.`);
  await b.close();
})();
