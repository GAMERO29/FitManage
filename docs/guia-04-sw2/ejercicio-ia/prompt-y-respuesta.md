# Ejercicio 4 · Refactorización hexagonal propuesta por una IA

**Herramienta:** Claude (Anthropic). **Fecha:** 30/10/2026. **Datos enviados:** solo el fragmento ficticio de la Guía 1 (`docs/guia-01-sw2/ejercicio-ia/legado.py`).

## Prompt

> Refactoriza este código Python hacia Arquitectura Hexagonal (puertos y adaptadores). Usa SQLAlchemy para la base de datos y separa claramente dominio, aplicación e infraestructura.
>
> (se pegó `legado.py`: 21 líneas, 19 con código)

## Respuesta

El código completo que entregó la IA está, sin modificar, en `respuesta_ia/`: 10 archivos con código y 178 líneas no vacías.

| Archivo | Contenido |
| --- | --- |
| `domain/entities.py` | `Zapato`, `Venta` |
| `domain/ports.py` | 6 interfaces: `ZapatoRepositoryPort`, `VentaRepositoryPort`, `PaymentGatewayPort`, `TaxCalculatorPort`, `LoggerPort`, `UnitOfWorkPort` |
| `application/dto.py`, `application/mappers.py` | DTO de entrada y salida y un mapeador |
| `application/use_cases.py` | `ProcesarVentaUseCase` (importa `sqlalchemy.exc`) |
| `infrastructure/*.py` | repositorios SQLAlchemy, PayU, calculadora de IVA, logger |
| `main.py` | raíz de composición |

## Corrección

Ver `corregido/` (2 archivos de producción: `nucleo_ventas.py` y `adaptador_sqlite.py`; 7 pruebas) y la sección del Ejercicio 4 en la guía resuelta.
