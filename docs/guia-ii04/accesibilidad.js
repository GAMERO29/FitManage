// Guía II-04 · Revisión automática de accesibilidad con axe-core 4.10.2 sobre las pantallas del
// flujo crítico y de la auditoría (WCAG 2.1 A y AA). Complementa la revisión manual con teclado.
// Uso: node accesibilidad.js [url] [ruta-de-axe.min.js]
const { chromium } = require('playwright');
const fs = require('fs');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
const AXE = fs.readFileSync(process.argv[3] || './node_modules/axe-core/axe.min.js', 'utf8');
const CLAVE = 'clave-de-demo-local';
const DOC = '1090000011';

(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1366, height: 860 } })).newPage();
  const revisar = async (nombre) => {
    await p.evaluate(AXE); // la CSP de la app bloquea scripts en línea; evaluate entra por el protocolo del navegador
    const r = await p.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] })));
    const v = r.violations.map((x) => `${x.id} (${x.impact}, ${x.nodes.length} nodos)`);
    console.log(`${nombre}: ${r.passes.length} reglas pasan · ${v.length ? 'violaciones: ' + v.join('; ') : 'sin violaciones'}`);
  };
  await p.goto(URL + '/');
  await revisar('Inicio de sesión');
  await p.fill('#correo', 'admin@demo.local'); await p.fill('#clave', CLAVE); await p.click('button:has-text("Entrar")');
  await p.waitForSelector('h1:has-text("Recepción")');
  await p.fill('#doc', DOC); await p.press('#doc', 'Enter'); await p.waitForSelector('.resultado .estado');
  await revisar('Recepción con resultado');
  // Un pago vigente para poder abrir la confirmación de anulación (datos ficticios).
  const t = (await (await fetch(URL + '/api/v1/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ correo: 'admin@demo.local', contrasena: CLAVE }) })).json()).tokenAcceso;
  const planes = await (await fetch(URL + '/api/v1/planes', { headers: { Authorization: `Bearer ${t}` } })).json();
  await fetch(URL + '/api/v1/pagos', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}`, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ tipoDocumento: 'CC', numeroDocumento: DOC, planId: planes[0].id, medio: 'EFECTIVO' }) });
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('h2:has-text("Historial de pagos")');
  await p.click('button:has-text("Anular último pago")'); await p.waitForSelector('#motivo');
  await revisar('Historial con la confirmación de anulación abierta');
  await p.click('a:has-text("Auditoría")'); await p.waitForSelector('tbody tr');
  await revisar('Auditoría');
  await b.close();
})();
