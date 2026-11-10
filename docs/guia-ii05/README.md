# Guía II-05 · Versiones, despliegue y operación

- `entrega_controlada.sh` y `.txt`: entrega controlada en dos entornos locales separados (versión anterior `992ddc7` → candidata `359aaeb`), verificación funcional, caída de la base, recuperación, restauración en un destino aparte y vuelta a la versión anterior.
- `docs/runbooks/Runbook_entrega.md`: el procedimiento, con quién decide y cuándo se detiene.
- `docs/releases/v1.1.0.md`: identidad de la entrega (commit, imagen, huella, esquema y contrato).
- `.github/workflows/release.yml`: etiqueta y publica una versión solo si el commit tuvo un despliegue exitoso.
