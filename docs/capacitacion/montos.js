// Guía II-06 · H-02: ¿algún monto de la tabla de historial se parte en dos líneas? Ancho en px como segundo argumento (1024 por defecto).
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: Number(process.argv[3] || 1024), height: 768 } })).newPage();
  await p.goto(URL + '/'); await p.fill('#correo', 'laura@demo.local'); await p.fill('#clave', 'clave-de-demo-local');
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', '1090000011'); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('td.der');
  const lineas = await p.$$eval('td.der', (tds) => tds.map((td) => { const r = document.createRange(); r.selectNodeContents(td); return [td.textContent.trim(), new Set([...r.getClientRects()].map((x) => Math.round(x.top))).size]; }));
  const partidos = lineas.filter(([, n]) => n > 1);
  console.log(`Ancho ${process.argv[3] || 1024} px · montos en la tabla: ${lineas.length} · partidos en dos líneas: ${partidos.length}`, partidos.length ? JSON.stringify(partidos) : '');
  await b.close();
})();
