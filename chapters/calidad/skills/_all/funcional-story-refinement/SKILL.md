---
id: calidad-funcional-story-refinement
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Refina historias de usuario a partir de un análisis previo: reescritura de narrativa y criterios, splitting con patrones SPIDR, Example Mapping / Tres Amigos para descubrir reglas y ejemplos. Todo refinamiento es una PROPUESTA que aprueba el PO; el agente jamás decide el negocio."
tags: [funcional, refinement, spidr, example-mapping, three-amigos, user-story, gherkin]
---

# Story Refinement — Refinamiento Propuesto, Decisión Humana

## Cuándo aplicar

- Después de `[[calidad-funcional-story-analysis]]`, sobre HUs con veredicto `not_ready` o `ready_with_warnings`. No se refina una HU sin análisis previo (el análisis es el diagnóstico; esto es el tratamiento).
- Cuando el usuario pide preparar la sesión de refinamiento del equipo: este skill produce el material (propuestas, ejemplos, preguntas) que la sesión humana discute.

## Instrucción

1. **Partir del reporte de análisis** — cada hallazgo del análisis debe quedar resuelto en la propuesta o convertido en pregunta abierta explícita. Nada se pierde en el camino.
2. **Reescribir la narrativa** cuando el análisis lo pida: Como (rol concreto del sistema) / Quiero (capacidad, no solución técnica) / Para (beneficio observable). Conservar el texto original en la propuesta (antes/después) — el PO decide con ambos a la vista.
3. **Reescribir/completar criterios de aceptación** en el formato que el equipo use (Gherkin en español por defecto): atómicos, decidibles, con datos concretos, cubriendo caminos negativos y bordes detectados. Cada CA nuevo o modificado se marca `[PROPUESTO]` y referencia el hallazgo del análisis que lo motiva.
4. **Evaluar splitting** — si INVEST-Small falló, aplicar los patrones de `references/story-splitting-patterns.md` (SPIDR y complementarios) y proponer la partición: N historias hijas con narrativa y CA borrador cada una, más el orden sugerido por valor.
5. **Example Mapping** cuando las reglas de negocio estén difusas — con `references/example-mapping-three-amigos.md`: derivar reglas (amarillo), ejemplos concretos por regla (verde) y preguntas sin respuesta (rojo). Los ejemplos verdes son la semilla directa de los casos de `[[calidad-funcional-test-design]]`.
6. **Empaquetar la propuesta** — formato de `references/refinement-proposal-format.md`: antes/después, justificación por cambio, preguntas abiertas, y el bloque de decisión para el PO (`aprobar | ajustar | rechazar` por ítem).
7. **Tras la aprobación humana** — aplicar exactamente lo aprobado: actualizar el work item en el ALM (`[[calidad-alm-mcp-integration]]`) o entregar el markdown final. Los ítems no aprobados no se aplican, aunque el agente "esté seguro".

## Restricciones

- **Gate humano obligatorio**: ningún cambio se aplica al ALM ni se da por definitivo sin aprobación explícita del PO/usuario, ítem por ítem o en bloque declarado. Es el mismo patrón del STRATEGY.md (`[[calidad-pre-design-strategy-document]]`).
- **NUNCA responder las preguntas rojas por cuenta propia**: si el PO no está, las preguntas quedan abiertas y la HU no llega a `ready`.
- **NUNCA inventar reglas de negocio** para completar un vacío; la propuesta marca el vacío y ofrece opciones SOLO si son mutuamente excluyentes y obvias del contexto, siempre como pregunta.
- El splitting propone; no se crean work items hijos en el ALM hasta la aprobación.
- Trazabilidad: cada cambio propuesto referencia el hallazgo del análisis que lo origina (`A-3 → CA-2 reescrito`).

## Cross-links

- `references/story-splitting-patterns.md`
- `references/example-mapping-three-amigos.md`
- `references/refinement-proposal-format.md`
- `[[calidad-funcional-story-analysis]]`, `[[calidad-funcional-test-design]]`, `[[calidad-alm-mcp-integration]]`, `[[calidad-analyze-and-refine-stories]]`
