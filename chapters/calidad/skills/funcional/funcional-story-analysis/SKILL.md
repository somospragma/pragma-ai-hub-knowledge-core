---
id: calidad-funcional-story-analysis
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [funcional]
description: "Analiza historias de usuario con rigor: scoring INVEST criterio por criterio, calidad y testabilidad de los criterios de aceptación, taxonomía de ambigüedades y vacíos, y veredicto contra la Definition of Ready. Emite un reporte accionable, nunca reescribe la HU."
tags: [funcional, user-story, invest, acceptance-criteria, ambiguity, definition-of-ready, analysis]
---

# Story Analysis — Análisis Riguroso de Historias de Usuario

## Cuándo aplicar

- Cuando el usuario pide analizar, evaluar o auditar una o varias historias de usuario (HU) antes de refinarlas, estimarlas o diseñar sus pruebas.
- Como paso previo automático de `[[calidad-funcional-story-refinement]]` y de `[[calidad-funcional-test-design]]`: no se refina ni se diseñan casos sobre una HU no analizada.
- Desde los stacks de automatización: cuando `[[calidad-mandatory-inputs-protocol]]` recibe una `user_story` débil (sin criterios de aceptación, ambigua), el flujo ofrece este análisis antes de generar código de pruebas.

Las HUs llegan pegadas en el chat, en archivos, o directamente desde Azure DevOps / Jira vía `[[calidad-alm-mcp-integration]]` (work items con título, descripción, criterios de aceptación y links).

## Lectura obligatoria antes de producir el entregable

Este SKILL es el índice; el método vive en `references/`. **Abrir estos ANTES de escribir el entregable** y declarar cuáles se leyeron (traza en `[[calidad-pipeline-state-tracking]]`):

| Reference | Para qué |
|---|---|
| `references/invest-scoring.md` | Rúbrica INVEST con evidencia |
| `references/acceptance-criteria-quality.md` | Auditoría de criterios de aceptación |
| `references/ambiguity-taxonomy.md` | Clasificación de ambigüedades y vacíos |

## Instrucción

1. **Recolectar la HU completa** — título, narrativa (Como/Quiero/Para), criterios de aceptación, descripción, adjuntos referenciados, links a otras HUs/features/épicas. Si viene del ALM, traer también estado, prioridad y relaciones (parent, related, blocked-by). Si algún elemento no existe, registrarlo como hallazgo, no inventarlo.
2. **Scoring INVEST** — evaluar los 6 criterios (Independent, Negotiable, Valuable, Estimable, Small, Testable) con la rúbrica de `references/invest-scoring.md`: cada criterio recibe `pass | warn | fail` con evidencia textual de la HU (citar la frase que motiva el veredicto). Nunca un score global sin el detalle por criterio.
3. **Evaluar los criterios de aceptación** — con `references/acceptance-criteria-quality.md`: formato (Gherkin vs checklist vs prosa), atomicidad, testabilidad (¿un tester tercero puede decidir pass/fail sin preguntar?), completitud contra la narrativa, presencia de caminos negativos y de borde, datos concretos vs vaguedades.
4. **Detectar ambigüedades y vacíos** — aplicar la taxonomía de `references/ambiguity-taxonomy.md`: ambigüedad léxica, de referencia, de cuantificación, condiciones sin else, reglas implícitas, dependencias no declaradas, casos límite ausentes. Cada hallazgo se registra como **pregunta concreta para el PO**, no como crítica abstracta.
5. **Veredicto Definition of Ready** — `ready | ready_with_warnings | not_ready` con la lista exacta de lo que falta para `ready`. El umbral: ninguna HU con criterio INVEST `fail` o con criterios de aceptación no testables puede ser `ready`.
6. **Emitir el reporte** — formato de `references/analysis-report-format.md`. Si la HU vino del ALM y el usuario lo aprueba, publicar el reporte como comentario del work item (`[[calidad-alm-mcp-integration]]`); nunca modificar la HU original desde este skill.

## Restricciones

- **Este skill NO reescribe la HU** — analiza y pregunta. La reescritura es de `[[calidad-funcional-story-refinement]]` y pasa por aprobación humana.
- **NUNCA inventar** reglas de negocio, criterios de aceptación ni respuestas a las preguntas detectadas: los vacíos se reportan como preguntas al PO, aunque la respuesta "parezca obvia".
- **NUNCA suavizar el veredicto** para no incomodar: una HU `not_ready` se reporta `not_ready` con evidencia. El costo de diseñar pruebas sobre una HU rota es mayor que el de la conversación incómoda.
- Cada hallazgo cita el texto de la HU que lo motiva (línea o frase); hallazgos sin evidencia textual no se emiten.
- En lotes (varias HUs de un sprint/plan), emitir un reporte por HU más un resumen agregado con distribución de veredictos.

## Cross-links

- `references/invest-scoring.md`
- `references/acceptance-criteria-quality.md`
- `references/ambiguity-taxonomy.md`
- `references/analysis-report-format.md`
- `[[calidad-funcional-story-refinement]]`, `[[calidad-funcional-test-design]]`, `[[calidad-alm-mcp-integration]]`, `[[calidad-analyze-and-refine-stories]]`
