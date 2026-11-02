// Experimento de la auditoría (Ejercicio 5): el patrón del script de la IA, desactivado.
// Igual que la IA: inicia sesión en cada iteración y no espera entre peticiones.
// Distinto: 10 VUs y no 5000, 30 s, solo contra el entorno de carga local y con el contrato real.
import http from 'k6/http';
import { check } from 'k6';
import exec from 'k6/execution';

const BASE_URL = 'http://127.0.0.1:8000';

export const options = {
  vus: 10,
  duration: '30s',
  // Solo para que k6 muestre el tiempo de cada endpoint por separado; no son criterios de aceptación.
  thresholds: {
    'http_req_duration{endpoint:emitirToken}': ['p(95)<60000'],
    'http_req_duration{endpoint:consultarEstado}': ['p(95)<60000'],
  },
};

export function setup() {
  if (!/^http:\/\/(127\.0\.0\.1|localhost)[:/]/.test(BASE_URL)) exec.test.abort('Solo entorno local');
}

export default function () {
  const login = http.post(
    `${BASE_URL}/api/v1/auth/token`,
    JSON.stringify({ correo: 'laura@carga.local', contrasena: 'carga-local-2026' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { endpoint: 'emitirToken' } },
  );
  const numero = 1090000000 + Math.floor(Math.random() * 2000);
  const r = http.get(`${BASE_URL}/api/v1/estados/CC/${numero}`, {
    headers: { Authorization: `Bearer ${login.json('tokenAcceso')}` },
    tags: { endpoint: 'consultarEstado' },
  });
  check(r, { 'responde 200': (res) => res.status === 200 });
}
