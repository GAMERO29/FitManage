// Guía II-04 · Carga de GET /api/v1/auditoria (ADR N.° 19) sobre 30.000 eventos en 31 días.
//
// Escenario: el administrador revisa el mes (31 días, la consulta más pesada que permite el
// contrato) y pasa páginas. 5 usuarios a la vez durante 2 minutos: el gimnasio tiene un solo
// administrador, así que 5 es un margen de 5 veces, no un volumen real.
// Umbral: p95 < 2 s (RNF-01, el mismo de la consulta de recepción) y 0 % de errores.
//
//   k6 run pruebas_carga/consulta_auditoria.js
// Nunca contra producción: solo localhost.

import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const HOSTS_PERMITIDOS = ['127.0.0.1', 'localhost'];

export const options = {
  stages: [
    { duration: '20s', target: 5 },
    { duration: '1m30s', target: 5 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate==0'],
    checks: ['rate==1'],
  },
};

export function setup() {
  const host = (/^https?:\/\/([^/:]+)/.exec(BASE_URL) || [])[1];
  if (!HOSTS_PERMITIDOS.includes(host)) exec.test.abort(`BASE_URL=${BASE_URL} no es un entorno de carga permitido.`);
  const r = http.post(`${BASE_URL}/api/v1/auth/token`, JSON.stringify({ correo: __ENV.CORREO, contrasena: __ENV.CLAVE }), { headers: { 'Content-Type': 'application/json' } });
  return { token: r.json('tokenAcceso') };
}

export default function (datos) {
  const pagina = 1 + Math.floor(Math.random() * 20);
  const r = http.get(`${BASE_URL}/api/v1/auditoria?desde=2026-10-10&hasta=2026-11-10&pagina=${pagina}`, {
    headers: { Authorization: `Bearer ${datos.token}` },
    tags: { endpoint: 'consultarAuditoria' },
  });
  check(r, {
    'responde 200': (x) => x.status === 200,
    'trae 50 eventos': (x) => x.status === 200 && x.json('eventos').length === 50,
  });
  sleep(1);
}
