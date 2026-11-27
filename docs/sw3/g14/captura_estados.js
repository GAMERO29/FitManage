// Software III · Guía 14: los estados de la anulación en la pantalla (laboratorio, datos ficticios).
// 1) motivo corto, 2) base caída al confirmar (mensaje recuperable), 3) éxito al volver la base.
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const URL = 'http://127.0.0.1:8765', CLAVE = 'clave-de-demo-local', DOC = process.argv[2] || '1090000077';
const PG = "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -o '-p 5433 -k /tmp' -m fast";
const pg = (accion) => execSync(`su pgrun -s /bin/bash -c "${PG} ${accion}"`, { stdio: 'ignore' });
const api = async (ruta, token, cuerpo, metodo = 'POST') => (await fetch(URL + '/api/v1' + ruta, { method: metodo, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), 'Idempotency-Key': crypto.randomUUID() }, body: cuerpo ? JSON.stringify(cuerpo) : undefined })).json();
(async () => {
  const t = (await api('/auth/token', null, { correo: 'admin@demo.local', contrasena: CLAVE })).tokenAcceso;
  await api('/socios', t, { tipoDocumento: 'CC', numeroDocumento: DOC, nombres: 'Rosa', apellidos: 'Prueba Demo', telefono: '3001234567', autorizaTratamientoDatos: true });
  const plan = (await api('/planes', t, null, 'GET')).find((p) => p.nombre === 'Mensual').id;
  await api('/pagos', t, { tipoDocumento: 'CC', numeroDocumento: DOC, planId: plan, medio: 'EFECTIVO' });
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  await p.goto(URL + '/'); await p.fill('#correo', 'admin@demo.local'); await p.fill('#clave', CLAVE);
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.click('button:has-text("Anular último pago")');
  await p.fill('#motivo', 'x'); await p.click('button:has-text("Anular pago")'); await p.waitForTimeout(300);
  console.log('1. motivo «x»: ' + (await p.locator('.msg-error').first().textContent()).trim());
  await p.screenshot({ path: 'estado_1_motivo_corto.png' });
  await p.fill('#motivo', 'Se registró el plan equivocado');
  pg('stop');
  try {
    await p.click('button:has-text("Anular pago")'); await p.waitForSelector('.aviso.a-mal'); await p.waitForTimeout(300);
    console.log('2. base detenida: ' + (await p.locator('.aviso.a-mal').textContent()).trim());
    await p.screenshot({ path: 'estado_2_base_caida.png', fullPage: true });
  } finally { pg('start'); }
  await new Promise((r) => setTimeout(r, 2500));
  await p.click('button:has-text("Anular pago")'); await p.waitForSelector('.aviso.a-aviso'); await p.waitForTimeout(400);
  console.log('3. base de vuelta, mismo clic: ' + (await p.locator('.aviso.a-aviso').textContent()).trim());
  await p.screenshot({ path: 'estado_3_anulado.png', fullPage: true });
  await b.close();
})();
