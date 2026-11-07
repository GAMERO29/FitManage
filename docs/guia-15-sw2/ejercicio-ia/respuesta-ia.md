## 1. Ingeniería inversa: qué hace el fragmento

Implementa un **patrón de idempotencia** para el endpoint `POST /api/v1/pagos`. Si el cliente reenvía la misma petición (por ejemplo, tras un timeout de red), el sistema no registra el pago dos veces y devuelve la respuesta original.

**Flujo actual:**

1. El cliente envía la cabecera `Idempotency-Key` con un UUID.
2. Se parsea el cuerpo JSON y se construye una `SolicitudPago`.
3. Dentro de una transacción externa, se intenta insertar un `IdempotenciaModelo` con esa clave.
   - Si la clave ya existe (`IntegrityError`), se devuelve la respuesta guardada, marcada con `Idempotent-Replayed: true`.
   - Si la clave es nueva, se registra el pago, se guarda el código HTTP y el cuerpo de la respuesta en ese mismo registro, y se responde `201` con `Location`.
4. Como la reserva de la clave y el pago están en la misma transacción, un fallo a mitad de camino deshace todo y la clave queda libre para reintentar.

**Reglas de negocio implícitas:**

| Regla | Dónde se ve |
|---|---|
| Solo personal autorizado (`TODO_EL_PERSONAL`) registra pagos. | `@endpoint(roles=...)` |
| Un pago se asocia a un plan (`planId`) y a un documento de identidad (`tipoDocumento` + `numeroDocumento`). | `SolicitudPago` |
| El medio de pago es obligatorio; la referencia (p. ej., número de transacción) es opcional. | `datos["medio"]`, `datos.get("referencia")` |
| Cada pago queda trazado al usuario que lo registró. | `registrar_pago(solicitud, request.usuario)` |
| Una misma operación no debe duplicar cobros. | Todo el mecanismo de idempotencia |
| La respuesta repetida es idéntica a la original (mismo estado y cuerpo). | `_respuesta_guardada` |

**Problemas que encuentro en el código legacy (deuda técnica):**

1. **La clave es global, no por usuario.** La clave primaria es solo `clave`, así que si el usuario B reenvía una clave del usuario A, recibe la respuesta del pago de A. Es un riesgo de seguridad y de colisiones.
2. **No se verifica que el cuerpo coincida.** Si llega la misma clave con datos distintos, se devuelve el resultado anterior en silencio. Lo esperable es rechazarlo (por ejemplo, con `422`).
3. **Entradas inválidas producen errores 500.** `uuid.UUID(...)`, `TipoDocumento(...)` y `datos["..."]` lanzan excepciones sin manejar.
4. **Lógica duplicada.** La construcción de `Location` aparece dos veces, y la respuesta se arma en dos sitios distintos.
5. **Mezcla de responsabilidades.** La vista orquesta HTTP, idempotencia, validación y dominio a la vez.
6. **Sin caducidad.** La tabla crece indefinidamente; `creada` no se usa para limpiar registros.
7. **Supuestos frágiles.** `_respuesta_guardada` asume que `cuerpo['id']` siempre existe.

## 2. Refactorización propuesta

Cambios principales:

- La clave se identifica por **usuario + clave** (con un `id` autoincremental como PK).
- Se guarda una **huella SHA-256** del cuerpo para detectar reutilización de clave con datos distintos (`422`).
- Las entradas inválidas responden `400` mediante una excepción propia.
- La construcción de la respuesta está centralizada en `_respuesta`.
- La reserva de la clave está aislada en `_reservar`.

Supuestos: `UsuarioModelo`, `TODO_EL_PERSONAL`, `TipoDocumento`, `SolicitudPago`, `endpoint`, `leer_json`, `contenedor`, `presentacion` y `_nombre_plan` existen tal como en tu código original.

```python
import hashlib
import json
import uuid
from dataclasses import dataclass

from django.db import IntegrityError, models, transaction
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_POST

RUTA_PAGOS = "/api/v1/pagos"
CABECERA_CLAVE = "Idempotency-Key"
CABECERA_REPETIDA = "Idempotent-Replayed"


class RegistroIdempotencia(models.Model):
    """Respuesta ya entregada para una petición idempotente, por usuario y clave.

    estado_http == 0 significa "sin completar". Como la reserva y el resultado
    se confirman en la misma transacción, en la práctica nunca se observa.
    """

    usuario = models.ForeignKey(UsuarioModelo, on_delete=models.CASCADE)
    clave = models.UUIDField()
    huella = models.CharField(max_length=64)
    estado_http = models.PositiveSmallIntegerField(default=0)
    cuerpo = models.JSONField(default=dict)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "clave"],
                name="uq_idempotencia_usuario_clave",
            ),
        ]


class PeticionInvalida(Exception):
    def __init__(self, mensaje: str, estado: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.estado = estado


@dataclass(frozen=True)
class PeticionPago:
    clave: uuid.UUID
    huella: str
    solicitud: SolicitudPago


def _error(mensaje: str, estado: int) -> JsonResponse:
    return JsonResponse({"error": mensaje}, status=estado)


def _huella(datos: dict) -> str:
    canonico = json.dumps(datos, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonico.encode("utf-8")).hexdigest()


def _leer_peticion(request: HttpRequest) -> PeticionPago:
    cabecera = request.headers.get(CABECERA_CLAVE)
    if not cabecera:
        raise PeticionInvalida(f"Falta la cabecera {CABECERA_CLAVE}.")
    try:
        clave = uuid.UUID(cabecera)
    except ValueError as exc:
        raise PeticionInvalida(f"{CABECERA_CLAVE} debe ser un UUID válido.") from exc

    datos = leer_json(request)
    try:
        solicitud = SolicitudPago(
            tipo_documento=TipoDocumento(datos["tipoDocumento"]),
            numero_documento=datos["numeroDocumento"],
            plan_id=uuid.UUID(datos["planId"]),
            medio=datos["medio"],
            referencia=datos.get("referencia"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PeticionInvalida(f"Datos de pago inválidos: {exc}") from exc

    return PeticionPago(clave=clave, huella=_huella(datos), solicitud=solicitud)


def _reservar(usuario, peticion: PeticionPago) -> tuple[RegistroIdempotencia, bool]:
    """Devuelve (registro_nuevo, True) o (registro_previo, False) si la clave ya existía."""
    try:
        with transaction.atomic():
            registro = RegistroIdempotencia.objects.create(
                usuario=usuario,
                clave=peticion.clave,
                huella=peticion.huella,
            )
        return registro, True
    except IntegrityError:
        registro = RegistroIdempotencia.objects.get(usuario=usuario, clave=peticion.clave)
        return registro, False


def _respuesta(cuerpo: dict, estado: int, repetida: bool = False) -> JsonResponse:
    respuesta = JsonResponse(cuerpo, status=estado)
    respuesta["Location"] = f"{RUTA_PAGOS}/{cuerpo['id']}"
    if repetida:
        respuesta[CABECERA_REPETIDA] = "true"
    return respuesta


def _repetir(registro: RegistroIdempotencia, huella: str) -> JsonResponse:
    if registro.huella != huella:
        return _error("La clave de idempotencia ya se usó con un cuerpo distinto.", 422)
    if registro.estado_http == 0:
        return _error("Ya existe una petición en curso con esta clave.", 409)
    return _respuesta(registro.cuerpo, registro.estado_http, repetida=True)


@require_POST
@endpoint(roles=TODO_EL_PERSONAL)
def registrar_pago(request: HttpRequest) -> JsonResponse:
    try:
        peticion = _leer_peticion(request)
    except PeticionInvalida as exc:
        return _error(exc.mensaje, exc.estado)

    with transaction.atomic():
        registro, nueva = _reservar(request.usuario, peticion)
        if not nueva:
            return _repetir(registro, peticion.huella)

        pago = contenedor.registro_pago().registrar_pago(peticion.solicitud, request.usuario)
        cuerpo = presentacion.pago(pago, _nombre_plan(pago.plan_id))

        registro.estado_http = 201
        registro.cuerpo = cuerpo
        registro.save(update_fields=["estado_http", "cuerpo"])

    return _respuesta(cuerpo, 201)
```

**Notas sobre la migración:**

- Cambiar la PK de `clave` a un `id` autoincremental y añadir la restricción `(usuario, clave)` requiere una migración de esquema. Si la tabla tiene datos, puedes vaciarla (son registros de caché con vida corta) o escribir una migración de datos.
- Conviene añadir una tarea periódica que elimine registros con más de 24 h (`creada`). Así la tabla no crece sin límite.
- Si el decorador `endpoint` ya convierte excepciones de dominio en respuestas HTTP, puedes dejarlo como está. Si no, las excepciones de `registrar_pago` seguirán produciendo 500.

## 3. Herramienta para medir la deuda técnica

**Recomendación principal: SonarQube** (Community Build, self-hosted y gratuita) o **SonarCloud** (gratuita para proyectos públicos).

Por qué:

- Calcula la deuda técnica como **tiempo estimado de remediación** (minutos u horas), lo que facilita hablar de prioridades.
- Detecta *code smells*, bugs, vulnerabilidades, código duplicado y complejidad cognitiva.
- Soporta Python y Django, y puede importar cobertura de `coverage.py`.
- Su *quality gate* permite bloquear merges cuando la deuda supera un umbral.

Pasos básicos:

1. Levanta SonarQube con Docker (`docker run -d -p 9000:9000 sonarqube:community`).
2. Crea un proyecto y genera un token.
3. Ejecuta `coverage run -m pytest` y luego `sonar-scanner` con la configuración del proyecto.

**Complementos útiles y ligeros:**

- **Ruff**: linter rápido que reemplaza a Flake8/isort.
- **Radon**: complejidad ciclomática e índice de mantenibilidad (`radon cc -s -a fitmanage/`).
- **Bandit**: análisis de seguridad estático para Python. Habría señalado el problema de la clave global si lo combinas con revisión manual.
