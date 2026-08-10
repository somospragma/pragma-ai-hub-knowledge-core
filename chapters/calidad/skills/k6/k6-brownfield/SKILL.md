---
id: calidad-k6-brownfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [k6]
description: Extiende un proyecto K6 existente con nuevos scripts/endpoints/thresholds respetando convenciones detectadas.
tags: [k6, brownfield, performance, conventions]
---

# K6 Brownfield

## Cuándo aplicar

Cuando el usuario tiene un **proyecto K6 ya inicializado** (mínimo `tests/config.js` + `tests/utils.js` + al menos un `tests/*-test.js`) y solicita extenderlo. Casos típicos:

- Añadir nuevos endpoints / scripts (p. ej. un `spike-test` adicional, un flujo de checkout dedicado).
- Recalibrar `thresholds` tras observar comportamiento real (`[[calidad-calibrate-k6-thresholds]]`).
- Refactor por nueva versión del spec (endpoints renombrados, campos añadidos).
- Introducir `auth_mode = external` en un proyecto que originalmente fue generado en modo `spec` (típicamente cuando aparece un API gateway o IdP nuevo en el path).

La decisión brownfield vs greenfield se toma en `[[calidad-brownfield-vs-greenfield]]`. Si el usuario no provee archivos del proyecto, no asumas: solicítalos o usa `[[calidad-k6-greenfield]]` previo acuerdo.

## Lectura obligatoria antes de tocar el proyecto

El conocimiento técnico del stack vive en el bundle **greenfield** del mismo stack; brownfield no lo duplica, lo consume. **Abrir antes de generar** y declarar cuáles se leyeron (traza en `[[calidad-pipeline-state-tracking]]`):

| Reference | Para qué |
|---|---|
| [[calidad-k6-greenfield]] (`references/thresholds-three-tiers.md`) | Tiers de thresholds y justificación |
| [[calidad-k6-greenfield]] (`references/crud-dynamic-id-correlation.md`) | Correlación de IDs |
| [[calidad-k6-greenfield]] (`references/handle-summary-evidence.md`) | handleSummary y evidencia |
| `references/convention-detection.md` · `references/extension-patterns.md` | Convenciones del proyecto (propias de este skill) |

**Cómo se aplica en brownfield**: estas references aportan el **conocimiento técnico** (cómo resolver un locator, cómo interactuar, cómo diagnosticar). Las **convenciones del proyecto del cliente siempre mandan** sobre las del chapter (naming, tags, idioma, estilo, versiones). Nunca se importan las convenciones del greenfield a un proyecto existente.

**Diagnóstico sin imposición**: si al analizar el proyecto detectas un defecto conocido del chapter (p. ej. `OnlineCast` disparando ChromeDriver, runner con tags hardcodeados que anulan el filtro de CLI, falta de `SerenityReporter` en `cucumber.plugin`, imports legacy de Serenity 3.x), **repórtalo al usuario con su evidencia y el fix sugerido — no lo apliques por tu cuenta**. Corregirlo sin permiso viola la regla de no tocar infraestructura ajena; callarlo deja al cliente con un falso verde que ya conocemos.

## Instrucción

1. **Recolectar inputs adicionales** — Además de los gobernados por `[[calidad-mandatory-inputs-protocol]]`, exige: `project_root` (ruta del proyecto K6 existente), `scripts_to_extend` (lista de scripts a modificar, vacía si todos los cambios son archivos nuevos), `new_endpoints_or_thresholds` (descripción libre del delta a aplicar). Si falta cualquier obligatorio, detente y solicítalo.
2. **Analizar proyecto existente** — Aplica el algoritmo de ``references/convention-detection.md``. Inspecciona estructura (`tests/`, `results/`, infra), el contenido actual de `config.js` y `utils.js`, scripts presentes (cuáles de los 5 tipos existen y cuáles faltan), naming convention de `group()` / `check()` (idioma, prefijos), patrón de IDs dinámicos y ruta de `handleSummary` (`results/` vs `reports/`).
3. **Detectar `auth_mode` actual** — Lee `tests/config.js` y `tests/utils.js`. Si `authToken` está definido y `Authorization` se emite en `getDefaultHeaders()`, el modo es `external` o `spec` con security; mira si el spec original declaraba security para distinguir. Si el usuario solicita migrar de `spec` a `external`, genera el patch explícito de `config.js`/`utils.js` (ver ``references/extension-patterns.md``).
4. **Generar SOLO scripts nuevos o modificaciones a existentes** — Cero archivos de infraestructura. Si un script existente se modifica, entrega el diff explícito (no la regeneración completa) salvo que el cambio supere ~60% del archivo, en lo que se reemplaza el archivo entero documentando el motivo.
5. **Reutilizar `utils.js` / `config.js`** — No regenerar. Si requieres un nuevo `buildXxxBody()` o un nuevo enum, entrégalo como patch incremental (`+ function buildXxx ...`) que respete el estilo detectado. IDs dinámicos en flujos CRUD se manejan con el patrón `[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)` ya presente en el proyecto.
6. **Validar checklist** — Recorre los criterios de finalización del workflow `[[calidad-extend-k6-brownfield]]` (ningún archivo de infra modificado salvo pedido explícito, convenciones detectadas al 100%, nuevos scripts pasan smoke test individual). Encadena trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

## Salidas

- Cero o más `tests/*-test.js` nuevos en el `tests_dir` detectado.
- Cero o más **patches** explícitos sobre `tests/config.js`, `tests/utils.js` o sobre scripts existentes. Cada patch se entrega como diff legible (líneas `+`/`-`) y nombra el archivo destino con su path absoluto/relativo al `project_root`.
- Nunca `package.json`, `README.md`, `run-all.sh`, `.gitignore`, ni archivos fuera de `tests/`. Si una modificación requiere tocar infra, repórtalo al usuario y espera autorización antes de tocarlo.

## Restricciones

- **NUNCA** regenerar `package.json`, `README.md`, `run-all.sh`, `.gitignore` ni cualquier archivo de infraestructura del proyecto existente.
- **Respetar 100%** las convenciones detectadas (`script_naming`, `groups_naming`, `auth_mode`, `existing_thresholds`, `existing_payload_builders`, `handle_summary_path`). No "mejorar" estilo si difiere del proyecto.
- **Preservar `handleSummary()` existente**: si el proyecto exporta a `results/` o `reports/` con un formato específico de timestamp o filename, los nuevos scripts deben usar exactamente la misma función (idealmente importada o copiada literal).
- Flujos CRUD nuevos deben usar IDs dinámicos siguiendo `[[calidad-k6-greenfield]] (consultar `references/crud-dynamic-id-correlation.md` en su subfolder)` y reutilizar el patrón de captura ya presente (extracción del `id` del response del POST con guard clause). No hardcodees IDs aunque otros scripts viejos lo hagan.
- Si las convenciones detectadas están en conflicto interno (p. ej. dos estilos de naming en distintos scripts), **pregunta al usuario** cuál adoptar; no decidas tú.
- Entrega con `[[calidad-streaming-files-protocol]]`. Trazabilidad por `[[calidad-test-evidence-and-traceability]]`.
