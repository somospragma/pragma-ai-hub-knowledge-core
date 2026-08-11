---
id: calidad-build-test-strategy-and-plan
version: 1.0.0
scope: chapter
type: workflow
chapter: calidad
description: "Workflow para construir la estrategia de pruebas y/o el plan de pruebas de un producto o release: levantamiento de contexto, estrategia risk-based, plan ISO 29119-3 con riesgos y criterios medibles, aprobación humana y publicación (wiki/Confluence/ALM)."
tags: [funcional, workflow, test-strategy, test-plan, risk-based, iso-29119, alm]
---

# Workflow — Construir Estrategia y Plan de Pruebas

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica el intent como estrategia/plan: "define la estrategia de pruebas", "arma el plan de pruebas del release", "necesito el test plan para el cliente". El alcance se resuelve en el paso 1: estrategia sola, plan solo (con estrategia existente), o ambos.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `alcance` | Sí | `estrategia` \| `plan` \| `ambos`. |
| `contexto_fuente` | Sí | De dónde sale el contexto: HUs/épicas del ALM (query o IDs), documentos del producto, o entrevista al usuario en el chat. |
| `output_path` | Sí | Persistencia de los documentos. |
| `nivel_plan` | No | `ligero` (equipo ágil interno) \| `formal` (cliente que exige plan completo). Preguntar si no viene. |
| `publish_target` | No | `wiki-azure` \| `confluence` \| `local` (default `local`). |

## Pasos

### Paso 1 — Levantar contexto

Traer alcance funcional desde el ALM si aplica (`[[calidad-alm-mcp-integration]]`): épicas/features/HUs del release. Completar con el usuario lo que ningún documento dice: arquitectura del SUT (`[[calidad-sut-types-and-adaptations]]`), criticidad y regulación (`[[calidad-context-determined-defaults]]`), práctica del equipo (BDD/ATDD/tradicional), estado de ambientes y desarrollo (`[[calidad-sut-readiness-gate]]` — probar antes del desarrollo cambia la estrategia), automatización existente. Los vacíos quedan como supuestos declarados o preguntas con dueño — no se inventan.

### Paso 2 — Construir la estrategia (si `alcance != plan`)

Aplicar `[[calidad-funcional-test-strategy]]`: niveles y frontera con lo unitario, cuadrantes/tipos con las capas transversales (`[[calidad-transversal-capabilities]]`), risk map producto acordable con negocio, mapeo a stacks de automatización con verificación de viabilidad de insumos, datos y ambientes. Documento standalone en `output_path/strategy/`. Presentar y **esperar aprobación** (gate humano); iterar los ajustes.

### Paso 3 — Construir el plan (si `alcance != estrategia`)

Aplicar `[[calidad-funcional-test-plan]]` con la profundidad de `nivel_plan`: estructura 29119-3 completa, riesgos producto+proyecto con dueño/mitigación/contingencia, criterios entrada/salida/suspensión medibles (valores fijados con el usuario), RTM como mecanismo declarado, cronograma con hitos verificables. Si `alcance = plan` y existe estrategia previa, referenciarla; si no existe, la sección 4 la construye en versión mínima con el mismo rigor del paso 2. Presentar y **esperar aprobación**.

### Paso 4 — Publicar

Con aprobación y si `publish_target != local`: wiki de Azure DevOps o Confluence vía `[[calidad-alm-mcp-integration]]`, con confirmación previa. El markdown local queda siempre como fuente versionable.

### Paso 5 — Activaciones derivadas (opcional, a elección del usuario)

Ofrecer los siguientes pasos que la estrategia/plan habilitan, sin ejecutarlos de oficio: diseñar los casos del alcance (`[[calidad-design-test-cases]]`), arrancar la automatización de los flujos CRITICAL por el router (`[[calidad-route-test-generation]]`), montar el ciclo de informes de avance.

### Paso 6 — Delivery gate

`[[calidad-delivery-gate-contract]]` adaptado: `framework: funcional`, `files_emitted` = documentos producidos, `execution.*: null`, y en `next_steps` las preguntas abiertas del contexto + las activaciones ofrecidas. `status: success` exige documentos aprobados por humano; documento emitido sin aprobación = `partial`.

## Criterios de finalización

- [ ] Contexto con fuentes citadas; todo dato no confirmado como supuesto declarado o `[A DETERMINAR]` con dueño — cero datos inventados (SLAs, fechas, responsables).
- [ ] Estrategia: los 4 cuadrantes con respuesta, frontera con dev pactada, risk map con calificaciones justificadas, stacks activados viables (insumos verificados).
- [ ] Plan: riesgos completos (dueño+mitigación+contingencia), criterios medibles con valores fijados, secciones no aplicables eliminadas con nota (no rellenadas).
- [ ] Aprobación humana explícita de cada documento antes de publicarlo o de regir.
- [ ] Delivery gate emitido con las activaciones derivadas ofrecidas.
