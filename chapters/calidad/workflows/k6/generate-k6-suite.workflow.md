---
id: calidad-generate-k6-suite
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [k6]
description: Workflow para generar una suite K6 completa (3 scripts obligatorios + hasta 2 opt-in + utils + infraestructura) desde un spec OpenAPI/Swagger.
tags: [k6, workflow, greenfield, openapi, swagger, performance]
---

# Generate K6 Suite — Workflow

## Cuándo usar

Cuando el routing del chapter (`[[calidad-route-test-generation]]`) detecta intent K6 + greenfield (no hay proyecto K6 previo). El intent se confirma con `[[calidad-intent-detection]]` y la naturaleza greenfield con `[[calidad-brownfield-vs-greenfield]]`.

## Inputs

Gobernados por `[[calidad-mandatory-inputs-protocol]]`:

- **Obligatorios**: `spec` (OpenAPI 3.x o Swagger 2.0), `project_name`, `output_path`, `base_url`.
- **Opcionales / recomendados**: `user_story` (para derivar SLA y elegir tier), `firma` (perfil del sistema — mission-critical → Conservative; business-as-usual → Moderate; internal → Relaxed), `auth_mode` (`spec` default | `external` override — ver paso 3 y `[[calidad-k6-greenfield]] (consultar `references/enums-headers-security-extraction.md` en su subfolder)`).

## Pasos

### Paso 1 (OBLIGATORIO) — Pre-flight check del stack

Antes de cualquier otra acción, ejecutar el pre-flight según [[calidad-k6-greenfield]] (consultar `references/preflight.md` en su subfolder):
- Si pasa: continuar al paso 2.
- Si falla: aplicar las degradaciones documentadas en `preflight.md` y reportar al usuario antes de proceder.
- Persistir el resultado en `.evidence/preflight-result.json`.

Este paso es enforcement obligatorio según `[[calidad-pre-generation-protocol]]`.

### Paso 2 — Análisis previo (STRATEGY.md)

Antes de generar cualquier código, generar `STRATEGY.md` en el `output_path` según ``references/templates.md` (sección `STRATEGY.md`)` y `[[calidad-pre-design-strategy-document]]`. Presentar al usuario y esperar:
- "aprobado" → continuar al siguiente paso.
- "modificar X" → iterar el documento; volver a presentar.

NUNCA generar código sin STRATEGY.md aprobado explícitamente.

### Paso 3 — Validar spec

Aplica `[[calidad-spec-validation]]`: >200 chars, JSON/YAML parseable, contiene `openapi` o `swagger`, `info`, `paths`. Si falla, detente y reporta.

### Paso 4 — Extraer endpoints

Lista cada `path` con `method`, `operationId`, parámetros y referencias de schema. Emite el checklist legible antes de generar código.

### Paso 5 — Extraer config data y decidir auth_mode

Aplica `[[calidad-k6-greenfield]] (consultar `references/enums-headers-security-extraction.md` en su subfolder)`: enums, headers requeridos y security schemes. Decide si `authToken` y `Authorization` aplican según el **modo de autenticación**:

- Rama A — `auth_mode = spec` (default, sin input explícito): incluye `authToken`/`Authorization` SOLO si el spec declara `security` (`components.securitySchemes` / `securityDefinitions`). Si no hay security, **no** los emitas.
- Rama B — `auth_mode = external` (input explícito o env `EXTERNAL_AUTH=true`): incluye `authToken: __ENV.AUTH_TOKEN || ''` en `config.js` y `Authorization: Bearer ${config.authToken}` en `getDefaultHeaders()` **siempre**, aunque el spec no declare security. Marca `AUTH_TOKEN` como env var obligatoria para el README.

Anota la rama elegida; los pasos siguientes dependen de ella.

### Paso 6 — Detectar CRUD flows

Aplica `[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)`: normaliza paths, agrupa, clasifica `full` o `partial`.

### Paso 7 — Elegir tier de thresholds

Aplica `[[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)`: deriva desde `user_story.SLA` → `firma.SLA` → Moderate default.

### Paso 8 — Generar utils template

Construye el contenido de `utils.js` (`uuidv4`, `getDefaultHeaders`, `buildXxxBody`) según `[[calidad-k6-greenfield]] (consultar `references/config-and-utils-modules.md` en su subfolder)`. Aún no se escribe a disco; sirve de plantilla para los tests.

### Paso 9 — Emitir archivos (orden estricto)

Aplica `[[calidad-streaming-files-protocol]]` y `[[calidad-k6-greenfield]]`:

1. Tests primero, en este orden: primero los 3 obligatorios `smoke-test.js`, `load-test.js`, `stress-test.js`, luego los opt-in activados (`spike-test.js`, `soak-test.js`) si `user_story` / `firma` / `risk_map` los amerita. Ver [[calidad-k6-greenfield]] (consultar `references/vocabulary-and-scenario-mapping.md`). Cada script incluye stages, thresholds, `default function`, `check()` con validación de campos, `sleep(1)`, `handleSummary()` (`[[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder)`). Genera cada test invocando `[[calidad-k6-generate-script-prompt]]`.
2. Luego `utils.js` (vía `[[calidad-k6-generate-utils-prompt]]`) y `config.js` (vía `[[calidad-k6-extract-config-prompt]]`).
3. Por último: `package.json`, `run-all.sh`, `.gitignore`, `README.md` (ver `[[calidad-k6-greenfield]] (consultar `references/project-structure.md` en su subfolder)`).

### Paso 10 — Validar DoD

Recorre el checklist de 10 items (`## Criterios de finalización`). Si algún ítem falla, regenera el archivo correspondiente antes de cerrar. Registra trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** En K6, esta fase usa **únicamente `smoke-test.js`** como verificación rápida del scaffold: 1-2 VUs por un minuto. Los scripts `load`, `stress`, `spike`, `soak` NO se ejecutan dentro del loop de auto-corrección porque generan carga real y requieren ventana de mantenimiento + gobernanza (`[[calidad-k6-greenfield]] (consultar `references/thresholds-three-tiers.md` en su subfolder)`).

**Si `execution_target: mock | hybrid`** (resuelto por `[[calidad-sut-readiness-gate]]`): levantar el mock Mockoon antes del smoke (`[[calidad-service-virtualization-mockoon]]`) y correr con `-e BASE_URL=http://localhost:3010/api`. **Regla dura**: contra mock SOLO se ejecuta el smoke 1:1 para validar la construcción de los scripts (correlación, checks, estructura); `load/stress/spike/soak` contra mock están PROHIBIDOS y sus métricas jamás se reportan — el mock no representa el comportamiento del SUT bajo carga. La ejecución real de la suite de performance queda para el switchover (`certification: pending_real_integration` en el delivery gate) vía `[[calidad-calibrate-k6-thresholds]]` bajo ventana coordinada.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin `k6`, sin red al `BASE_URL`, ambiente productivo sin autorización), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** sólo `smoke-test.js` vía `[[calidad-test-execution-orchestration]]` (`k6 run -e BASE_URL=$BASE_URL tests/smoke-test.js`, agregando `AUTH_TOKEN` si `auth_mode = external`). Capturar `results/${timestamp}-summary.json` como evidencia.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky (típico K6: 401 por token expirado, payload mal correlacionado, threshold inicial irreal, endpoint inexistente). El thresholds-tier inicial puede ser irreal en el ambiente real — eso NO es bug del SUT; queda para `[[calidad-calibrate-k6-thresholds]]`.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (p. ej. ajuste de payload por schema-drift). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar `checks` para esconder respuestas 4xx/5xx reales, nunca eliminar `http_req_failed` ni `http_req_duration` de `options.thresholds` para forzar verde, nunca reducir `iterations` para esconder degradación.
5. **Smoke 1:1 gate obligatorio**: ejecutar `k6 run tests/linea-base/main.js --vus 1 --iterations 1` (o `tests/smoke/main.js` según vocabulario elegido). Ver [[calidad-k6-greenfield]] (consultar `references/smoke-1-1-gate.md`). Exit != 0 → `status: partial`, `blocker: "smoke_1_1_failed"`. Exit 0 → continuar al prompt del paso 6.
6. **Prompt explícito al usuario post-generación** (solo si smoke 1:1 OK):

   > "Smoke 1:1 validado [OK]. ¿Cómo procedemos con la suite completa?
   > (a) Ejecutar ahora `linea-base` -> `carga` -> `estres` con orquestación `run-all.sh`
   > (b) Solo dejar scaffold y ejecutar después manualmente
   > (c) Ejecutar solo `linea-base` (más rápido) y dejar el resto preparado"

7. Reportar estado final: `success` (smoke pasa) | `partial` (entregado scaffold, no se pudo ejecutar smoke o load/stress quedan fuera de scope del loop) | `failed` (escalado a humano con script, métricas medidas, threshold violado e hipótesis).
8. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`. Recordar al usuario que la calibración formal de thresholds y la ejecución de `load/stress/spike/soak` se hace con `[[calidad-calibrate-k6-thresholds]]` bajo ventana coordinada.

### Paso final — Reporte ejecutivo

Invocar `[[calidad-generate-executive-report]]` con `results_path`, `strategy_md_path` y `output_format` (preguntar al usuario o usar default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y se referencia en el `delivery_gate.evidence_persisted.executive_report`. Si modo es `scaffold-only` o `dry-run` → omitir este paso y registrar `null`.

## Criterios de finalización (DoD — 10 items)

1. Todos los imports usados (sin dead imports).
2. Todos los endpoints del spec cubiertos al menos por un script.
3. DELETE incluido en cada flujo CRUD detectado.
4. Credenciales y `baseUrl` provienen de `config.js`/`__ENV` (cero hardcoded en tests). En modo `external`, `AUTH_TOKEN` está documentada como obligatoria en el `README.md`.
5. `options.stages` y `options.thresholds` presentes en cada script emitido (los 3 obligatorios y los opt-in activados).
6. Cada `check()` valida campos del response (no solo el status code).
7. Flujos CRUD usan IDs dinámicos con guard clause (`[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)`).
8. Headers se construyen vía `getDefaultHeaders()` de `utils.js` (no inline).
9. Payloads se construyen vía `buildXxxBody()` de `utils.js` (no inline).
10. `handleSummary()` presente en cada script exportando JSON a `results/`.
11. `smoke-test.js` ejecutado al menos una vez. Estado: `success` / `partial` / `failed` reportado. `load/stress/spike/soak` quedan fuera del loop y se ejecutan via `[[calidad-calibrate-k6-thresholds]]`.
12. Si hubo fallos en el smoke: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
13. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados (no se relajaron `checks`, ni `http_req_failed`, ni `http_req_duration`).
14. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando `k6 run ...` + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
15. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
