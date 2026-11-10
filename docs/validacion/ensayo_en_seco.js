// Guía II-06 · Ensayo en seco del protocolo: el autor ejecuta cada tarea en la versión local con datos
// ficticios y comprueba que el criterio de éxito se puede observar. NO es una sesión con participantes.
// Requiere el servidor local con una base nueva (docs/guia-ii05). Uso: node ensayo_en_seco.js [url] [--solo-preparar]
const { chromium } = require('playwright');
const URL = process.argv.slice(2).find((a) => a.startsWith('http')) || 'http://127.0.0.1:8765';
const SOLO_PREPARAR = process.argv.includes('--solo-preparar');
const CLAVE = 'clave-de-demo-local', DOC = '1090000011';
const res = [];
const anotar = (id, ok, detalle) => { res.push(ok); console.log(`${id} ${ok ? 'PASA' : 'FALLA'} · ${detalle}`); };
async function api(ruta, { metodo = 'GET', token, cuerpo } = {}) {
  const c = { 'Content-Type': 'application/json', 'Idempotency-Key': crypto.randomUUID() };
  if (token) c.Authorization = `Bearer ${token}`;
  const r = await fetch(URL + '/api/v1' + ruta, { method: metodo, headers: c, body: cuerpo ? JSON.stringify(cuerpo) : undefined });
  let json = null; try { json = await r.json(); } catch { /* sin cuerpo */ }
  return { estado: r.status, json };
}
const token = async (correo) => (await api('/auth/token', { metodo: 'POST', cuerpo: { correo, contrasena: CLAVE } })).json.tokenAcceso;
const entrar = async (p, correo) => {
  await p.goto(URL + '/'); await p.fill('#correo', correo); await p.fill('#clave', CLAVE);
  await p.click('button:has-text("Entrar")'); await p.waitForSelector('h1:has-text("Recepción")');
};
const historial = async (t) => (await api(`/socios/CC/${DOC}/pagos`, { token: t })).json.pagos;

(async () => {
  // Preparación (el facilitador, antes de cada participante): base nueva, cuenta de práctica y socia ficticia con un mes pagado.
  const admin = await token('admin@demo.local');
  await api('/personal', { metodo: 'POST', token: admin, cuerpo: { nombre: 'Laura Demo', correo: 'laura@demo.local', rol: 'RECEPCIONISTA', contrasena: CLAVE } });
  const laura = await token('laura@demo.local');
  const planes = (await api('/planes', { token: admin })).json;
  const id = (n) => planes.find((p) => p.nombre === n).id;
  await api('/socios', { metodo: 'POST', token: laura, cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, nombres: 'Ana', apellidos: 'Prueba Demo', telefono: '3001234567', autorizaTratamientoDatos: true } });
  await api('/pagos', { metodo: 'POST', token: laura, cuerpo: { tipoDocumento: 'CC', numeroDocumento: DOC, planId: id('Mensual'), medio: 'EFECTIVO' } });
  if (SOLO_PREPARAR) { console.log('Datos listos para el siguiente participante.'); return; }

  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
  await entrar(p, 'laura@demo.local');

  // T1 · ¿Puede pasar y hasta qué día?
  await p.fill('#doc', DOC); await p.press('#doc', 'Enter'); await p.waitForSelector('.estado'); await p.waitForTimeout(1500);
  const t1 = (await p.textContent('.resultado')).replace(/\s+/g, ' ');
  anotar('T1', /ACTIVO/.test(t1) && /Vence\s*\S+ \d{1,2} de \S+/.test(t1), `la pantalla dice: «${t1.trim().slice(0, 80)}»`);

  // T2 · Pago de otro mes por Nequi con su comprobante.
  await p.click('a:has-text("Registrar pago")'); await p.waitForTimeout(800);
  if (await p.$('#doc-b')) { await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter'); }
  await p.waitForSelector('.linea-fechas');
  await p.click('.opcion:has-text("Mensual")'); await p.click('.chip:has-text("Nequi")'); await p.fill('#ref', 'M123456');
  await p.click('button.btn-confirmar'); await p.waitForSelector('button:has-text("Pago registrado")');
  const h2 = await historial(laura);
  const ultimo = h2.find((x) => x.referencia === 'M123456');
  anotar('T2', ultimo && ultimo.estado === 'VIGENTE' && ultimo.medio === 'NEQUI', `pago Nequi M123456 ${ultimo ? ultimo.estado : 'no encontrado'}; vence ${ultimo && ultimo.vence}`);

  // T3 · Era quincena, no mes. Ruta 1 de 2: cambiar el plan desde el historial (la otra es anular y registrar de nuevo).
  await p.click('a:has-text("Socios e historial")'); await p.fill('#doc-b', DOC); await p.press('#doc-b', 'Enter');
  await p.waitForSelector('h2:has-text("Historial de pagos")');
  await p.click('button:has-text("Cambiar plan")'); await p.waitForSelector('#t-cp');
  await p.click('.opcion:has-text("Quincenal")'); await p.click('.chip:has-text("Efectivo")');
  if (await p.$('#motivo-c')) await p.fill('#motivo-c', 'La socia pidió quince días y no un mes');
  await p.click('button:has-text("Cambiar a Quincenal")'); await p.waitForTimeout(1200);
  const h3 = await historial(laura);
  const vigente = h3.filter((x) => x.estado === 'VIGENTE').map((x) => x.plan);
  const anulado = h3.find((x) => x.referencia === 'M123456');
  anotar('T3', vigente.includes('Quincenal') && anulado.estado === 'ANULADO' && !!(anulado.anulacion && anulado.anulacion.motivo),
    `vigentes: ${vigente.join(', ')} · M123456 ${anulado.estado} («${anulado.anulacion && anulado.anulacion.motivo}»)`);

  // A1 · ¿Quién deshizo un cobro, a qué hora y por qué? (administrador)
  await p.click('button[aria-label="Cerrar sesión"]'); await entrar(p, 'admin@demo.local');
  await p.click('a:has-text("Auditoría")'); await p.waitForSelector('h1:has-text("Auditoría")'); await p.waitForTimeout(1200);
  const a1 = (await p.textContent('main')).replace(/\s+/g, ' ');
  anotar('A1', /Laura Demo/.test(a1) && /quince días/.test(a1) && /\d{1,2}:\d{2}/.test(a1), 'la pantalla de auditoría muestra a Laura Demo, la hora y el motivo');

  // A2 · El mes pasa a 80.000; lo ya pagado no cambia (RN-08).
  await p.click('a:has-text("Planes")'); await p.waitForSelector('input[aria-label="Precio del plan Mensual"]');
  await p.fill('input[aria-label="Precio del plan Mensual"]', '80.000'); await p.click('button:has-text("Guardar precios")'); await p.waitForTimeout(1200);
  const nuevo = (await api('/planes', { token: admin })).json.find((x) => x.nombre === 'Mensual');
  const pagados = (await historial(admin)).filter((x) => x.plan === 'Mensual').map((x) => Number(x.valor));
  anotar('A2', Number(nuevo.precio) === 80000 && pagados.every((v) => v === 75000), `precio nuevo ${nuevo.precio}; pagos Mensual ya hechos: ${pagados.join(', ')}`);

  console.log(`Resumen: ${res.filter(Boolean).length} de ${res.length} tareas se pueden completar y observar en esta versión.`);
  await b.close(); process.exit(res.every(Boolean) ? 0 : 1);
})();
