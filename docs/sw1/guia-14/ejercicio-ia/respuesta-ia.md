Aquí tienes un archivo de pruebas con pytest para `CalculadoraMembresia`. Cubre RN-03, RN-04 y RN-05, incluidos los bordes de fecha.

No tengo a la vista `dominio/modelos.py`, así que usé un doble de prueba (`PagoFalso`) con los dos atributos que usa la calculadora: `fecha_vencimiento` y `esta_vigente()`. Si tu clase `Pago` tiene un constructor real, puedes reemplazar `PagoFalso` por ella. También tendrás que ajustar el import de `CalculadoraMembresia` a la ruta real de tu módulo.

```python
"""Pruebas unitarias para CalculadoraMembresia (RN-03, RN-04 y RN-05)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import pytest

from dominio.modelos import EstadoMembresia
from dominio.calculos import CalculadoraMembresia  # ajustar a la ruta real del módulo

HOY = date(2026, 6, 15)
UN_DIA = timedelta(days=1)


@dataclass
class PagoFalso:
    """Doble de prueba: solo expone lo que usa la calculadora."""

    fecha_vencimiento: date
    vigente: bool = True

    def esta_vigente(self) -> bool:
        return self.vigente


def pago(vencimiento: date, vigente: bool = True) -> PagoFalso:
    return PagoFalso(fecha_vencimiento=vencimiento, vigente=vigente)


@pytest.fixture
def calc() -> CalculadoraMembresia:
    return CalculadoraMembresia()


# RN-03 -----------------------------------------------------------------------

class TestCalcularVencimiento:
    @pytest.mark.parametrize(
        "inicio, duracion, esperado",
        [
            (date(2026, 1, 1), 30, date(2026, 1, 30)),
            (date(2026, 1, 1), 1, date(2026, 1, 1)),        # el último día cuenta
            (date(2026, 1, 31), 30, date(2026, 3, 1)),      # cruza febrero (no bisiesto)
            (date(2024, 2, 1), 30, date(2024, 3, 1)),       # cruza febrero bisiesto
            (date(2026, 12, 1), 365, date(2027, 11, 30)),   # cruza el año
        ],
    )
    def test_vencimiento_es_inicio_mas_duracion_menos_uno(self, calc, inicio, duracion, esperado):
        assert calc.calcular_vencimiento(inicio, duracion) == esperado


# RN-04 -----------------------------------------------------------------------

class TestCalcularFechaInicio:
    def test_sin_pagos_inicia_hoy(self, calc):
        assert calc.calcular_fecha_inicio([], HOY) == HOY

    def test_renovacion_anticipada_empieza_el_dia_siguiente_al_vencimiento(self, calc):
        vencimiento = HOY + timedelta(days=10)
        assert calc.calcular_fecha_inicio([pago(vencimiento)], HOY) == vencimiento + UN_DIA

    def test_vence_hoy_todavia_cuenta_como_renovacion_anticipada(self, calc):
        # Límite: vencimiento == hoy, la membresía sigue vigente hoy.
        assert calc.calcular_fecha_inicio([pago(HOY)], HOY) == HOY + UN_DIA

    def test_vencida_ayer_inicia_hoy(self, calc):
        assert calc.calcular_fecha_inicio([pago(HOY - UN_DIA)], HOY) == HOY

    def test_usa_el_vencimiento_mas_lejano(self, calc):
        pagos = [pago(HOY + timedelta(days=5)), pago(HOY + timedelta(days=20)), pago(HOY - timedelta(days=3))]
        assert calc.calcular_fecha_inicio(pagos, HOY) == HOY + timedelta(days=21)

    def test_ignora_pagos_no_vigentes(self, calc):
        pagos = [pago(HOY + timedelta(days=30), vigente=False)]
        assert calc.calcular_fecha_inicio(pagos, HOY) == HOY

    def test_acepta_iterables_que_no_son_listas(self, calc):
        pagos = iter([pago(HOY + timedelta(days=10))])
        assert calc.calcular_fecha_inicio(pagos, HOY) == HOY + timedelta(days=11)


# RN-05 -----------------------------------------------------------------------

class TestEstadoDe:
    def test_sin_pagos_es_sin_membresia(self, calc):
        assert calc.estado_de([], HOY) == (EstadoMembresia.SIN_MEMBRESIA, None)

    def test_solo_pagos_no_vigentes_es_sin_membresia(self, calc):
        pagos = [pago(HOY + timedelta(days=30), vigente=False)]
        assert calc.estado_de(pagos, HOY) == (EstadoMembresia.SIN_MEMBRESIA, None)

    def test_vencimiento_futuro_es_activo(self, calc):
        vencimiento = HOY + timedelta(days=10)
        assert calc.estado_de([pago(vencimiento)], HOY) == (EstadoMembresia.ACTIVO, vencimiento)

    def test_el_dia_del_vencimiento_sigue_activo(self, calc):
        assert calc.estado_de([pago(HOY)], HOY) == (EstadoMembresia.ACTIVO, HOY)

    def test_un_dia_despues_del_vencimiento_es_vencido(self, calc):
        assert calc.estado_de([pago(HOY - UN_DIA)], HOY) == (EstadoMembresia.VENCIDO, HOY - UN_DIA)

    def test_estado_se_deriva_del_pago_mas_lejano(self, calc):
        pagos = [pago(HOY - timedelta(days=30)), pago(HOY + timedelta(days=5))]
        assert calc.estado_de(pagos, HOY) == (EstadoMembresia.ACTIVO, HOY + timedelta(days=5))


# Días de mora ---------------------------------------------------------------

class TestDiasDeMora:
    def test_activo_no_tiene_mora(self, calc):
        assert calc.dias_de_mora([pago(HOY + timedelta(days=3))], HOY) == 0

    def test_el_dia_del_vencimiento_no_tiene_mora(self, calc):
        assert calc.dias_de_mora([pago(HOY)], HOY) == 0

    def test_un_dia_de_mora(self, calc):
        assert calc.dias_de_mora([pago(HOY - UN_DIA)], HOY) == 1

    def test_mora_de_varios_dias(self, calc):
        assert calc.dias_de_mora([pago(HOY - timedelta(days=45))], HOY) == 45

    def test_sin_membresia_no_tiene_mora(self, calc):
        assert calc.dias_de_mora([], HOY) == 0
```

Para ejecutarlo, desde la raíz del proyecto:

```
pytest -v
```

Si `dominio` no se encuentra al importar, agrega la raíz al `PYTHONPATH` o crea un `conftest.py` vacío en la raíz.

Dos observaciones sobre la clase que las pruebas no cubren:

- `calcular_vencimiento` no valida `duracion_dias`. Con 0 o un valor negativo devuelve una fecha anterior al inicio sin error. Si quieres que eso sea un error, habría que añadir la validación y una prueba con `pytest.raises(ValueError)`.
- Los tests de `estado_de` y `dias_de_mora` dependen de que `esta_vigente()` sea solo un filtro. Si ese método depende de la fecha actual del sistema, conviene que lo pruebes por separado en la clase `Pago`.
