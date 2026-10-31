// Pruebas de contrato del consumidor (Consumer-Driven Contracts, Guía 7).
// Generan pacts/VistaMovil-FitManageAPI.json, que el proveedor verifica en
// tests/contrato/test_pact_proveedor.py antes de cada push.
import assert from 'node:assert/strict';
import path from 'node:path';
import { describe, it } from 'node:test';
import { MatchersV3, PactV3 } from '@pact-foundation/pact';
import { crearClienteEstados, ErrorDeSesion } from '../src/clienteEstados.js';

const { like, regex, eachLike, datetime } = MatchersV3;

const pact = new PactV3({
  consumer: 'VistaMovil',
  provider: 'FitManageAPI',
  dir: path.resolve('pacts'),
});

const TOKEN = 'eyJhbGciOiJIUzI1NiJ9.token-de-prueba.firma';
const autorizacion = { Authorization: regex('^Bearer .+$', `Bearer ${TOKEN}`) };

const estadoActivo = {
  documentoHash: regex('^[0-9a-f]{16}$', '9b1f0c7e5a2d4e8f'),
  nombreCorto: like('Ana P.'),
  documentoEnmascarado: regex('^[A-Z]+ \\*+\\d{4}$', 'CC ******3456'),
  estado: 'ACTIVO',
  venceEl: regex('^\\d{4}-\\d{2}-\\d{2}$', '2026-10-21'),
  diasRestantes: like(15),
};

// En la copia completa conviven socios activos, vencidos y sin membresía: solo estos campos
// vienen siempre. (La primera versión de este pact exigía venceEl y diasRestantes en todos, y la
// verificación del proveedor lo rechazó con razón.)
const estadoCualquiera = {
  documentoHash: regex('^[0-9a-f]{16}$', '9b1f0c7e5a2d4e8f'),
  nombreCorto: like('Ana P.'),
  documentoEnmascarado: regex('^[A-Z]+ \\*+\\d{4}$', 'CC ******3456'),
  estado: regex('^(ACTIVO|VENCIDO|SIN_MEMBRESIA)$', 'ACTIVO'),
};

const problema = { 'Content-Type': regex('application/problem\\+json.*', 'application/problem+json') };

const cliente = (url) => crearClienteEstados({ baseUrl: url, obtenerToken: () => TOKEN });

describe('VistaMovil → FitManageAPI', () => {
  it('consulta el estado de una socia activa', () => {
    pact
      .given('la socia CC 1090123456 tiene membresía activa')
      .uponReceiving('una consulta de estado de una socia activa')
      .withRequest({ method: 'GET', path: '/api/v1/estados/CC/1090123456', headers: autorizacion })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': regex('application/json.*', 'application/json') },
        body: estadoActivo,
      });
    return pact.executeTest(async (mock) => {
      const estado = await cliente(`${mock.url}/api/v1`).consultar('CC', '1090123456');
      assert.equal(estado.estado, 'ACTIVO');
      assert.equal(estado.dias, 15);
      assert.match(estado.documento, /\*{4,}\d{4}$/);
    });
  });

  it('consulta un documento que no existe', () => {
    pact
      .given('no hay ningún socio con el documento CC 1111111111')
      .uponReceiving('una consulta de un documento inexistente')
      .withRequest({ method: 'GET', path: '/api/v1/estados/CC/1111111111', headers: autorizacion })
      .willRespondWith({
        status: 404,
        headers: problema,
        body: { status: 404, codigo: 'NO_ENCONTRADO', title: like('No hay ningún socio con ese documento') },
      });
    return pact.executeTest(async (mock) => {
      assert.equal(await cliente(`${mock.url}/api/v1`).consultar('CC', '1111111111'), null);
    });
  });

  it('descarga la copia para trabajar sin conexión', () => {
    pact
      .given('la socia CC 1090123456 tiene membresía activa')
      .uponReceiving('la descarga de la copia de estados')
      .withRequest({ method: 'GET', path: '/api/v1/estados', headers: autorizacion })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': regex('application/json.*', 'application/json') },
        body: {
          generadoEl: datetime("yyyy-MM-dd'T'HH:mm:ssXXX", '2026-10-07T18:45:00-05:00'),
          estados: eachLike(estadoCualquiera),
        },
      });
    return pact.executeTest(async (mock) => {
      const copia = await cliente(`${mock.url}/api/v1`).descargarCopia();
      const [unEstado] = Object.values(copia.porClave);
      assert.equal(unEstado.estado, 'ACTIVO');
      assert.equal(unEstado.telefono, undefined); // la copia del celular nunca trae teléfonos
    });
  });

  it('pide renovar cuando el token venció', () => {
    pact
      .given('la socia CC 1090123456 tiene membresía activa')
      .uponReceiving('una consulta con un token vencido')
      .withRequest({
        method: 'GET',
        path: '/api/v1/estados/CC/1090123456',
        headers: { Authorization: 'Bearer token-vencido' },
      })
      .willRespondWith({ status: 401, headers: problema, body: { codigo: 'NO_AUTENTICADO' } });
    return pact.executeTest(async (mock) => {
      const vencido = crearClienteEstados({ baseUrl: `${mock.url}/api/v1`, obtenerToken: () => 'token-vencido' });
      await assert.rejects(vencido.consultar('CC', '1090123456'), ErrorDeSesion);
    });
  });
});
