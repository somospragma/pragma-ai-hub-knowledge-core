---
id: calidad-pre-generation-protocol
version: 1.3.0
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

0. **Abrir con el estado, no con la tarea** — Ejecutar el comando de estado de sesión (`emit-session-state.py` de `[[calidad-delivery-gate-contract]]`): imprime fase actual, siguiente acción, bloqueos vigentes y correcciones a reafirmar, leyendo la traza y la bitácora. Si no hay traza, se crea antes de tocar nada. **Se continúa por su siguiente acción, no por lo que parezca urgente.** Detalle del contrato de traza en `[[calidad-pipeline-state-tracking]]`.

1. **Confirmar mandatory inputs** (todos obligatorios, ninguno se asume) y **leer COMPLETO cada insumo entregado**, emitiendo la tabla de extracción: qué se extrajo de cada uno y dónde se usará (`[[calidad-mandatory-inputs-protocol]]`). **Un insumo sin fila es un insumo ignorado.** Como mínimo: `intent`, `project_name` en kebab-case, `output_path` absoluto, la fuente principal del stack, el **modo** de operación, `user_story` y `firma` declarados aunque sean nulos, y `risk_map` confirmado. K6 añade su checklist propio.

1.5. **Solo en brownfield — barrer el repositorio y emitir el inventario (BLOCKER)**: ejecutar `[[calidad-repo-capability-discovery]]` y emitir `.evidence/repo-capability-map.md` (qué scripts, runbook, taxonomía de etiquetas, alcance del ejecutor e integraciones ya existen), más `.evidence/archetype-inventory.md` con la tabla de clasificación de steps (`[[calidad-brownfield-vs-greenfield]]`). **Sin ambos artefactos mostrados al usuario no se genera nada.** De aquí salen los comandos de ejecución y la taxonomía real: prohibido inventarlos.

   Emitir también el **checkpoint de datos de prueba** con validación cruzada contra el catálogo del proyecto (`[[calidad-mandatory-inputs-protocol]]`) y esperar confirmación.

1.6. **Dictaminar la preparación del sistema, no sólo la llegada de los insumos (BLOCKER)**: emitir `.evidence/input-sufficiency.json` con `[[calidad-sut-readiness-gate]]`. La historia llega casi siempre y casi nunca basta: se evalúa **suficiencia entrada por entrada** y, en lo que falte, se nombra la pieza —no el documento—, de dónde puede venir y qué cuesta seguir sin ella. En front son obligatorios además el recorrido funcional (`[[calidad-functional-flow-input]]`, `.evidence/functional-flow.md`) y la declaración de fuentes de interfaz con el eje que cubre cada una (`[[calidad-ui-source-contract]]`, `.evidence/ui-sources.md`). Si el usuario decide arrancar igual, se arranca: queda registrado como riesgo aceptado con su cifra.

1.7. **Resolver lo determinista con herramientas del proyecto, no con el razonamiento (BLOCKER)**: aplicar `[[calidad-deterministic-work-to-tooling]]` y emitir `.evidence/tooling-gaps.md`. Lo que el repositorio ya resuelve se usa; lo que no, se construye una vez, se documenta y se registra. Un hueco que no se puede cerrar se declara con lo que costaría y lo que ahorraría. Y cuando el objetivo es mock o híbrido, se lee antes el manifiesto de `[[calidad-pre-development-artifacts-continuity]]`: qué se hereda y qué se añade, porque reconstruir lo que ya existía es el desperdicio más caro de ese modo.

2. **Ejecutar el pre-flight check del stack** invocando la reference `preflight.md` del skill greenfield correspondiente. Si falla → reportar y **degradar a `scaffold-only`** con razón documentada; no continuar a generación full.

3. **Declarar coverage upfront** antes de generar, con la fórmula de cada stack y mostrando el número al usuario: por endpoint en Karate, por historia en Playwright, los tres escenarios base obligatorios más los opt-in justificados en K6, y escenarios ejecutables contra planeados en Appium. El detalle de cada fórmula vive en el skill greenfield del stack.

4. **Generar `STRATEGY.md` y esperar aprobación del usuario antes de proceder a templates.** Aplicar `[[calidad-pre-design-strategy-document]]`. El documento se materializa en `output_path/STRATEGY.md` usando el `STRATEGY.md` del stack correspondiente (Karate / Playwright / K6 / Appium). El agente lo presenta, itera ante "modificar X" y SOLO avanza al paso 5 al recibir "aprobado" (o equivalente explícito). NUNCA se emite código antes de esta aprobación.

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

`[[calidad-mandatory-inputs-protocol]]`, `[[calidad-pre-design-strategy-document]]`, `[[calidad-test-execution-orchestration]]`, [[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder), `[[calidad-business-driven-prioritization]]`, `[[calidad-test-organization-by-scenario]]` — cómo se reparten los archivos cuando el alcance trae tres o más historias, `[[calidad-delivery-gate-contract]]`, `[[calidad-generate-executive-report]]`.
