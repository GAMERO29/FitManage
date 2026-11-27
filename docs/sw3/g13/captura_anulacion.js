// Software III · Guía 13: ¿la pantalla habilita «Anular último pago» a quien no puede anular?
// Dos recepcionistas ficticias con el mismo nombre. «Laura Demo A» registra un pago de hoy;
// «Laura Demo B» abre el mismo historial. Uso: node captura_anulacion.js <sufijo-de-archivo>
const { chromium } = require('playwright');
const URL = 'http://127.0.0.1:8765', CLAVE = 'clave-de-demo-local', DOC = '1090000055';
const sufijo = process.argv[2] || 'despues';
const api = async (ruta, token, cuerpo, metodo = 'POST') => {
  const r = await fetch(URL + '/api/v1' + ruta, { method: metodo, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), 'Idempotency-Key': crypto.randomUUID() }, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  return r.status === 204 ? null : r.json();
};
const token = async (correo, clave) => (await api('/auth/token', null, { correo, contrasena: clave })).tokenAcceso;
(async () => {
  const admin = await token('admin@demo.local', CLAVE);
  for (const [correo, clave] of [['laura.a@demo.local', 'clave-laura-a-2026'], ['laura.b@demo.local', 'clave-laura-b-2026']])
    await api('/personal', admin, { nombre: 'Laura Demo', correo, rol: 'RECEPCIONISTA', contrasena: clave });
  await api('/socios', admin, { tipoDocumento: 'CC', numeroDocumento: DOC, nombres: 'Lucía', apellidos: 'Prueba Demo', telefono: '3001234567', autorizaTratamientoDatos: true });
  const a = await token('laura.a@demo.local', 'clave-laura-a-2026');
  const plan = (await api('/planes', a, null, 'GET')).find((p) => p.nombre === 'Mensual').id;
  await api('/pagos', a, { tipoDocumento: 'CC', numeroDocumento: DOC, planId: plan, medio: 'EFECTIVO' });
  const b = await chromium.launch();
  for (const [quien, correo, clave] of [['b', 'laura.b@demo.local', 'clave-laura-b-2026'], ['a', 'laura.a@demo.local', 'clave-laura-a-2026']]) {
    const p = await (await b.newContext({ viewport: { width: 1280, height: 860 } })).newPage();
    await p.goto(URL + '/'); await p.fill('#correo', correo); await p.fill('#clave', clave);
    await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
    await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
    const boton = p.locator('button:has-text("Anular último pago")'); await boton.waitFor();
    console.log(`Laura Demo ${quien.toUpperCase()} (${quien === 'a' ? 'registró el pago' : 'no lo registró'}): botón ${await boton.isDisabled() ? 'deshabilitado' : 'HABILITADO'}`);
    if (quien === 'b' && !(await boton.isDisabled())) {
      await boton.click(); await p.fill('#motivo', 'Prueba de la guía 13'); await p.click('button:has-text("Anular pago")');
      await p.waitForTimeout(800);
      console.log(`  al confirmar, la pantalla muestra: ${(await p.locator('.aviso, [role=alert], .msg-error').first().textContent().catch(() => '(sin mensaje)'))?.trim()}`);
    }
    await p.waitForTimeout(300); await p.screenshot({ path: `anulacion_laura_${quien}_${sufijo}.png` });
  }
  await b.close();
})();
