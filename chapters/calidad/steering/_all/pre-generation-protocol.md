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

Aplica a los 5 IDEs soportados (Kiro, Claude Code, GitHub Copilot, Amazon Q IDE, Amazon Q CLI) y a los 5 frameworks del chapter (Karate, Playwright, K6, Appium, serenity-wdio), tanto en greenfield como en brownfield.

## Pasos del protocolo

0. **Leer la traza del pipeline y la bitácora** — Si el `output_path` ya existe, leer `.evidence/pipeline-state.json` y `.evidence/session-log.md` (`[[calidad-pipeline-state-tracking]]`) y ejecutar el ritual de apertura antes de tocar nada: fase actual, siguiente acción, bloqueos y `open_corrections` reafirmadas. Si no existen, crearlos. Continuar por su `next_action`, no por lo que parezca urgente.

1. **Confirmar mandatory inputs** (todos obligatorios, ninguno se asume) y **leer COMPLETO cada insumo entregado**, emitiendo la tabla de extracción: qué se extrajo de cada uno y dónde se usará (`[[calidad-mandatory-inputs-protocol]]`). **Un insumo sin fila es un insumo ignorado.** Como mínimo: `intent` (Karate / Playwright / K6 / Appium Serenity / Appium WebdriverIO / serenity-wdio), `project_name` en kebab-case, `output_path` absoluto, la fuente principal del stack (`ui_source` en Playwright, `spec` en Karate/K6, `apk_path` en Appium Serenity, `platform_context` + `base_url`/`target` en serenity-wdio), el **modo** de operación (`full | dry-run | scaffold-only | execute-only`), `user_story` y `firma` declarados aunque sean nulos, y `risk_map` confirmado. K6 añade su checklist propio.

2. **Ejecutar pre-flight check del stack** invocando la reference correspondiente:
   - Karate → [[karate-greenfield]] (consultar `references/preflight.md` en su subfolder)
   - Playwright → `references/preflight.md` análogo
   - K6 → análogo
   - Appium → análogo
   - serenity-wdio → [[serenity-wdio-greenfield]] (consultar `references/preflight.md` en su subfolder)

1.5. **Solo en brownfield — barrer el repositorio y emitir el inventario (BLOCKER)**: ejecutar `[[calidad-repo-capability-discovery]]` y emitir `.evidence/repo-capability-map.md` (qué scripts, runbook, taxonomía de etiquetas, alcance del ejecutor e integraciones ya existen), más `.evidence/archetype-inventory.md` con la tabla de clasificación de steps (`[[calidad-brownfield-vs-greenfield]]`). **Sin ambos artefactos mostrados al usuario no se genera nada.** De aquí salen los comandos de ejecución y la taxonomía real: prohibido inventarlos.

   Emitir también el **checkpoint de datos de prueba** con validación cruzada contra el catálogo del proyecto (`[[calidad-mandatory-inputs-protocol]]`) y esperar confirmación.

3. **Declarar coverage upfront** antes de generar, con la fórmula de cada stack y mostrando el número al usuario:
   - Karate: por endpoint, calcular `effective_minimum` con fórmula `[[karate-negative-coverage-formula]]` y mostrar al usuario `{endpoint: N}`.
   - Playwright: por HU, calcular `effective_minimum = happy + 2_boundary + 2_negative + 1_edge ≈ 8` mínimo.
   - K6: los 3 escenarios Línea Base / Carga / Estrés (Smoke / Load / Stress en docs k6) son obligatorios. Spike y Soak son opt-in con justificación documentada en `.evidence/scenarios-opt-in.md` (ver [[k6-greenfield]] (consultar `references/vocabulary-and-scenario-mapping.md`)). Declarar también tier (Conservative/Moderate/Relaxed) con razón.
   - Appium: número de escenarios `@smoke` ejecutables + escenarios `@proposed` planeados.
   - serenity-wdio: por plataforma declarada (`web`, `web_movil`, `movil` android/ios, `desktop`, `api`), al menos dos escenarios `@smoke` iniciales; declarar identificadores verificados (`app_package`/`app_activity` o `bundle_id`) cuando aplique móvil.

4. **Generar `STRATEGY.md` y esperar aprobación del usuario antes de proceder a templates.** Aplicar `[[calidad-pre-design-strategy-document]]`. El documento se materializa en `output_path/STRATEGY.md` usando el `STRATEGY.md.tpl` del stack correspondiente (Karate / Playwright / K6 / Appium Serenity / Appium WebdriverIO / serenity-wdio). El agente lo presenta, itera ante "modificar X" y SOLO avanza al paso 5 al recibir "aprobado" (o equivalente explícito). NUNCA se emite código antes de esta aprobación.

5. **Esperar confirmación EXPLÍCITA del usuario** ("procede" o equivalente) antes de emitir el primer archivo de código (separada de la aprobación del STRATEGY.md).

## Restricciones

- NUNCA emitir el primer archivo sin que todos los pasos se hayan completado.
- NUNCA generar ni ejecutar en brownfield sin el mapa de recursos y el inventario del arquetipo emitidos (paso 1.5).
- NUNCA ejecutar un comando que no salga del mapa de recursos o que el usuario no haya confirmado.
- NUNCA emitir código sin `STRATEGY.md` aprobado explícitamente (regla anti-cheating del paso 4).
- NUNCA asumir `modo: full` por defecto — preguntar.
- NUNCA asumir `risk: HIGH` sin confirmar — preguntar.
- Si el IDE no permite preguntas interactivas (modo batch), generar `STRATEGY.md` propuesto + `scaffold-only` con `.evidence/missing-inputs.md` y `.evidence/strategy-approval.md` documentando los faltantes y el bloqueo a aprobación humana asíncrona.

## Cross-links

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-pre-design-strategy-document]]`, `[[calidad-test-execution-orchestration]]`, [[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder), `[[calidad-business-driven-prioritization]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-generate-executive-report]]`.
