// Guía II-06 · Regresión de H-01 y H-03: qué mensaje y qué indicador ve la recepcionista según la respuesta.
// Simula la respuesta de /estados en el navegador (page.route); no toca la base. Uso: node mensajes.js
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
const casos = [
  ['500 sin cuerpo (base caída)', 500, null, /hoja de papel/, /no responde/],
  ['503 SERVICIO_NO_DISPONIBLE', 503, { title: 'Servicio no disponible', status: 503, codigo: 'SERVICIO_NO_DISPONIBLE' }, /hoja de papel/, /no responde/],
  ['503 CORREO_NO_DISPONIBLE', 503, { title: 'No se pudo enviar el correo', status: 503, codigo: 'CORREO_NO_DISPONIBLE' }, /No se pudo enviar el correo/, /En línea/],
  ['404 NO_ENCONTRADO', 404, { title: 'No hay ningún socio con ese documento', status: 404, codigo: 'NO_ENCONTRADO' }, /No registrado|No hay ningún socio/, /En línea/],
];
(async () => {
  const b = await chromium.launch(); let fallas = 0;
  const p = await (await b.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
  await p.goto(URL + '/'); await p.fill('#correo', 'laura@demo.local'); await p.fill('#clave', 'clave-de-demo-local');
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
  for (const [nombre, estado, cuerpo, esperaMensaje, esperaIndicador] of casos) {
    await p.unroute('**/api/v1/estados/**');
    await p.route('**/api/v1/estados/**', (r) => r.fulfill({ status: estado, contentType: 'application/problem+json', body: cuerpo ? JSON.stringify(cuerpo) : '' }));
    await p.fill('#doc', '1090000011'); await p.press('#doc', 'Enter'); await p.waitForTimeout(700);
    const mensaje = (await p.textContent('.resultado, [role=alert]')) || '';
    const indicador = (await p.textContent('.conexion')).trim();
    const ok = esperaMensaje.test(mensaje) && esperaIndicador.test(indicador);
    if (!ok) fallas++;
    console.log(`${ok ? 'PASA' : 'FALLA'} · ${nombre} · indicador: «${indicador}» · mensaje: «${mensaje.trim().slice(0, 90)}»`);
  }
  console.log(`Resumen: ${casos.length - fallas} de ${casos.length} casos pasan.`);
  await b.close(); process.exit(fallas ? 1 : 0);
})();
