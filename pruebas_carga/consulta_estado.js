// Prueba de carga de GET /api/v1/estados/{tipoDocumento}/{numeroDocumento} (RF-04, QA-01, RNF-01).
//
// Es el endpoint que más se usa en hora pico: la recepcionista lo llama por cada socio que llega.
// QA-01 pide que el 95 % responda en menos de 2 s, sin errores, con 10 usuarios simultáneos y una
// base de 2.000 socios y 20.000 pagos (pruebas_carga/sembrar.py).
//
//   k6 run pruebas_carga/consulta_estado.js                      # perfil qa01: 10 VUs, 10 minutos
//   k6 run -e PERFIL=exploracion pruebas_carga/consulta_estado.js # hasta 50 VUs, para ver el margen
//
// Regla de oro de la Guía 8: nunca contra producción. Solo se aceptan los hosts de HOSTS_PERMITIDOS;
// cualquier otra BASE_URL aborta la prueba antes de la primera petición.

import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const HOSTS_PERMITIDOS = ['127.0.0.1', 'localhost'];
const SOCIOS = 2000; // los que siembra pruebas_carga/sembrar.py
const PERFIL = __ENV.PERFIL || 'qa01';

const PERFILES = {
  // QA-01 tal cual: 10 usuarios simultáneos durante 10 minutos. El gimnasio tiene 1 o 2
  // recepcionistas; 10 usuarios que consultan cada segundo ya son unas 20 veces la hora pico real.
  qa01: [
    { duration: '1m', target: 10 }, // rampa de subida
    { duration: '8m', target: 10 }, // sostenimiento
    { duration: '1m', target: 0 }, // bajada
  ],
  // Para encontrar el margen: hasta 50 usuarios, el tope que fija la guía. No es un volumen real.
  exploracion: [
    { duration: '2m', target: 50 },
    { duration: '3m', target: 50 },
    { duration: '1m', target: 0 },
  ],
};

export const options = {
  stages: PERFILES[PERFIL],
  thresholds: {
    // RNF-01 / QA-01: el 95 % en menos de 2 s y ninguna consulta con error.
    http_req_duration: ['p(95)<2000'],
    http_req_failed: ['rate==0'],
    // Alarma de ingeniería, más estricta que el negocio: si se pasa, algo empeoró aunque
    // QA-01 todavía se cumpla. La recepcionista nota una espera de más de 0,3 s.
    'http_req_duration{endpoint:consultarEstado}': ['p(95)<300'],
    checks: ['rate==1'],
  },
};

function hostDe(url) {
  const coincide = /^https?:\/\/([^/:]+)/.exec(url);
  return coincide ? coincide[1] : '';
}

export function setup() {
  if (!HOSTS_PERMITIDOS.includes(hostDe(BASE_URL))) {
    exec.test.abort(`BASE_URL=${BASE_URL} no es un entorno de carga permitido. Nunca producción.`);
  }
  const r = http.post(
    `${BASE_URL}/api/v1/auth/token`,
    JSON.stringify({ correo: 'laura@carga.local', contrasena: __ENV.CLAVE_CARGA || 'carga-local-2026' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { endpoint: 'emitirToken' } },
  );
  if (r.status !== 200) {
    exec.test.abort(`No se pudo iniciar sesión en el entorno de carga (HTTP ${r.status}).`);
  }
  return { token: r.json('tokenAcceso') };
}

export default function (datos) {
  const numero = 1090000000 + Math.floor(Math.random() * SOCIOS);
  const r = http.get(`${BASE_URL}/api/v1/estados/CC/${numero}`, {
    headers: { Authorization: `Bearer ${datos.token}` },
    tags: { endpoint: 'consultarEstado', name: 'GET /estados/{tipo}/{numero}' },
  });
  check(r, {
    'responde 200': (res) => res.status === 200,
    'trae el estado': (res) => ['ACTIVO', 'VENCIDO', 'SIN_MEMBRESIA'].includes(res.json('estado')),
  });
  sleep(1); // una consulta por segundo por usuario
}
