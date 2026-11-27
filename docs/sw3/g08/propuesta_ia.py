"""Salida de la IA, copiada sin cambios (fragmento relevante). NO se usa en el código de FitManage.

Prompt: «Propón el modelo de clases del dominio de FitManage (socios, planes, pagos y membresías
de un gimnasio) en Python, con sus atributos y métodos.»
"""

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass
class Membresia:
    socio_documento: str  # identifica al socio
    fecha_inicio: date
    duracion_dias: int
    estado: str = "ACTIVA"

    @property
    def fecha_vencimiento(self) -> date:
        return self.fecha_inicio + timedelta(days=self.duracion_dias)

    def set_estado(self, nuevo_estado: str) -> None:
        self.estado = nuevo_estado

    def esta_activa(self, hoy: date) -> bool:
        return self.estado == "ACTIVA" and hoy <= self.fecha_vencimiento
