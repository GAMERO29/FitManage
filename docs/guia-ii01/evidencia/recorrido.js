// Guía II-01 · Recorrido técnico del flujo «Anular el último pago» sobre el aplicativo real.
// Servidor local con gunicorn (1 proceso, 4 hilos) y PostgreSQL 16, base aislada con datos ficticios.
// Uso: node recorrido.js [url]   (por defecto http://127.0.0.1:8765)
// Imprime una línea por comprobación (R1…R12) y guarda capturas en la carpeta actual.
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
const DOC = '1090000011';
const CLAVE = 'clave-de-demo-local';
const resultados = [];
const anotar = (id, ok, detalle) => { resultados.push({ id, ok, detalle }); console.log(`${id} ${ok ? 'PASA' : 'FALLA'} · ${detalle}`); };

async function api(ruta, { metodo = 'GET', token, cuerpo, clave } = {}) {
  const cabeceras = { 'Content-Type': 'application/json' };
  if (token) cabeceras.Authorization = `Bearer ${token}`;
  if (clave) cabeceras['Idempotency-Key'] = clave;
  const r = await fetch(URL + '/api/v1' + ruta, { method: metodo, headers: cabeceras, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  let json = null; try { json = await r.json(); } catch { /* sin cuerpo */ }
  return { estado: r.status, json };
}
const token = async (correo) => (await api('/auth/token', { metodo: 'POST', cuerpo: { correo, contrasena: CLAVE } })).json.tokenAcceso;

(async () => {
  // Preparación por la API: tres cuentas ficticias creadas por el administrador.
  const admin = await token('admin@demo.local');
  for (const [nombre, correo, rol] of [['Laura Demo', 'laura@demo.local', 'RECEPCIONISTA'], ['Diana Demo', 'diana@demo.local', 'RECEPCIONISTA'], ['Diego Demo', 'diego@demo.local', 'ENTRENADOR']]) {
    await api('/personal', { metodo: 'POST', token: admin, cuerpo: { nombre, correo, rol, contrasena: CLAVE } });
  }
  const planes = (await api('/planes', { token: admin })).json;
  const mensual = planes.find((p) => p.nombre === 'Mensual');

  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 860 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  const errores = [];
  p.on('pageerror', (e) => errores.push(String(e)));
  const foto = async (n) => { await p.waitForTimeout(700); await p.screenshot({ path: `./${n}.png`, fullPage: true }); };
  const entrar = async (pagina, correo) => {
    await pagina.goto(URL + '/');
    await pagina.fill('#correo', correo);
    await pagina.fill('#clave', CLAVE);
    await pagina.click('button:has-text("Entrar")');
    await pagina.waitForSelector('h1:has-text("Recepción")');
  };
  const abrirHistorial = async (pagina) => {
    await pagina.click('a:has-text("Socios e historial")');
    await pagina.fill('#doc-b', DOC);
    await pagina.press('#doc-b', 'Enter');
    await pagina.waitForSelector('h2:has-text("Historial de pagos")');
  };

  // R1 · La recepcionista registra a la socia y su primer pago.
  await entrar(p, 'laura@demo.local');
  await p.fill('#doc', DOC);
  await p.press('#doc', 'Enter');
  await p.waitForSelector('.estado:has-text("No registrado")');
  await p.click('.acciones a:has-text("Registrar socio")');
  await p.fill('#nom', 'Ana');
  await p.fill('#ape', 'Prueba Demo');
  await p.fill('#tel', '3001234567');
  await p.check('#autoriza');
  await p.click('button:has-text("Guardar socio")');
  await p.waitForSelector('.aviso.a-ok');
  await p.click('a:has-text("Registrar su primer pago")');
  await p.waitForSelector('.linea-fechas');
  await p.click('.chip:has-text("Nequi")');
  await p.fill('#ref', 'M123456');
  await p.click('.btn-confirmar');
  await p.waitForSelector('.aviso.a-ok');
  anotar('R1', true, (await p.textContent('.aviso.a-ok')).trim());

  // R2 · En el historial, el botón está habilitado y se alcanza con el teclado.
  await abrirHistorial(p);
  const habilitado = await p.isEnabled('button:has-text("Anular último pago")');
  let pasos = 0; let enfocado = '';
  await p.focus('#doc-b');
  while (pasos < 40 && !enfocado.includes('Anular último pago')) { await p.keyboard.press('Tab'); pasos += 1; enfocado = await p.evaluate(() => document.activeElement.textContent || ''); }
  anotar('R2', habilitado && enfocado.includes('Anular último pago'), `botón habilitado: ${habilitado}; alcanzado con ${pasos} pulsaciones de Tab`);
  await foto('r02-historial-laura');

  // R3 · Al abrir la confirmación el foco va al motivo; sin motivo no se anula.
  await p.keyboard.press('Enter');
  await p.waitForSelector('#motivo');
  const foco = await p.evaluate(() => document.activeElement.id);
  await p.click('button:has-text("Anular pago")');
  await p.waitForSelector('.msg-error[role=alert]');
  const historial1 = (await api(`/socios/CC/${DOC}/pagos`, { token: admin })).json;
  const sigueVigente = historial1.pagos.every((x) => x.estado === 'VIGENTE');
  anotar('R3', foco === 'motivo' && sigueVigente, `foco en #${foco}; mensaje: «${(await p.textContent('.msg-error')).trim()}»; el pago sigue vigente: ${sigueVigente}`);
  await foto('r03-motivo-vacio');

  // R4 · Con motivo, el pago queda anulado (no se borra) y la membresía se recalcula.
  await p.fill('#motivo', 'Plan equivocado: la socia pidió Quincenal');
  await p.click('button:has-text("Anular pago")');
  await p.waitForSelector('.aviso.a-aviso');
  const historial2 = (await api(`/socios/CC/${DOC}/pagos`, { token: admin })).json;
  const estado2 = (await api(`/estados/CC/${DOC}`, { token: admin })).json;
  const fila = historial2.pagos[0];
  anotar('R4', fila.estado === 'ANULADO' && historial2.pagos.length === 1 && estado2.estado === 'SIN_MEMBRESIA',
    `pagos en el historial: ${historial2.pagos.length}; estado del pago: ${fila.estado}; anuló: ${fila.anulacion.anuladoPor}; membresía: ${estado2.estado}`);
  await foto('r04-anulado');

  // R5 · Otra recepcionista ve el botón deshabilitado y el motivo en texto.
  const nuevo = await api('/pagos', { metodo: 'POST', token: await token('laura@demo.local'), clave: crypto.randomUUID(), cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, planId: mensual.id, medio: 'EFECTIVO' } });
  const p2 = await ctx.newPage();
  await entrar(p2, 'diana@demo.local');
  await abrirHistorial(p2);
  const deshabilitado = !(await p2.isEnabled('button:has-text("Anular último pago")'));
  const explicacion = (await p2.textContent('p:has-text("Usted puede anular solo")'))?.trim();
  anotar('R5', nuevo.estado === 201 && deshabilitado && Boolean(explicacion), `pago nuevo de Laura: ${nuevo.estado}; botón deshabilitado para Diana: ${deshabilitado}`);
  await p2.waitForTimeout(700);
  await p2.screenshot({ path: './r05-diana-sin-permiso.png', fullPage: true });

  // R6 · Aunque Diana llame a la API directamente, el servidor rechaza y no cambia nada.
  const diana = await token('diana@demo.local');
  const intento = await api(`/pagos/${nuevo.json.id}`, { metodo: 'PATCH', token: diana, cuerpo: { estado: 'ANULADO', motivo: 'Intento directo' } });
  const tras6 = (await api(`/socios/CC/${DOC}/pagos`, { token: admin })).json.pagos.find((x) => x.id === nuevo.json.id);
  anotar('R6', intento.estado === 403 && tras6.estado === 'VIGENTE', `PATCH directo de Diana: ${intento.estado}; el pago sigue ${tras6.estado}`);

  // R7 · El entrenador no anula ni ve el historial.
  const diego = await token('diego@demo.local');
  const r7a = await api(`/pagos/${nuevo.json.id}`, { metodo: 'PATCH', token: diego, cuerpo: { estado: 'ANULADO', motivo: 'Intento del entrenador' } });
  const r7b = await api(`/socios/CC/${DOC}/pagos`, { token: diego });
  anotar('R7', r7a.estado === 403 && r7b.estado === 403, `PATCH del entrenador: ${r7a.estado}; historial: ${r7b.estado}`);

  // R8 · Dos anulaciones simultáneas del mismo pago: solo una tiene éxito (D-01).
  const dos = await Promise.all(['Doble clic 1', 'Doble clic 2'].map((motivo) => api(`/pagos/${nuevo.json.id}`, { metodo: 'PATCH', token: admin, cuerpo: { estado: 'ANULADO', motivo } })));
  const codigos = dos.map((r) => r.estado).sort();
  anotar('R8', codigos.join() === '200,409', `códigos: ${codigos.join(' y ')}; el 409 dice «${(dos.find((r) => r.estado === 409) || {}).json?.detail}»`);

  // R9 · Repetir la anulación más tarde responde 409 y no cambia quién anuló.
  const antes = (await api(`/socios/CC/${DOC}/pagos`, { token: admin })).json.pagos.find((x) => x.id === nuevo.json.id);
  const repetida = await api(`/pagos/${nuevo.json.id}`, { metodo: 'PATCH', token: admin, cuerpo: { estado: 'ANULADO', motivo: 'Tercer intento' } });
  const despues = (await api(`/socios/CC/${DOC}/pagos`, { token: admin })).json.pagos.find((x) => x.id === nuevo.json.id);
  anotar('R9', repetida.estado === 409 && antes.anulacion.motivo === despues.anulacion.motivo, `repetición: ${repetida.estado}; motivo y autor conservados: «${despues.anulacion.motivo}», ${despues.anulacion.anuladoPor}`);

  // R10 · El estado se dice con texto, no solo con color.
  await abrirHistorial(p);
  const celdas = await p.$$eval('tbody tr td:last-child', (tds) => tds.map((t) => t.textContent.trim()));
  anotar('R10', celdas.every((t) => /Anulado|Vigente/.test(t)), `columna Estado: ${celdas.join(' | ')}`);
  await foto('r10-dos-anulados');

  // R11 · A 360 px de ancho la página no se desplaza de lado.
  await p.setViewportSize({ width: 360, height: 780 });
  await p.waitForTimeout(500);
  const ancho = await p.evaluate(() => document.documentElement.scrollWidth);
  anotar('R11', ancho <= 360, `ancho del documento: ${ancho} px`);
  await p.screenshot({ path: './r11-360px.png', fullPage: true });

  // R13 · Hallazgo de ADR 18: otra recepcionista sí puede cambiar el plan de un pago que no registró,
  // y el cambio anula ese pago. Se registra lo que pasa; la regla queda como pregunta para el dueño.
  const laura = await token('laura@demo.local');
  const tercero = await api('/pagos', { metodo: 'POST', token: laura, clave: crypto.randomUUID(), cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, planId: mensual.id, medio: 'EFECTIVO' } });
  const masBarato = planes.filter((x) => x.activo !== false && x.id !== mensual.id).sort((a, c) => a.precio - c.precio)[0];
  const cambio = await api(`/pagos/${tercero.json.id}/cambio-de-plan`, { metodo: 'POST', token: diana, cuerpo: { planId: masBarato.id, medio: 'EFECTIVO', motivo: 'La socia pidió un plan más corto' } });
  anotar('R13', cambio.estado === 201, `Diana cambia a ${masBarato.nombre} el pago que registró Laura: ${cambio.estado}; diferencia ${cambio.json?.diferencia} (negativa = se le devuelve a la socia); el pago de Laura queda ${cambio.json?.anulado?.estado}`);

  // R12 · Sin errores de JavaScript en todo el recorrido.
  anotar('R12', errores.length === 0, errores.length ? errores.join(' | ') : 'ninguno');

  console.log(`\nResumen: ${resultados.filter((r) => r.ok).length} de ${resultados.length} comprobaciones pasan.`);
  await b.close();
})();
