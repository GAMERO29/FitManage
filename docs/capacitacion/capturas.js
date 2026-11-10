// Guía II-06 · Capturas de la guía rápida, tomadas de la versión en uso (datos ficticios).
// Requiere el servidor local con los datos de docs/guia-ii03/escenario.js. Uso: node capturas.js
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765', CLAVE = 'clave-de-demo-local', DOC = '1090000011';
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
  const foto = async (n) => { await p.waitForTimeout(800); await p.screenshot({ path: `./img/${n}.png` }); };
  const t = (await (await fetch(URL + '/api/v1/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ correo: 'laura@demo.local', contrasena: CLAVE }) })).json()).tokenAcceso;
  const planes = await (await fetch(URL + '/api/v1/planes', { headers: { Authorization: `Bearer ${t}` } })).json();
  await fetch(URL + '/api/v1/pagos', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}`, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ tipoDocumento: 'CC', numeroDocumento: DOC, planId: planes.find((x) => x.nombre === 'Mensual').id, medio: 'EFECTIVO' }) });
  await p.goto(URL + '/'); await foto('01-ingreso');
  await p.fill('#correo', 'laura@demo.local'); await p.fill('#clave', CLAVE); await p.click('button:has-text("Entrar")');
  await p.waitForSelector('h1:has-text("Recepción")');
  await p.fill('#doc', DOC); await p.press('#doc', 'Enter'); await p.waitForSelector('.estado:has-text("ACTIVO")'); await foto('02-consulta-activo');
  await p.fill('#doc', '1090000099'); await p.press('#doc', 'Enter'); await p.waitForSelector('.estado:has-text("No registrado")'); await foto('03-no-registrado');
  await p.click('a:has-text("Registrar pago")'); await p.waitForSelector('#doc-b, .opcion');
  if (await p.$('#doc-b')) { await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter'); }
  await p.waitForSelector('.linea-fechas'); await p.click('.chip:has-text("Nequi")'); await foto('04-registrar-pago');
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('h2:has-text("Historial de pagos")'); await foto('05-historial');
  await p.click('button:has-text("Anular último pago")'); await p.waitForSelector('#motivo'); await foto('06-anular');
  await b.close();
})();
