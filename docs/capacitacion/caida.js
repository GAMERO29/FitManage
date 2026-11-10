// Guía II-06 · H-01 y H-03: qué ve la recepcionista si la base de datos se cae.
// Requiere el servidor local (docs/guia-ii05) y PostgreSQL local controlado con pg_ctl. Uso: node caida.js <archivo.png>
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const URL = 'http://127.0.0.1:8765', CLAVE = 'clave-de-demo-local', DOC = '1090000011';
const PG = (accion) => execSync(`su pgrun -s /bin/bash -c "/usr/lib/postgresql/16/bin/pg_ctl -D /tmp/pgdata -l /tmp/pg.log -m fast -o '-p 5433 -k /tmp' ${accion}" >/dev/null`);
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
  await p.goto(URL + '/'); await p.fill('#correo', 'laura@demo.local'); await p.fill('#clave', CLAVE);
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
  PG('stop');
  try {
    await p.fill('#doc', DOC); await p.press('#doc', 'Enter'); await p.waitForTimeout(2500);
    const mensaje = await p.$$eval('.resultado, [role=alert]', (es) => es.map((e) => e.textContent.trim()).filter(Boolean));
    const indicador = await p.textContent('.conexion');
    console.log('Mensaje:', JSON.stringify(mensaje)); console.log('Indicador:', indicador.trim());
    await p.screenshot({ path: process.argv[2] || 'img/base-caida.png' });
  } finally { PG('start'); }
  await p.waitForTimeout(1500); await p.fill('#doc', DOC); await p.press('#doc', 'Enter');
  await p.waitForSelector('.estado'); console.log('Después de arrancar la base, indicador:', (await p.textContent('.conexion')).trim());
  await b.close();
})();
