# Pre-flight check — K6 greenfield

Antes de generar la suite K6 el agente debe validar el entorno local, la accesibilidad del `BASE_URL` y la presencia de credenciales si el spec declara `security`. El protocolo de enforcement está descrito en `[[calidad-pre-generation-protocol]]`.

## Validaciones obligatorias

- `k6 version` debe responder. Versión recomendada ≥ 0.50.0; versiones inferiores no garantizan `handleSummary()` ni los thresholds compuestos usados por la suite (`[[k6-thresholds-three-tiers]]`).
- `BASE_URL` accesible vía `curl -sI --max-time 5 "$BASE_URL"`. Si responde 4xx/5xx pero el host resuelve, considerarlo alcanzable para el pre-flight (el smoke detectará el detalle).
- `AUTH_TOKEN` exportado si el spec declara `security` (`auth_mode = spec` con security activa) o si el operador eligió `auth_mode = external`. Si falta, degradar el smoke a `partial` y reportar al usuario.
- Conectividad a `jslib.k6.io` (HTTPS) para resolver los imports del runtime estándar. Si el ambiente es air-gapped, validar que existe una copia vendored y ajustar los imports — el patrón está documentado en `[[k6-handle-summary-evidence]]`.

## Degradación

- `k6` ausente o demasiado antiguo: degradar a `scaffold-only`. Recordar al usuario el comando de instalación (`brew install k6`, `apt install k6` o `choco install k6`).
- `BASE_URL` no resuelve DNS: degradar a `scaffold-only` y documentar la razón en `.evidence/preflight-result.json`.
- `AUTH_TOKEN` faltante con `auth_mode = external`: no generar requests reales; producir scaffold con `// TODO: exportar AUTH_TOKEN antes de ejecutar`.
- `jslib.k6.io` inalcanzable: cambiar imports a la copia vendored y dejar nota en el README.

## Script shippeable

El agente debe copiar `templates/preflight-k6.sh` al proyecto generado bajo `scripts/preflight.sh`. El script reproduce las validaciones en CI o en máquinas de desarrolladores. Ver `[[calidad-delivery-gate-contract]]` para la convención de entregables y `[[calidad-post-generation-protocol]]` para el archivado del resultado del pre-flight.
