---
id: calidad-pre-generation-protocol
version: 1.0.0
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

1. **Confirmar mandatory inputs** (todos obligatorios, no se asume ninguno):
   - `intent`: qué tipo de pruebas (Karate / Playwright / K6 / Appium)
   - `project_name`: kebab-case
   - `output_path`: ruta absoluta
   - `ui_source` (Playwright) / `spec` (Karate/K6) / `apk_path` (Appium): fuente principal
   - **`modo` de operación**: `full | dry-run | scaffold-only | execute-only`
   - `user_story`: HUT-XXX o `null` (declarar explícitamente)
   - `firma`: documento de servicio o `null`
   - `risk_map`: por endpoint/HU/script `{nombre: CRITICAL|HIGH|MEDIUM|LOW}`; si no se provee, default `HIGH` con confirmación

2. **Ejecutar pre-flight check del stack** invocando la reference correspondiente:
   - Karate → [ver pre-flight Karate](../../skills/karate/karate-greenfield/references/preflight.md) (será creada en otra oleada — link por path relativo)
   - Playwright → `references/preflight.md` análogo
   - K6 → análogo
   - Appium → análogo

   Si pre-flight falla → reportar al usuario y **degradar a `scaffold-only`** con razón documentada. No continuar a generación full.

3. **Declarar coverage upfront** antes de generar:
   - Karate: por endpoint, calcular `effective_minimum` con fórmula `[[karate-negative-coverage-formula]]` y mostrar al usuario `{endpoint: N}`.
   - Playwright: por HU, calcular `effective_minimum = happy + 2_boundary + 2_negative + 1_edge ≈ 8` mínimo.
   - K6: los 5 scripts (smoke, load, stress, spike, soak) son obligatorios, no opcionales; declarar también tier (Conservative/Moderate/Relaxed) con razón.
   - Appium: número de escenarios `@smoke` ejecutables + escenarios `@proposed` planeados.

4. **Esperar confirmación EXPLÍCITA del usuario** ("procede" o equivalente) antes de emitir el primer archivo.

## Restricciones

- NUNCA emitir el primer archivo sin que los 4 pasos se hayan completado.
- NUNCA asumir `modo: full` por defecto — preguntar.
- NUNCA asumir `risk: HIGH` sin confirmar — preguntar.
- Si el IDE no permite preguntas interactivas (modo batch), generar `scaffold-only` con `.evidence/missing-inputs.md` documentando los faltantes.

## Cross-links

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-test-execution-orchestration]]`, `[[karate-negative-coverage-formula]]`, `[[calidad-business-driven-prioritization]]`, `[[calidad-delivery-gate-contract]]`.
