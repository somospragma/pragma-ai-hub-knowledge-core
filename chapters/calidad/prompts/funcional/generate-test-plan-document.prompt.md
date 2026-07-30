---
id: calidad-funcional-generate-test-plan-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [funcional]
description: "Prompt puntual que redacta el documento de plan de pruebas (estructura ISO 29119-3) desde un contexto ya levantado, con riesgos y criterios medibles; marca como A DETERMINAR todo dato no provisto, sin inventar."
tags: [funcional, prompt, test-plan, iso-29119, risk-analysis]
---

# Prompt — Generar Documento de Plan de Pruebas

## Cuándo invocar este prompt

Cuando el contexto YA está levantado (alcance, riesgos conocidos, fechas, equipo) y solo falta redactar el documento. Si el contexto no existe, usar el workflow `[[calidad-build-test-strategy-and-plan]]` que lo levanta con el usuario — este prompt NO entrevista ni completa vacíos.

## Variables

- `{{contexto}}` — Todo lo levantado: producto/release, alcance (IDs de HUs/épicas), estrategia existente o lineamientos, riesgos conocidos, ambientes y su estado, equipo/roles, hitos/fechas, exigencias del cliente (formal vs ligero).
- `{{nivel}}` — `ligero` | `formal`.
- `{{defaults_criterios}}` — Opcional: valores para los criterios de entrada/salida/suspensión. Sin ellos, se emiten los defaults del chapter marcados `[DEFAULT — confirmar]`.

## Instrucción para el LLM

Aplica `[[calidad-funcional-test-plan]]` estrictamente (consultar `references/test-plan-structure.md`, `references/risk-analysis-matrix.md` y `references/entry-exit-criteria.md` en su subfolder):

1. Redacta las 14 secciones de la estructura 29119-3 con la profundidad de `{{nivel}}`; secciones no aplicables se eliminan con nota, no se rellenan con generalidades.
2. Matriz de riesgos producto + proyecto: cada riesgo con probabilidad × impacto, mitigación, contingencia y dueño — riesgo incompleto no entra (queda como pregunta abierta).
3. Criterios de entrada/salida/suspensión con números; los no confirmados, `[DEFAULT — confirmar]`.
4. **Todo dato ausente del contexto queda `[A DETERMINAR — dueño, fecha]` visible. PROHIBIDO inventar SLAs, fechas, nombres, ambientes o cifras.** Un plan con TBDs honestos es el entregable correcto; uno completo e inventado es el defecto.
5. Cierra el documento con la tabla de aprobaciones vacía y el historial de versiones iniciado (v0.1 — borrador para aprobación).

Recuerda en la salida: el documento es un BORRADOR hasta aprobación humana; no rige el proceso por haber sido generado.
