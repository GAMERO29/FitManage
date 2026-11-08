// Recorrido completo del aplicativo (ADR N.° 17) con Chromium contra gunicorn local.
// Base creada con `migrate` + `preparar_gimnasio`, más una cuenta de recepcionista de prueba.
// Uso: node e2e.js [url]   (por defecto http://127.0.0.1:8765)
const { chromium } = require('playwright');
const URL = process.argv[2] || 'http://127.0.0.1:8765';
const DOC = '1090000011';
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1366, height: 860 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  const errores = [];
  p.on('console', (m) => { if (m.type() === 'error') errores.push(m.text()); });
  p.on('pageerror', (e) => errores.push(String(e)));
  const foto = async (n) => { await p.waitForTimeout(1100); await p.screenshot({ path: `./${n}.png`, fullPage: true }); };
  const texto = (sel) => p.textContent(sel);

  await p.goto(URL + '/');
  await p.fill('#correo', 'admin@demo.local');
  await p.fill('#clave', 'clave-equivocada');
  await p.click('button:has-text("Entrar")');
  await p.waitForSelector('.msg-error:not(:empty)');
  console.log('1 login malo:', (await texto('.msg-error')).trim());
  await foto('01-ingreso');
  await p.fill('#clave', 'clave-de-demo-local');
  await p.click('button:has-text("Entrar")');
  await p.waitForSelector('h1:has-text("Recepción")');
  await foto('02-recepcion');

  await p.fill('#doc', DOC);
  await p.press('#doc', 'Enter');
  await p.waitForSelector('.estado:has-text("No registrado")');
  console.log('2 consulta:', (await texto('.estado-sub')).trim());
  await foto('03-no-registrado');

  await p.click('.acciones a:has-text("Registrar socio")');
  await p.waitForSelector('h1:has-text("Registrar socio")');
  await p.fill('#nom', 'Ana');
  await p.fill('#ape', 'Prueba Demo');
  await p.fill('#tel', '3001234567');
  await p.check('#autoriza');
  await foto('04-registro-socio');
  await p.click('button:has-text("Guardar socio")');
  await p.waitForSelector('.aviso.a-ok');
  console.log('3 socio:', (await texto('.aviso.a-ok')).trim());

  await p.click('a:has-text("Registrar su primer pago")');
  await p.waitForSelector('.linea-fechas');
  await p.click('.chip:has-text("Nequi")');
  await p.fill('#ref', 'M123456');
  await foto('05-pago');
  await p.dblclick('.btn-confirmar');
  await p.waitForSelector('.aviso.a-ok');
  console.log('4 pago:', (await texto('.aviso.a-ok')).trim());
  await foto('06-pago-registrado');

  await p.click('a[href="#recepcion"] >> nth=0');
  await p.fill('#doc', DOC);
  await p.press('#doc', 'Enter');
  await p.waitForSelector('.estado:has-text("ACTIVO")');
  console.log('5 estado:', (await texto('.resultado .estado-sub')).trim(), '·', (await texto('.anillo .centro')).replace(/\s+/g, ' ').trim());
  await foto('07-activo');

  await p.click('a:has-text("Renovar antes de que venza")');
  await p.waitForSelector('.linea-fechas');
  await p.click('.opcion:has-text("Trimestral")');
  await p.waitForFunction(() => document.querySelector('.leyenda') && document.querySelector('.leyenda').textContent.includes('Trimestral'));
  console.log('6 renovación (vista previa):', (await texto('.linea-fechas')).replace(/\s+/g, ' ').trim());
  await foto('08-renovacion-vista-previa');

  await p.click('a:has-text("Socios e historial")');
  await p.fill('#doc-b', DOC);
  await p.press('#doc-b', 'Enter');
  await p.waitForSelector('h2:has-text("Historial de pagos")');
  await foto('09-historial');
  await p.click('button:has-text("Anular último pago")');
  await p.fill('#motivo', 'Prueba de anulación del recorrido');
  await p.click('button:has-text("Anular pago")');
  await p.waitForSelector('.aviso.a-aviso');
  console.log('7 anulación:', (await texto('tbody tr td:last-child')).replace(/\s+/g, ' ').trim());
  await foto('10-anulado');

  await p.click('a:has-text("Reportes")');
  await p.waitForSelector('.total');
  console.log('8 reporte:', (await texto('.resumen')).replace(/\s+/g, ' ').trim());
  await foto('11-reportes');

  await p.click('a:has-text("Planes")');
  await p.fill('input[aria-label="Precio del plan Diario"]', '9.000');
  await p.click('button:has-text("Guardar precios")');
  await p.waitForSelector('.aviso.a-ok');
  console.log('9 planes:', (await texto('.aviso.a-ok')).trim());
  await p.click('button:has-text("Crear plan")');
  await p.fill('#p-nombre', 'Semestral');
  await p.fill('#p-dias', '180');
  await p.fill('#p-precio', '380.000');
  await p.click('form button[type=submit]:has-text("Crear plan")');
  await p.waitForSelector('.aviso.a-ok:has-text("Semestral")');
  console.log('9b plan nuevo:', (await texto('.aviso.a-ok')).trim());
  await p.click('tr:has-text("Diario") button:has-text("Desactivar")');
  await p.waitForSelector('tr.anulada:has-text("Diario")');
  console.log('9c desactivado:', (await texto('.aviso.a-ok')).trim());
  await foto('12-planes');
  await p.click('a:has-text("Registrar pago")');
  await p.waitForSelector('.opcion, #doc-b');
  if (await p.$('#doc-b')) { await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter'); }
  await p.waitForSelector('.opcion');
  const ofrecidos = await p.$$eval('.opcion b', (bs) => bs.map((b) => b.textContent));
  console.log('9d planes en Registrar pago:', ofrecidos.join(', '));

  await p.click('a:has-text("Personal")');
  await p.click('button:has-text("Crear cuenta")');
  await p.fill('#c-nombre', 'Sofía Prueba');
  await p.fill('#c-correo', 'sofia@demo.local');
  await p.fill('#c-clave', 'clave-inicial-2026');
  await p.click('form button[type=submit]:has-text("Crear cuenta")');
  await p.waitForSelector('.aviso.a-ok');
  console.log('10 personal:', (await texto('.aviso.a-ok')).trim());
  await foto('13-personal');

  await p.click('a:has-text("Vencimientos")');
  await p.waitForSelector('h1:has-text("Próximos vencimientos")');
  await foto('14-vencimientos');

  const cel = await ctx.newPage();
  await cel.setViewportSize({ width: 412, height: 915 });
  await cel.goto(URL + '/');
  await cel.fill('#correo', 'laura@demo.local');
  await cel.fill('#clave', 'clave-de-demo-local');
  await cel.click('button:has-text("Entrar")');
  await cel.waitForSelector('h1:has-text("Recepción")');
  await cel.fill('#doc', DOC);
  await cel.press('#doc', 'Enter');
  await cel.waitForSelector('.resultado .estado');
  await cel.waitForTimeout(1100);
  await cel.screenshot({ path: './15-celular-recepcionista.png', fullPage: true });
  await cel.goto(URL + '/#reportes');
  await cel.waitForSelector('h1');
  console.log('11 recepcionista en #reportes:', (await cel.textContent('h1')).trim());
  await cel.waitForTimeout(400);
  await cel.screenshot({ path: './16-recepcionista-sin-permiso.png', fullPage: true });

  console.log('errores de consola:', errores.length ? errores : 'ninguno');
  await b.close();
})();
