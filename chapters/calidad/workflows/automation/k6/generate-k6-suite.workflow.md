---
id: generate-k6-suite
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Workflow para generar una suite K6 completa (5 scripts + utils + infraestructura) desde un spec OpenAPI/Swagger.
tags: [k6, workflow, greenfield, openapi, swagger, performance]
---

# Generate K6 Suite — Workflow

## Cuándo usar

Cuando el routing del chapter (`[[calidad-route-test-generation]]`) detecta intent K6 + greenfield (no hay proyecto K6 previo). El intent se confirma con `[[calidad-intent-detection]]` y la naturaleza greenfield con `[[calidad-brownfield-vs-greenfield]]`.

## Inputs

Gobernados por `[[calidad-mandatory-inputs-protocol]]`:

- **Obligatorios**: `spec` (OpenAPI 3.x o Swagger 2.0), `project_name`, `output_path`, `base_url`.
- **Opcionales / recomendados**: `user_story` (para derivar SLA y elegir tier), `firma` (perfil del cliente — banca core → Conservative), `auth_mode` (`spec` default | `external` override — ver paso 3 y `[[k6-enums-headers-security-extraction]]`).

## Pasos

### Paso 1 — Validar spec

Aplica `[[calidad-spec-validation]]`: >200 chars, JSON/YAML parseable, contiene `openapi` o `swagger`, `info`, `paths`. Si falla, detente y reporta.

### Paso 2 — Extraer endpoints

Lista cada `path` con `method`, `operationId`, parámetros y referencias de schema. Emite el checklist legible antes de generar código.

### Paso 3 — Extraer config data y decidir auth_mode

Aplica `[[k6-enums-headers-security-extraction]]`: enums, headers requeridos y security schemes. Decide si `authToken` y `Authorization` aplican según el **modo de autenticación**:

- Rama A — `auth_mode = spec` (default, sin input explícito): incluye `authToken`/`Authorization` SOLO si el spec declara `security` (`components.securitySchemes` / `securityDefinitions`). Si no hay security, **no** los emitas.
- Rama B — `auth_mode = external` (input explícito o env `EXTERNAL_AUTH=true`): incluye `authToken: __ENV.AUTH_TOKEN || ''` en `config.js` y `Authorization: Bearer ${config.authToken}` en `getDefaultHeaders()` **siempre**, aunque el spec no declare security. Marca `AUTH_TOKEN` como env var obligatoria para el README.

Anota la rama elegida; los pasos 6 y 7 dependen de ella.

### Paso 4 — Detectar CRUD flows

Aplica `[[k6-crud-dynamic-id-correlation]]`: normaliza paths, agrupa, clasifica `full` o `partial`.

### Paso 5 — Elegir tier de thresholds

Aplica `[[k6-thresholds-three-tiers]]`: deriva desde `user_story.SLA` → `firma.SLA` → Moderate default.

### Paso 6 — Generar utils template

Construye el contenido de `utils.js` (`uuidv4`, `getDefaultHeaders`, `buildXxxBody`) según `[[k6-config-and-utils-modules]]`. Aún no se escribe a disco; sirve de plantilla para los tests.

### Paso 7 — Emitir archivos (orden estricto)

Aplica `[[calidad-streaming-files-protocol]]` y `[[k6-greenfield]]`:

1. Tests primero, en este orden: `smoke-test.js`, `load-test.js`, `stress-test.js`, `spike-test.js`, `soak-test.js`. Cada uno incluye stages, thresholds, `default function`, `check()` con validación de campos, `sleep(1)`, `handleSummary()` (`[[k6-handle-summary-evidence]]`). Genera cada test invocando `[[k6-generate-script-prompt]]`.
2. Luego `utils.js` (vía `[[k6-generate-utils-prompt]]`) y `config.js` (vía `[[k6-extract-config-prompt]]`).
3. Por último: `package.json`, `run-all.sh`, `.gitignore`, `README.md` (ver `[[k6-project-structure]]`).

### Paso 8 — Validar DoD

Recorre el checklist de 10 items (`## Criterios de finalización`). Si algún ítem falla, regenera el archivo correspondiente antes de cerrar. Registra trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

## Criterios de finalización (DoD — 10 items)

1. Todos los imports usados (sin dead imports).
2. Todos los endpoints del spec cubiertos al menos por un script.
3. DELETE incluido en cada flujo CRUD detectado.
4. Credenciales y `baseUrl` provienen de `config.js`/`__ENV` (cero hardcoded en tests). En modo `external`, `AUTH_TOKEN` está documentada como obligatoria en el `README.md`.
5. `options.stages` y `options.thresholds` presentes en cada uno de los 5 scripts.
6. Cada `check()` valida campos del response (no solo el status code).
7. Flujos CRUD usan IDs dinámicos con guard clause (`[[k6-crud-dynamic-id-correlation]]`).
8. Headers se construyen vía `getDefaultHeaders()` de `utils.js` (no inline).
9. Payloads se construyen vía `buildXxxBody()` de `utils.js` (no inline).
10. `handleSummary()` presente en cada script exportando JSON a `results/`.
