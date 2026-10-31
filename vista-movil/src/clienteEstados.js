// Cliente HTTP que usará el Service Worker de la vista móvil para llenar su caché (QA-02).
// Solo lee el esquema público: nombre corto, documento enmascarado, estado y fechas.

export class ErrorDeSesion extends Error {}

export function crearClienteEstados({ baseUrl, obtenerToken, fetch = globalThis.fetch }) {
  async function pedir(ruta) {
    const respuesta = await fetch(`${baseUrl}${ruta}`, {
      headers: { Accept: 'application/json', Authorization: `Bearer ${obtenerToken()}` },
    });
    if (respuesta.status === 401) throw new ErrorDeSesion('El token venció; hay que renovarlo.');
    if (respuesta.status === 404) return null;
    if (!respuesta.ok) throw new Error(`La API respondió ${respuesta.status}`);
    return respuesta.json();
  }

  return {
    // Lo que muestra la tarjeta de recepción del celular.
    async consultar(tipo, numero) {
      const estado = await pedir(`/estados/${encodeURIComponent(tipo)}/${encodeURIComponent(numero)}`);
      if (estado === null) return null;
      return {
        clave: estado.documentoHash,
        nombre: estado.nombreCorto,
        documento: estado.documentoEnmascarado,
        estado: estado.estado,
        venceEl: estado.venceEl ?? null,
        dias: estado.diasRestantes ?? estado.diasMora ?? 0,
      };
    },
    // La copia completa para cuando se cae el internet.
    async descargarCopia() {
      const { generadoEl, estados } = await pedir('/estados');
      return { generadoEl, porClave: Object.fromEntries(estados.map((e) => [e.documentoHash, e])) };
    },
  };
}
