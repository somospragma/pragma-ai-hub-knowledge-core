---
id: calidad-pre-generation-protocol
version: 1.1.0
scope: chapter
type: steering
chapter: calidad
description: "Protocolo obligatorio que el agente DEBE ejecutar antes de emitir cualquier archivo en cualquier workflow del chapter. Aplica a los 5 IDEs."
tags: [protocol, mandatory, pre-flight, mandatory-inputs, modo, enforcement]
---

# Pre-Generation Protocol — Disciplina Obligatoria Antes del Primer Archivo

## Rol

Antes de generar el primer archivo de cualquier proyecto de pruebas, ejecutar este protocolo en orden. Saltarse cualquier paso = entrega inválida.

Aplica a los 5 IDEs soportados (Kiro, Claude Code, GitHub Copilot, Amazon Q IDE, Amazon Q CLI) y a los 4 frameworks del chapter (Karate, Playwright, K6, Appium), tanto en greenfield como en brownfield.

## Pasos del protocolo

0. **Leer la traza del pipeline** — Si el `output_path` ya existe, leer `.evidence/pipeline-state.json` (`[[calidad-pipeline-state-tracking]]`) y reportar dónde quedó el proceso antes de hacer nada. Si no existe, crearlo. Continuar por su `next_action`, no por lo que parezca urgente.

1. **Confirmar mandatory inputs** (todos obligatorios, no se asume ninguno) y **leer COMPLETO cada insumo entregado**, emitiendo la tabla de extracción (qué se extrajo de cada uno y dónde se usará — `[[calidad-mandatory-inputs-protocol]]`). Un insumo sin fila es un insumo ignorado:
   - `intent`: qué tipo de pruebas (Karate / Playwright / K6 / Appium)
   - `project_name`: kebab-case
   - `output_path`: ruta absoluta
   - `ui_source` (Playwright) / `spec` (Karate/K6) / `apk_path` (Appium): fuente principal
   - **`modo` de operación**: `full | dry-run | scaffold-only | execute-only`
   - `user_story`: HUT-XXX o `null` (declarar explícitamente)
   - `firma`: documento de servicio o `null`
   - `risk_map`: por endpoint/HU/script `{nombre: CRITICAL|HIGH|MEDIUM|LOW}`; si no se provee, default `HIGH` con confirmación
   - Para K6, además de los inputs base, completar el checklist K6-específico (perfil de carga, dependencias externas, disponibilidad objetivo, data de prueba, endpoint objetivo vs auxiliares, volumen esperado, restricciones de ambiente) según `[[calidad-mandatory-inputs-protocol]]`

2. **Ejecutar pre-flight check del stack** invocando la reference correspondiente:
   - Karate → [[calidad-karate-greenfield]] (consultar `references/preflight.md` en su subfolder)
   - Playwright → `references/preflight.md` análogo
   - K6 → análogo
   - Appium → análogo

   Si pre-flight falla → reportar al usuario y **degradar a `scaffold-only`** con razón documentada. No continuar a generación full.

3. **Declarar coverage upfront** antes de generar:
   - Karate: por endpoint, calcular `effective_minimum` con fórmula `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)` y mostrar al usuario `{endpoint: N}`.
   - Playwright: por HU, calcular `effective_minimum = happy + 2_boundary + 2_negative + 1_edge ≈ 8` mínimo.
   - K6: los 3 escenarios Línea Base / Carga / Estrés (Smoke / Load / Stress en docs k6) son obligatorios. Spike y Soak son opt-in con justificación documentada en `.evidence/scenarios-opt-in.md` (ver [[calidad-k6-greenfield]] (consultar `references/vocabulary-and-scenario-mapping.md`)). Declarar también tier (Conservative/Moderate/Relaxed) con razón.
   - Appium: número de escenarios `@smoke` ejecutables + escenarios `@proposed` planeados.

4. **Generar `STRATEGY.md` y esperar aprobación del usuario antes de proceder a templates.** Aplicar `[[calidad-pre-design-strategy-document]]`. El documento se materializa en `output_path/STRATEGY.md` usando el `STRATEGY.md` del stack correspondiente (Karate / Playwright / K6 / Appium). El agente lo presenta, itera ante "modificar X" y SOLO avanza al paso 5 al recibir "aprobado" (o equivalente explícito). NUNCA se emite código antes de esta aprobación.

5. **Esperar confirmación EXPLÍCITA del usuario** ("procede" o equivalente) antes de emitir el primer archivo de código (separada de la aprobación del STRATEGY.md).

## Restricciones

- NUNCA emitir el primer archivo sin que los 5 pasos se hayan completado.
- NUNCA emitir código sin `STRATEGY.md` aprobado explícitamente (regla anti-cheating del paso 4).
- NUNCA asumir `modo: full` por defecto — preguntar.
- NUNCA asumir `risk: HIGH` sin confirmar — preguntar.
- Si el IDE no permite preguntas interactivas (modo batch), generar `STRATEGY.md` propuesto + `scaffold-only` con `.evidence/missing-inputs.md` y `.evidence/strategy-approval.md` documentando los faltantes y el bloqueo a aprobación humana asíncrona.

## Cross-links

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-pre-design-strategy-document]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`, `[[calidad-business-driven-prioritization]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-generate-executive-report]]`.
