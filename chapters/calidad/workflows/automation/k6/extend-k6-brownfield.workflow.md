---
id: extend-k6-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Workflow para extender un proyecto K6 existente (nuevos scripts/endpoints/thresholds) respetando convenciones detectadas y sin regenerar infraestructura.
tags: [k6, brownfield, workflow, performance, conventions]
---

# Extend K6 Brownfield — Workflow

## Cuándo usar

Cuando `[[calidad-route-test-generation]]` (paso 5) y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario brownfield K6: el `project_root` contiene mínimo `tests/config.js` + `tests/utils.js` + ≥1 `tests/*-test.js`. El skill subyacente es `[[k6-brownfield]]`.

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

### Paso 1 — Analizar proyecto existente

Inspecciona `project_root`. Verifica que cumple los criterios brownfield (`tests/config.js`, `tests/utils.js`, ≥1 `tests/*-test.js`). Anota qué scripts de los 5 canónicos (`smoke`, `load`, `stress`, `spike`, `soak`) están presentes y cuáles faltan.

### Paso 2 — Detectar convenciones

Aplica el algoritmo de `[[k6-convention-detection]]`. Consolida: `tests_dir`, `script_naming`, `groups_naming`, `auth_mode` actual, `existing_thresholds` (tier dominante), `existing_payload_builders`, `existing_id_correlation_pattern`, `handle_summary_path`, `import_style`, `env_vars_in_use`. Estos valores son el contrato para todo lo que se genere a continuación.

### Paso 3 — Determinar tipo de cambio

Mapea el `change_request` a uno o varios de los patrones de `[[k6-extension-patterns]]`:

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

Bajo ninguna circunstancia regenerar `handleSummary()` con un formato distinto al detectado. Si los scripts existentes exportan a `results/${timestamp}-summary.json` con un timestamp ISO específico, los scripts nuevos usan exactamente la misma función (idealmente copiada literal del primer script existente). Si el proyecto usa `vendor/k6-summary.js` (ver `[[k6-handle-summary-evidence]]` sección offline), los nuevos scripts también lo importan de ahí.

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

Detalle de comandos en `[[k6-run-and-suite]]`.

## Criterios de finalización

1. Ningún archivo de infraestructura modificado (`package.json`, `README.md`, `run-all.sh`, `.gitignore`) salvo lo explícitamente solicitado por el usuario.
2. Convenciones detectadas (`script_naming`, `groups_naming`, `auth_mode`, `existing_thresholds`, `existing_payload_builders`, `existing_id_correlation_pattern`, `handle_summary_path`, `import_style`) respetadas al 100%.
3. Los nuevos scripts pasan smoke test individual (verificable con el comando entregado en el paso 7). Si el usuario no puede correrlo localmente, al menos `k6 inspect tests/<nuevo-script>-test.js` debe correr sin errores de parseo.
4. Cada nuevo `check()` valida campos del response (no solo status code).
5. Flujos CRUD nuevos usan IDs dinámicos (`[[k6-crud-dynamic-id-correlation]]`); cero IDs hardcodeados, aun si scripts viejos los tuvieran.
6. `handleSummary()` preservado: ruta de salida, formato de timestamp y origen de `textSummary` (jslib remota o vendor local) idénticos a los del proyecto.
7. Si hubo migración a `auth_mode = external`, el usuario fue notificado de actualizar `README.md` y CI con `AUTH_TOKEN` como variable obligatoria.
8. Mensaje final al usuario enumera: (a) archivos nuevos, (b) patches a archivos existentes con path y resumen del cambio, (c) comando de ejecución, (d) cualquier acción manual pendiente.
