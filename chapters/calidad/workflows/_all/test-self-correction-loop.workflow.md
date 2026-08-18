---
id: calidad-test-self-correction-loop-workflow
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
description: "Workflow estándar invocado por todos los workflows de construcción de tests para ejecutar, triar y auto-corregir tests hasta validar."
tags: [self-correction, workflow, execute, triage, fix, validate]
---

# Test Self-Correction Loop — Workflow Estándar de Ejecución, Triage y Auto-Corrección

## Cuándo usar

Invocado como **fase final obligatoria** de todo workflow de generación o extensión de tests del chapter. No es opcional.

Workflows que deben encadenar este workflow al cierre:

- `[[calidad-generate-karate-greenfield]]`
- `[[calidad-extend-karate-brownfield]]`
- `[[calidad-generate-playwright-greenfield]]`
- `[[calidad-update-playwright-brownfield]]`
- `[[calidad-playwright-from-live-app]]`
- `[[calidad-generate-k6-suite]]`
- `[[calidad-extend-k6-brownfield]]`
- `[[calidad-calibrate-k6-thresholds]]`
- `[[calidad-generate-appium-screenplay-android]]`
- `[[calidad-complete-deferred-locators]]`
- `[[calidad-extend-appium-brownfield]]`
- `[[generate-serenity-wdio-greenfield]]`
- `[[extend-serenity-wdio-brownfield]]`

El workflow rector `[[calidad-route-test-generation]]` lo encadena automáticamente como paso terminal.

## Inputs

Obligatorios:

- `tests_path`: ruta al proyecto de tests recién generado/modificado.
- `framework`: `karate` | `playwright` | `k6` | `appium` | `serenity-wdio`.
- `mode`: `full` | `dry-run` | `scaffold-only` | `execute-only`.
- `client_regulated` (boolean): si `true`, fuerza modo `dry-run` (ver `references/regulated-client-overrides.md` del skill).

Opcionales:

- `max_iterations` (default 3).
- `sut_context`: URL del SUT, commit hash, environment.
- `evidence_root`: ruta donde persistir audit log y trazas; default según `[[calidad-test-evidence-and-traceability]]`.

## Pasos

### Paso 1 — Resolver modo efectivo

- Si `client_regulated == true` → forzar `mode = dry-run` (sin importar el input).
- Si capacidad técnica del agente lo impide (sin shell, sin env, sin acceso al SUT) → degradar a `scaffold-only` y registrar la razón en el reporte final.
- Confirmar inputs ambiguos vía `[[calidad-mandatory-inputs-protocol]]`.

### Paso 2 — Salir temprano si `scaffold-only`

- Reportar al humano los comandos de ejecución del framework correspondiente (`mvn test`, `npx playwright test`, `k6 run`, `./gradlew test`).
- Estado final: `partial`.
- Salir.

### Paso 3 — Ejecutar tests

Invocar `[[calidad-test-execution-orchestration]]` con el `mode` resuelto.

- Capturar stdout + stderr + exit code + artefactos (reports HTML, JSON summaries, screenshots, traces, videos).
- Parsear output al esquema común definido por el skill de orchestration.

### Paso 4 — Decidir según resultado

- Si **todo pasa** → estado `success`, generar evidencia con `correction_count: 0`, salir.
- Si **hay fallos** → continuar al paso 5.

### Paso 5 — Triage por cada fallo

Por cada test fallido, invocar `[[calidad-failure-triage-and-classification]]`:

- Recolectar evidencia mínima (test_id, error, stack, trace/screenshot, env context).
- Aplicar protocolo de re-run para determinismo.
- Clasificar el patrón contra `failure-pattern-catalog.md`.
- Calcular stability score.
- Decidir si habilita auto-corrección, healing, escalation o quarantine.

### Paso 6 — Auto-corrección por cada fallo elegible

Por cada fallo cuya clasificación habilita auto-corrección, aplicar `[[calidad-test-self-correction-loop]]`:

- Ejecutar la state machine completa (PRISTINE → EXECUTED → FAILED → DIAGNOSING → guardrails → FIXING → RE-EXECUTING → VALIDATED/ESCALATED).
- Respetar `max_iterations`.
- Registrar cada iteración en el audit log.

### Paso 7 — Manejo del modo `dry-run`

Si el modo efectivo es `dry-run`:

- **No aplicar** ninguna corrección, ni siquiera las que pasaron guardrails.
- Producir, por cada propuesta: patch + justificación + evidencia.
- Entregar el conjunto al humano para aprobación individual.
- Estado: `partial` (espera aprobación humana).

### Paso 8 — Aplicación en modo `full`

Si el modo efectivo es `full`:

- Aplicar las correcciones que pasaron guardrails, hasta `max_iterations` por test.
- Logear cada cambio en el audit log con formato canónico.
- Después de cada cambio, re-ejecutar **SOLO el test corregido**, aislado por nombre o tag (nunca la suite completa: eso es inventario al inicio y regresión al final — ver la cadencia en `[[calidad-test-self-correction-loop]]`).

### Paso 9 — Re-ejecución y bucle

- Repetir desde el paso 4 con el subconjunto afectado, hasta:
  - Todos los tests `VALIDATED`, o
  - Algún test alcanza `ESCALATED` (max_iterations, guardrail violado, oscilación detectada, etc.).

### Paso 10 — Reporte final

Generar reporte estructurado con:

- Tests pasados, fallidos, escalados, en quarantine.
- Correcciones aplicadas (con link al audit log) y propuestas (en `dry-run`).
- Evidencia archivada (paths absolutos).
- Tickets generados (quarantine con SLA, bugs reportados al cliente).
- Estado global: `success` | `partial` | `failed`.
- Recomendación de siguiente paso (entregar, iterar, escalar a humano).

## Criterios de finalización

- [ ] Reporte de ejecución generado con estado explícito `success | partial | failed`.
- [ ] Si hubo correcciones aplicadas: audit log persistido junto con evidence, formato canónico.
- [ ] Si hubo escalations: contexto completo (clasificación, evidencia, hipótesis, recomendación) entregado al humano; nunca "half-context".
- [ ] Si modo es `dry-run` y se proponen correcciones: patch + justificación + evidencia entregados, sin aplicar.
- [ ] Tags de trazabilidad (`@user-story:<ID>`, `@requirement:<ID>`) preservados en cualquier test modificado.
- [ ] Guardrails anti-cheating evaluados sin violación silenciosa: cualquier bloqueo aparece explícito en el reporte.
- [ ] Si modo degradado a `scaffold-only` por capacidad técnica: la razón está documentada.
- [ ] Si cliente regulado: modo forzado a `dry-run`, audit log con retención y separación de roles según `references/regulated-client-overrides.md` del skill.
