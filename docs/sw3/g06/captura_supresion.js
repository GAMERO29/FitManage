// Software III · Guía 06: la supresión vista por el administrador (laboratorio, datos ficticios).
const { chromium } = require('playwright');
const URL = 'http://127.0.0.1:8765', CLAVE = 'clave-de-demo-local', DOC = '1090000044';
(async () => {
  const t = (await (await fetch(URL + '/api/v1/auth/token', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ correo: 'admin@demo.local', contrasena: CLAVE }) })).json()).tokenAcceso;
  await fetch(URL + '/api/v1/socios', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${t}`, 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ tipoDocumento: 'CC', numeroDocumento: DOC, nombres: 'Mario', apellidos: 'Prueba Demo', telefono: '3001234567', autorizaTratamientoDatos: true }) });
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
  await p.goto(URL + '/'); await p.fill('#correo', 'admin@demo.local'); await p.fill('#clave', CLAVE);
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('button:has-text("Suprimir datos del socio")'); await p.click('button:has-text("Suprimir datos del socio")');
  await p.waitForSelector('#t-sup'); await p.waitForTimeout(500); await p.screenshot({ path: 'supresion_confirmar.png' });
  await p.click('button:has-text("Suprimir datos")'); await p.waitForSelector('text=Se suprimieron los datos'); await p.waitForTimeout(400);
  await p.screenshot({ path: 'supresion_hecha.png' });
  await b.close();
})();
