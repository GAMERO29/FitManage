// Tráfico de recepción para el tablero de Grafana (Guía 13). No es una prueba de rendimiento:
// no tiene umbrales, porque el workflow «Observabilidad» apaga la base a propósito a mitad de la
// corrida para ver si el tablero y las alertas lo notan.
//
//   k6 run pruebas_carga/trafico_observabilidad.js         # 5 usuarios durante 6 minutos
//
// Mezcla parecida a una tarde real: casi todos son socios que existen, algunos documentos mal
// digitados (404) y algún tipo de documento que el contrato no admite (400).

import http from 'k6/http';
import { sleep } from 'k6';
import exec from 'k6/execution';

const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const HOSTS_PERMITIDOS = ['127.0.0.1', 'localhost'];
const SOCIOS = 2000;

export const options = {
  stages: [
    { duration: '30s', target: 5 },
    { duration: __ENV.DURACION || '5m', target: 5 },
    { duration: '30s', target: 0 },
  ],
};

export function setup() {
  const host = (/^https?:\/\/([^/:]+)/.exec(BASE_URL) || [])[1];
  if (!HOSTS_PERMITIDOS.includes(host)) {
    exec.test.abort(`BASE_URL=${BASE_URL} no es un entorno local. Nunca producción.`);
  }
  const r = http.post(
    `${BASE_URL}/api/v1/auth/token`,
    JSON.stringify({ correo: 'laura@carga.local', contrasena: __ENV.CLAVE_CARGA || 'carga-local-2026' }),
    { headers: { 'Content-Type': 'application/json' } },
  );
  if (r.status !== 200) exec.test.abort(`No se pudo iniciar sesión (HTTP ${r.status}).`);
  return { token: r.json('tokenAcceso') };
}

export default function (datos) {
  const azar = Math.random();
  let ruta;
  if (azar < 0.85) ruta = `CC/${1090000000 + Math.floor(Math.random() * SOCIOS)}`;
  else if (azar < 0.97) ruta = `CC/${1190000000 + Math.floor(Math.random() * 1000)}`; // no existe
  else ruta = `TI/${1090000000 + Math.floor(Math.random() * SOCIOS)}`; // fuera del contrato
  http.get(`${BASE_URL}/api/v1/estados/${ruta}`, {
    headers: { Authorization: `Bearer ${datos.token}` },
    tags: { name: 'GET /estados/{tipo}/{numero}' },
  });
  sleep(0.5 + Math.random());
}
