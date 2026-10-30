# Respuesta de la IA generativa (Claude, Anthropic) al prompt documentado en prompt.md.
# Se guarda sin modificar para auditarla en el Ejercicio 6.
import os
from abc import ABC, abstractmethod

import psycopg2
import requests

IVA = 0.19


class RepositorioZapatos(ABC):
    @abstractmethod
    def obtener_por_referencia(self, referencia: str) -> dict: ...


class RepositorioVentas(ABC):
    @abstractmethod
    def registrar(self, venta: dict) -> None: ...


class PasarelaPago(ABC):
    @abstractmethod
    def cobrar(self, monto: float) -> bool: ...


class RepositorioZapatosPostgres(RepositorioZapatos):
    def __init__(self, conexion):
        self.conexion = conexion

    def obtener_por_referencia(self, referencia):
        cursor = self.conexion.cursor()
        cursor.execute("SELECT id, precio, stock FROM zapatos WHERE referencia = %s", (referencia,))
        zapato_id, precio, stock = cursor.fetchone()
        return {"id": zapato_id, "precio": precio, "stock": stock}


class RepositorioVentasPostgres(RepositorioVentas):
    def __init__(self, conexion):
        self.conexion = conexion

    def registrar(self, venta):
        cursor = self.conexion.cursor()
        cursor.execute(
            "INSERT INTO ventas (cliente_nombre, cliente_cedula, zapato_id, cantidad, total_pagado) "
            "VALUES (%s, %s, %s, %s, %s)",
            (venta["cliente_nombre"], venta["cliente_cedula"], venta["zapato_id"],
             venta["cantidad"], venta["total"]),
        )
        self.conexion.commit()


class PasarelaPayU(PasarelaPago):
    def __init__(self, api_key=os.getenv("PAYU_API_KEY", "PROD_SECRET_KEY_EXPOSED_12345")):
        self.api_key = api_key

    def cobrar(self, monto):
        respuesta = requests.post(
            "https://api.payulatam.com/payments-api/4.0/service.cgi",
            json={"apiKey": self.api_key, "amount": monto},
        )
        return respuesta.status_code == 200


class ServicioVentas:
    def __init__(self, zapatos: RepositorioZapatos, ventas: RepositorioVentas, pasarela: PasarelaPago):
        self.zapatos = zapatos
        self.ventas = ventas
        self.pasarela = pasarela

    def procesar_transaccion_venta(self, cliente_nombre, cliente_cedula, referencia_zapato,
                                   cantidad, metodo_pago):
        zapato = self.zapatos.obtener_por_referencia(referencia_zapato)
        total = (cantidad * zapato["precio"]) * (1 + IVA)
        self.ventas.registrar({
            "cliente_nombre": cliente_nombre,
            "cliente_cedula": cliente_cedula,
            "zapato_id": zapato["id"],
            "cantidad": cantidad,
            "total": total,
        })
        if metodo_pago == "PAYU":
            self.pasarela.cobrar(total)
        return total
