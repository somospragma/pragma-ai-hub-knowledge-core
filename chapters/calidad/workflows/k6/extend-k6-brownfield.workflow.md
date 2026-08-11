---
id: calidad-extend-k6-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [k6]
description: Workflow para extender un proyecto K6 existente (nuevos scripts/endpoints/thresholds) respetando convenciones detectadas y sin regenerar infraestructura.
tags: [k6, brownfield, workflow, performance, conventions]
---

# Extend K6 Brownfield — Workflow

## Cuándo usar

Cuando `[[calidad-route-test-generation]]` (paso 5) y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario brownfield K6: el `project_root` contiene mínimo `tests/config.js` + `tests/utils.js` + ≥1 `tests/*-test.js`. El skill subyacente es `[[calidad-k6-brownfield]]`.

### Pre-flight (OBLIGATORIO)

Antes de cualquier acción, ejecutar [[calidad-k6-greenfield]] (consultar `references/preflight.md` en su subfolder) del stack. En brownfield aplica los mismos checks de versión/tooling. Si falla → degradar a `scaffold-only` con razón documentada.

Cumplir el protocolo `[[calidad-pre-generation-protocol]]` incluso en brownfield: confirmar inputs (incluido `modo`), declarar coverage de los archivos NUEVOS (no de los preexistentes), esperar confirmación del usuario.

### Regla brownfield específica — Auto-corrección

La auto-corrección y self-healing aplican EXCLUSIVAMENTE a los archivos NUEVOS que este workflow genera. Los archivos preexistentes del cliente (tests, Page Objects, fixtures, configs) son INTOCABLES bajo ningún concepto, aunque fallen. Si tests preexistentes fallan en la ejecución:

1. Reportar el fallo al usuario con triage (deterministic vs flaky).
2. NUNCA modificar el test preexistente.
3. NUNCA modificar fixtures, data o configs preexistentes para hacer pasar tests.
4. Escalar a humano con el contexto completo del fallo.

Esta regla es non-negotiable y es enforcement obligatorio del `[[calidad-test-self-correction-loop]]` y sus `references/anti-cheating-guardrails.md`.

Refuerzos adicionales:
- **Step isolation** (ver `[[calidad-step-isolation-pattern]]`) aplica a los `group()` / `check()` de los scripts NUEVOS. Los scripts preexistentes mantienen su estructura aunque no cumplan el patrón; no se les aplica refactor.
- **Validación contractual no superficial** según [[calidad-k6-greenfield]] (consultar `references/contractual-checks-from-user-story.md`) aplica solo a scripts/escenarios nuevos. NO re-escribir checks preexistentes.

### Paso previo — Análisis condicional con STRATEGY.md

Si el alcance del brownfield es **grande** (≥3 endpoints/escenarios nuevos, o cambios cross-cutting que afectan multiple scripts preexistentes, o migración de `auth_mode`): generar `STRATEGY.md` según el template [[calidad-k6-greenfield]] (template en ``references/templates.md` (sección `STRATEGY.md`)`) y el skill `[[calidad-pre-design-strategy-document]]`. Esperar aprobación del usuario antes de continuar.

Si el alcance es **pequeño** (1-2 cambios puntuales, p. ej. añadir un endpoint o recalibrar un threshold): omitir STRATEGY.md y proceder directo a generación, documentando la decisión en `.evidence/scope-decision.md`.

Respetar convenciones del proyecto cliente: el STRATEGY del brownfield documenta lo NUEVO, no rediseña lo existente. Respetar nomenclatura existente (smoke/load/stress/spike/soak vs línea-base/carga/estrés/pico/resistencia): si el proyecto cliente usa una, NO renombrar a la otra.

Transfiere control aquí cuando el usuario pide:

- Agregar endpoints / scripts a la suite K6 existente.
- Recalibrar thresholds tras observar comportamiento real.
- Refactor por nueva versión del spec.
- Migrar `auth_mode` (típicamente `spec` → `external`).
- Cualquier otra extensión que no implique regenerar infra (`package.json`, `README.md`, `run-all.sh`, `.gitignore`).

## Inputs

Gobernados por `[[calidad-mandatory-inputs-protocol]]`:

| Input | Obligatorio | Notas |
|---|---|---|
| `project_root` | Sí | Ruta del proyecto K6 existente. Debe contener `tests/config.js` + `tests/utils.js` + ≥1 `tests/*-test.js`. |
| `change_request` | Sí | Texto libre describiendo el delta (p. ej. "añadir endpoint `POST /orders` al load-test y crear spike-test"). |
| `spec_addendum` | No | Fragmento de OpenAPI/Swagger con los nuevos endpoints o cambios. Si la modificación es puramente de thresholds o `auth_mode`, puede omitirse. |
| `new_thresholds` | No | Tier o valores explícitos a aplicar (`Conservative` / `Moderate` / `Relaxed`, o map de métricas → umbrales). |
| `user_story` | No (recomendado) | Para trazar el cambio con `@user-story:<ID>`. |

Si falta cualquier obligatorio, detente y solicítalo.

## Pasos

### Paso 0 — Leer la traza del pipeline (SIEMPRE)

Aplica `[[calidad-pipeline-state-tracking]]` antes de tocar nada: si el `project_root`/`output_path` ya tiene `.evidence/pipeline-state.json`, leerlo y abrir el turno reportando fase actual, pendientes, bloqueos y `open_corrections`. Si no existe, crearlo con las fases de la ruta brownfield en `pending`. Actualizarlo al cerrar cada fase, con evidencia.

En brownfield el riesgo de perder el hilo es MAYOR que en greenfield: son sesiones largas sobre proyectos grandes del cliente, que es justo donde el contexto se llena y el proceso se fragmenta.


### Paso 1 — Analizar proyecto existente

Inspecciona `project_root`. Verifica que cumple los criterios brownfield (`tests/config.js`, `tests/utils.js`, ≥1 `tests/*-test.js`). Anota qué scripts de los 5 canónicos (`smoke`, `load`, `stress`, `spike`, `soak`) están presentes y cuáles faltan.

### Paso 2 — Detectar convenciones

Aplica el algoritmo de [[calidad-k6-brownfield]] (consultar `references/convention-detection.md` en su subfolder). Consolida: `tests_dir`, `script_naming`, `groups_naming`, `auth_mode` actual, `existing_thresholds` (tier dominante), `existing_payload_builders`, `existing_id_correlation_pattern`, `handle_summary_path`, `import_style`, `env_vars_in_use`. Estos valores son el contrato para todo lo que se genere a continuación.

### Paso 3 — Determinar tipo de cambio

Mapea el `change_request` a uno o varios de los patrones de [[calidad-k6-brownfield]] (consultar `references/extension-patterns.md` en su subfolder):

- Añadir endpoint a script existente → patch.
- Crear nuevo script → archivo nuevo.
- Añadir threshold a script existente → patch en `options.thresholds`.
- Cambiar tier → patch en los 5 scripts.
- Agregar CRUD flow → archivo / patch + nuevos `buildXxxBody()` como patch en `utils.js`.
- Migrar `auth_mode = spec` a `external` → patches en `config.js` y `utils.js` + nota al usuario sobre `AUTH_TOKEN` obligatoria.

Si el cambio mezcla varios patrones, planifica el orden de emisión (tests primero, patches a `utils.js`/`config.js` después).

### Paso 4 — Generar / modificar archivos mínimos

Aplica `[[calidad-streaming-files-protocol]]`:

1. Primero los `tests/*-test.js` nuevos o los patches a los existentes.
2. Después los patches a `tests/utils.js` (nuevos `buildXxxBody()`, nuevos imports) y `tests/config.js` (nuevos enums, `authToken` si migración).
3. Cero archivos fuera de `tests/`. Si la modificación requiere tocar `package.json`, `README.md`, `run-all.sh` o `.gitignore`, **detente, reporta el motivo y espera autorización explícita**.

Cada modificación a un archivo existente se entrega como **diff legible** (líneas `+`/`-`) con el path destino claramente identificado, salvo que el cambio reemplace >60% del archivo.

### Paso 5 — Preservar `handleSummary()`

Bajo ninguna circunstancia regenerar `handleSummary()` con un formato distinto al detectado. Si los scripts existentes exportan a `results/${timestamp}-summary.json` con un timestamp ISO específico, los scripts nuevos usan exactamente la misma función (idealmente copiada literal del primer script existente). Si el proyecto usa `vendor/k6-summary.js` (ver [[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder) sección offline), los nuevos scripts también lo importan de ahí.

### Paso 6 — Validar checklist

Recorre `## Criterios de finalización`. Si algún ítem falla, regenera el archivo correspondiente antes de cerrar. Registra trazabilidad con `[[calidad-test-evidence-and-traceability]]` (cada test nuevo debe llevar al menos un tag `@user-story:<ID>` o `@requirement:<ID>` si el proyecto usa tags; si no, dejarlo documentado en el `group()` raíz).

### Paso 7 — Comando run para verificación rápida

Entrega al usuario el comando exacto para correr **solo** los scripts nuevos o modificados (smoke individual), aprovechando las convenciones del proyecto:

```bash
# Smoke individual del script nuevo
k6 run -e BASE_URL=$BASE_URL tests/<nuevo-script>-test.js

# Si auth_mode = external, además AUTH_TOKEN:
k6 run -e BASE_URL=$BASE_URL -e AUTH_TOKEN=$AUTH_TOKEN tests/<nuevo-script>-test.js
```

Detalle de comandos en `[[calidad-k6-run-and-suite]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** En K6 brownfield, esta fase usa **únicamente smoke individual del/los script(s) nuevo(s) o modificado(s)**: `load/stress/spike/soak` quedan fuera del loop. Además, la auto-corrección aplica **EXCLUSIVAMENTE** a los scripts/patches generados por este workflow; NUNCA a los scripts preexistentes del cliente, aunque fallen (ver `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

**Cadencia de corrección (aplica a los tests nuevos de esta corrida)**: gate de un escenario → suite de los tests nuevos como inventario → **corrección aislada, re-ejecutando SOLO el test que se corrige** → regresión de los nuevos. Nunca relanzar la suite en cada iteración. Detalle en `[[calidad-test-self-correction-loop]]`. La suite preexistente del cliente no entra en este ciclo.


1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin `k6`, sin red al `BASE_URL`, sin `AUTH_TOKEN` cuando aplique), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` sólo el smoke individual del nuevo script (`k6 run -e BASE_URL=$BASE_URL tests/<nuevo-script>-test.js`). Si el cambio fue patch a `utils.js`/`config.js`, correr el smoke del primer script afectado. Capturar `results/${timestamp}-summary.json`.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky. Causas típicas: payload mal correlacionado con el nuevo endpoint, header faltante, `AUTH_TOKEN` mal seteado, threshold heredado irreal para el nuevo flujo. Fallos de scripts preexistentes del cliente por daño colateral del patch: detenerse y reportar, NO auto-corregir el legado.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar `checks`, `http_req_failed` ni `http_req_duration`; las correcciones deben respetar las convenciones detectadas (`script_naming`, `groups_naming`, `auth_mode`, `existing_thresholds`, `handle_summary_path`).
5. Reportar estado final: `success` | `partial` | `failed` con script, métricas, threshold violado e hipótesis cuando se escala.
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. Recordar que la calibración formal de thresholds para el nuevo flujo se hace via `[[calidad-calibrate-k6-thresholds]]`.
7. **Invocar `[[calidad-post-generation-protocol]]`** para coherence checks post-emisión (find paths `tests/*.js`, grep `handleSummary` en scripts nuevos, `k6 inspect tests/<nuevo-script>-test.js` validación de sintaxis) antes de cerrar.
8. **Smoke gate universal (scripts nuevos)**: antes de declarar `success`, ejecutar el smoke gate del stack según [[calidad-smoke-gate-policy]]. En brownfield K6, el gate ejecuta **únicamente smoke individual de los scripts/escenarios nuevos** con la mínima carga: `k6 run tests/<nuevo-script>-test.js --vus 1 --iterations 1` (o `-e BASE_URL=...` y `AUTH_TOKEN` cuando aplique). Bajo NINGÚN concepto re-ejecutar `load/stress/spike/soak` preexistentes en el gate (esos tienen otro propósito y duración). Si la nomenclatura del proyecto cliente usa línea-base en vez de smoke, aplicar el equivalente local manteniendo carga mínima. Si fallan scripts preexistentes al correr la suite completa después, eso NO bloquea la entrega — se reporta como issue separado.
9. **Evidencia de bloqueo de ambiente**: si la ejecución sufre bloqueo de ambiente (WAF/network/auth/rate limit/throughput cap), emitir `.evidence/execution-status.json` según [[calidad-environment-blocker-evidence]]. El estado pasa a `partial` con razón.
10. **Metadata por corrida**: emitir `results/k6/{date}/{ISO}-metadata.json` según el schema universal [[calidad-execution-metadata-schema]]. En brownfield, el campo `workload_or_scope` debe distinguir "N scripts/escenarios nuevos sobre M preexistentes" e incluir VUs/iterations efectivos.
11. **Reporte ejecutivo**: invocar `[[calidad-generate-executive-report]]` para producir reporte consolidado en `.evidence/report-{ISO}.{html|pptx|docx|md}`, usando `k6-report-template.md`. El reporte debe segregar explícitamente "scripts nuevos (en scope de esta sesión)" de "scripts preexistentes (referencia, no ejecutados en el gate)" e incluir comparación corrida nueva vs baseline preexistente si los `results/*-summary.json` previos están disponibles.
12. **Emitir el bloque `delivery_gate` yaml** según `[[calidad-delivery-gate-contract]]` — **precondición: leer `.evidence/pipeline-state.json` y verificar cero fases obligatorias pendientes; con pendientes NO se emite el gate, se emite reporte de estado y el trabajo continúa** — con: status declarado coherente con execution, manifest de archivos nuevos/patches, evidencia (`.evidence/session-config.json`, `.evidence/generation-manifest.json`, `results/${timestamp}-summary.json` si modo=full, `.evidence/execution-status.json` si hubo bloqueo de ambiente, metadata por corrida, reporte ejecutivo, audit log si hubo correcciones), blockers (fallos en scripts preexistentes del cliente reportados como blocker con status `partial`, jamás auto-corregidos).

## Criterios de finalización

1. Ningún archivo de infraestructura modificado (`package.json`, `README.md`, `run-all.sh`, `.gitignore`) salvo lo explícitamente solicitado por el usuario.
2. Convenciones detectadas (`script_naming`, `groups_naming`, `auth_mode`, `existing_thresholds`, `existing_payload_builders`, `existing_id_correlation_pattern`, `handle_summary_path`, `import_style`) respetadas al 100%.
3. Los nuevos scripts pasan smoke test individual (verificable con el comando entregado en el paso 7). Si el usuario no puede correrlo localmente, al menos `k6 inspect tests/<nuevo-script>-test.js` debe correr sin errores de parseo.
4. Cada nuevo `check()` valida campos del response (no solo status code).
5. Flujos CRUD nuevos usan IDs dinámicos ([[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)); cero IDs hardcodeados, aun si scripts viejos los tuvieran.
6. `handleSummary()` preservado: ruta de salida, formato de timestamp y origen de `textSummary` (jslib remota o vendor local) idénticos a los del proyecto.
7. Si hubo migración a `auth_mode = external`, el usuario fue notificado de actualizar `README.md` y CI con `AUTH_TOKEN` como variable obligatoria.
8. Mensaje final al usuario enumera: (a) archivos nuevos, (b) patches a archivos existentes con path y resumen del cambio, (c) comando de ejecución, (d) cualquier acción manual pendiente.
9. Smoke del/los script(s) nuevo(s) ejecutado al menos una vez. Estado: `success` / `partial` / `failed` reportado.
10. Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada. Fallos de scripts preexistentes del cliente reportados al humano, NO auto-corregidos.
11. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Auto-corrección sólo tocó scripts/patches generados por este workflow.
12. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
13. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
