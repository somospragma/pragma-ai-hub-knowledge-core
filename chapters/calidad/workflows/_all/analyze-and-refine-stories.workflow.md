---
id: calidad-analyze-and-refine-stories
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
description: "Workflow para analizar y refinar historias de usuario: trae HUs (ALM o manuales), analiza INVEST/CA/ambigüedades, propone refinamiento, espera aprobación del PO y aplica lo aprobado de vuelta al ALM."
tags: [funcional, workflow, user-story, analysis, refinement, invest, alm]
---

# Workflow — Analizar y Refinar Historias de Usuario

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica el intent como funcional de análisis/refinamiento: "analiza estas HUs", "revisa el INVEST", "refina la historia", "prepara el refinamiento del sprint". También como remediación cuando `[[calidad-mandatory-inputs-protocol]]` detecta una `user_story` débil en un flujo de automatización.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `stories_source` | Sí | IDs/URLs de work items (Azure/Jira), query (WIQL/JQL), o el texto de las HUs pegado. |
| `output_path` | Sí | Donde se persisten reportes y propuestas. |
| `alcance` | No | `solo_analisis` (default si el usuario solo pidió analizar) o `analisis_y_refinamiento`. |
| `write_back` | No | `true|false` — publicar al ALM (comentarios, actualizaciones aprobadas). Default `false` hasta confirmación. |

## Pasos

### Paso 1 — Traer las HUs

Si `stories_source` apunta al ALM, aplicar `[[calidad-alm-mcp-integration]]` (setup guiado si no está configurado; fallback manual si el usuario no puede). Traer cada work item COMPLETO: título, narrativa, descripción, criterios, estado, prioridad, links. Reportar cuántas HUs entraron al lote.

### Paso 2 — Analizar

Aplicar `[[calidad-funcional-story-analysis]]` a cada HU: INVEST con evidencia, calidad de CA, ambigüedades/vacíos como preguntas al PO, veredicto DoR. Persistir reporte por HU + resumen agregado en `output_path/analysis/`. Presentar el resumen al usuario.

### Paso 3 — Decidir continuación

- `solo_analisis` → saltar al paso 6. Ofrecer publicar los reportes como comentarios en el ALM (requiere confirmación).
- `analisis_y_refinamiento` → continuar con las HUs `not_ready` y `ready_with_warnings` (las `ready` no se tocan salvo pedido explícito).

### Paso 4 — Proponer refinamiento

Aplicar `[[calidad-funcional-story-refinement]]`: reescrituras antes/después, CA nuevos/modificados trazados a hallazgos, splitting si aplica, example map si las reglas están difusas. Emitir la propuesta con su bloque de decisión y **esperar la respuesta del PO/usuario ítem por ítem** (gate humano — mismo patrón del STRATEGY.md). Iterar los `ajustar`.

### Paso 5 — Aplicar lo aprobado

Solo los ítems aprobados: actualizar work items, crear hijas del splitting con links parent-child, dejar comentario de auditoría — todo vía `[[calidad-alm-mcp-integration]]` con confirmación del lote antes de escribir. Sin ALM: entregar los markdown finales. Los rechazados se registran con el comentario del PO.

### Paso 6 — Cierre

Emitir el bloque `[[calidad-delivery-gate-contract]]` adaptado al stack funcional: `framework: funcional`, `execution.*: null` (no aplica ejecución), `files_emitted` con reportes/propuestas, y en `coverage` el conteo de HUs por veredicto. `status: success` solo si el lote completo fue analizado y toda escritura al ALM fue aprobada y confirmada; preguntas abiertas van en `next_steps`.

## Criterios de finalización

- [ ] Cada HU del lote tiene reporte de análisis con INVEST + CA + hallazgos con evidencia textual.
- [ ] Ningún hallazgo del análisis se perdió: resuelto en propuesta o registrado como pregunta abierta.
- [ ] Cero reescrituras aplicadas sin aprobación explícita; cero preguntas respondidas por el agente en nombre del PO.
- [ ] Escrituras al ALM: solo las aprobadas, con comentario de auditoría, reportadas (creadas/actualizadas/omitidas).
- [ ] Delivery gate emitido con el resumen del lote.
