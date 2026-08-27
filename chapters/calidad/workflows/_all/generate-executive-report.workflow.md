---
id: calidad-generate-executive-report
version: 1.1.0
scope: chapter
type: workflow
chapter: calidad
description: "Workflow invocado al final de toda generación para producir el reporte ejecutivo post-corrida en formato HTML/PPTX/DOC desde los outputs técnicos."
tags: [executive-report, workflow, post-corrida, stakeholders]
---

# Workflow — Generar reporte ejecutivo post-corrida

## Cuándo usar

Como **último paso** de TODO workflow de generación del chapter (Karate / Playwright / K6 / Appium Serenity / Appium WebdriverIO / serenity-wdio, tanto greenfield como brownfield) cuando hubo ejecución real (`modo: full` o `execute-only`).

En `modo: scaffold-only` o `dry-run` se **omite** este workflow: no hay outputs técnicos que post-procesar. El `delivery_gate.evidence_persisted.executive_report` se reporta como `null` en esos modos, con `blocker: "execution_skipped"` documentado.

Este workflow encapsula la invocación del skill `[[calidad-executive-report-generator]]` y la persistencia del artefacto en `.evidence/`.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `results_path` | Sí | Ruta a `results/<stack>/` con corridas timestamp. |
| `strategy_md_path` | Recomendado | Ruta a `STRATEGY.md` para tabular SLAs declarados. Si no existe, el reporte se marca **parcial — sin SLAs**. |
| `output_format` | No | `html` (default) / `pptx` / `doc` / `md`. Preguntar al usuario si no se provee. |
| `framework` | Sí | `karate | playwright | k6 | appium-serenity | appium-wdio | serenity-wdio`. Determina la plantilla específica del stack. |

## Pasos

### Paso 1 — Resolver framework y leer outputs técnicos

Confirmar el `framework` recibido y localizar los outputs primarios según el Paso 1 del `[[calidad-executive-report-generator]]`. Si `results_path` no contiene carpetas timestamp válidas, abortar con `status: failed` y mensaje "sin corridas para reportar".

### Paso 2 — Leer STRATEGY.md para extraer SLAs

Buscar `strategy_md_path`. Si existe, extraer SLAs declarados, criterios de aceptación, umbrales de cobertura. Si no existe, marcar el reporte como **parcial** y omitir la sección 2 (Cumplimiento de SLAs).

### Paso 3 — Invocar el skill de generación

Invocar `[[calidad-executive-report-generator]]` con los inputs resueltos. El skill ejecuta sus 7 pasos internos (lectura, consolidación, comparación, clasificación, render, conversión) y retorna el path del archivo final.

### Paso 4 — Persistir reporte en `.evidence/`

Persistir el resultado en `.evidence/report-{ISO}.{ext}` donde:

- `{ISO}` es el timestamp ISO 8601 de la corrida principal (no de la generación del reporte).
- `{ext}` es la extensión derivada de `output_format` (`.html`, `.pptx`, `.docx`, `.md`).

Si `pandoc` no está disponible y se pidió formato distinto a `md`, emitir el `.md` y documentar el comando exacto de conversión manual en el mensaje al usuario.

### Paso 5 — Reportar al usuario

Mostrar al usuario:

- Path absoluto del reporte generado.
- Resumen del estado global (verde / amarillo / rojo) con una frase de justificación.
- Conteo de hallazgos por clasificación (`SUT_BUG`, `THRESHOLD_TOO_STRICT`, `ENVIRONMENT_BLOCKED`, `TEST_DESIGN_ISSUE`, `DATA_ISSUE`, `UNKNOWN`).
- Recordatorio de registrar el path en `delivery_gate.evidence_persisted.executive_report`.
- **Si `execution_target: mock | hybrid`**: el reporte DEBE llevar un banner visible en la portada/encabezado — *"Ejecutado contra mock ({tool}): valida la construcción de la suite, no certifica el SUT. Certificación pendiente de integraciones reales."* — y el mensaje al usuario lo repite. Sin este banner el reporte puede leerse como certificación, que es exactamente lo que la regla maestra de `[[calidad-sut-readiness-gate]]` prohíbe.

## Criterios de finalización (DoD)

- [ ] Reporte generado en `.evidence/report-{ISO}.{ext}` (no `null`).
- [ ] Sección "Cumplimiento de SLAs" tabulada (o explícitamente omitida si no había `STRATEGY.md`).
- [ ] Todos los fallos determinísticos clasificados con evidencia (sin clasificaciones vacías; `UNKNOWN` aceptable solo si la evidencia es insuficiente).
- [ ] Sección "Recomendaciones por rol" presente con al menos una acción por rol con hallazgos asociados, o nota "sin acciones para <rol>".
- [ ] Path del reporte registrado en `delivery_gate.evidence_persisted.executive_report`.
- [ ] Si `modo` es `scaffold-only` o `dry-run`, este workflow se omite y `delivery_gate.evidence_persisted.executive_report = null` con `blocker: "execution_skipped"`.
- [ ] Si `execution_target: mock | hybrid`: banner de "no certifica el SUT" presente en el reporte y repetido en el mensaje de cierre.

## Cross-links

- `[[calidad-executive-report-generator]]` — skill que ejecuta los 7 pasos internos.
- `[[calidad-failure-triage-and-classification]]` — catálogo de patrones para clasificar fallos.
- `[[calidad-delivery-gate-contract]]` — schema YAML donde se registra el path del reporte.
- `[[calidad-test-evidence-and-traceability]]` — política de persistencia en `.evidence/`.
- `[[calidad-post-generation-protocol]]` — protocolo del que este workflow es la última fase.
