# Auditoría de IA · Guía 05 (reorganización de paquetes)

**Prompt.** «Propón una reorganización de paquetes para FitManage (Django, socios, planes, pagos y
reportes) que deje mejor separadas las capas.» Se entregó solo el árbol de carpetas.

**Fragmento relevante de la salida.**

```text
fitmanage/
  planes/   models.py  services.py  views.py  permissions.py
  pagos/    models.py  services.py  views.py
  socios/   ...
# planes/services.py
from django.db import models
from .models import PlanModelo
class CalculadoraMembresia: ...        # movida aquí desde dominio/
# planes/permissions.py
class VerDesactivados(BasePermission):  # solo el administrador ve los planes desactivados
```

## Verificación con importaciones concretas

| Afirmación | Criterio | Resultado |
|---|---|---|
| «Las capas quedan mejor separadas» | ¿Dónde quedan las reglas de negocio y qué importan? | **No.** `CalculadoraMembresia` (RN-03 a RN-05) pasa a un módulo que importa `django.db`. Hoy `test_el_nucleo_no_importa_infraestructura` impide justo eso. |
| La regla de los planes desactivados va en `permissions.py` | ¿La regla queda en presentación o en aplicación? | **Queda en presentación.** Si mañana otro consumidor (un reporte, un comando) lista planes, la regla no lo acompaña. En FitManage está en `GestionPlanesService.listar` y la prueba `test_solo_el_administrador_ve_los_planes_desactivados` la cubre sin HTTP. |
| Paquetes por funcionalidad | Fowler, *PresentationDomainDataLayering*: los módulos por dominio convienen en sistemas grandes | **Válido como dirección, no ahora.** FitManage tiene 49 módulos; las capas como primer nivel siguen siendo manejables, y la regla de dependencias funciona con esa estructura. |

## Corrección

Me quedo con la estructura hexagonal actual y con el cambio real de la guía: la vista de
`GET /planes` deja de consultar `PlanModelo` y llama a `GestionPlanesService.listar()`
([`regla_dependencias.txt`](regla_dependencias.txt), [`importaciones_antes.tsv`](importaciones_antes.tsv),
[`importaciones_despues.tsv`](importaciones_despues.tsv)).

**Limitación.** La misma sesión generó y auditó la propuesta.
