---
id: calidad-design-test-cases
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [funcional]
description: "Workflow por fases para diseñar casos de prueba de alto nivel desde HUs y publicarlos al ALM (Azure Test Plans / Jira): obtener insumos, filtrar, respetar casos ya ejecutados, diseñar con técnicas formales, crear y vincular, reporte final. Funciona también sin ALM con salida markdown."
tags: [funcional, workflow, test-design, test-cases, azure-test-plans, jira, alm, phases]
---

# Workflow — Diseñar Casos de Prueba (y Publicarlos al ALM)

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica el intent como diseño de casos: "diseña los casos de prueba de estas HUs", "crea los test cases del test plan X", "genera casos para el sprint". Cubre el ciclo completo insumo → diseño → publicación → reporte.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `stories_source` | Sí (uno) | Test Plan ID (Azure), IDs/query de work items (Azure/Jira), o HUs pegadas/en archivos. |
| `output_path` | Sí | Persistencia local de casos, matriz y reportes. |
| `publish_target` | No | `azure-test-plans` \| `jira` \| `local` (default `local` hasta que el usuario confirme publicación). |
| `filtros` | No | Estados de HU a excluir (default: excluir Closed/Done), títulos a excluir, prioridad mínima. |
| `formato_equipo` | No | `gherkin` (default) \| `paso-a-paso`; y práctica del equipo (BDD/ATDD) si se conoce. |

## Pasos (por fases, con status y confirmación entre fases)

Cada fase cierra con status al usuario (qué se completó, números, qué sigue) y **espera confirmación** antes de continuar — en lotes grandes esto evita descubrir al final que la fase 1 trajo lo que no era. En lotes triviales (1-2 HUs) el usuario puede autorizar "todo de corrido" al inicio.

### Fase 1 — Obtener insumos

Vía `[[calidad-alm-mcp-integration]]` (o pegado manual): si es Test Plan de Azure, traer suites y HUs vinculadas (el Iteration Path sale del plan); si son work items, traerlos completos. Status: N suites, M HUs.

### Fase 2 — Filtrar

Aplicar `filtros`: excluir por estado/título, listar elegibles vs excluidas con motivo. Status y confirmación.

### Fase 3 — Validar casos existentes (anti-duplicación y anti-cheating)

Por cada HU elegible, consultar casos ya vinculados en el ALM:
- **Con ejecuciones registradas** → NO se tocan (regla de `[[calidad-alm-mcp-integration]]`); si el diseño detecta que quedaron desalineados con la HU, se reporta y se propone caso nuevo versionado.
- Sin ejecutar y alineados → se conservan.
- Sin ejecutar y desalineados → candidatos a actualización (listar, decidirá el usuario en fase 5).
- Sin casos → diseño desde cero.

### Fase 4 — Verificar readiness y analizar contexto

Cada HU debe estar `ready|ready_with_warnings`: si no hay análisis previo, correr `[[calidad-funcional-story-analysis]]` en línea. HUs `not_ready` **salen del lote de diseño** y se reportan con sus bloqueantes (ofrecer `[[calidad-analyze-and-refine-stories]]`). Diseñar sobre HUs rotas produce casos que validan ambigüedades — no se hace.

### Fase 5 — Diseñar

Aplicar `[[calidad-funcional-test-design]]`: técnicas declaradas por HU, casos en el formato del equipo (Gherkin español data-driven por default), prioridad del risk map, matriz CA↔casos al 100%. Persistir en `output_path/test-cases/{HU}/`. Status: casos por HU, distribución happy/negativo/borde, técnicas usadas. Confirmación del set (y de las actualizaciones de la fase 3) antes de publicar.

### Fase 6 — Publicar y vincular (si `publish_target != local`)

Vía `[[calidad-alm-mcp-integration]]`, con confirmación del lote: crear test cases (mapeo de campos según `[[calidad-funcional-test-design]]`, consultar `references/test-case-format.md` en su subfolder), vincular a su HU, asignar a la suite del test plan (Azure) o al esquema Xray/Zephyr disponible (Jira — verificar qué expone la instancia antes de prometer). Idempotencia: existentes se reportan, no se duplican. Status: creados/vinculados/omitidos/errores.

### Fase 7 — Reporte final y delivery gate

Resumen: HUs procesadas y excluidas (con motivo), casos creados/actualizados/intactos, cobertura CA, links al ALM. Emitir `[[calidad-delivery-gate-contract]]` adaptado (`framework: funcional`, `coverage` = matriz CA→casos, `files_emitted` = casos + matriz, `execution.*: null`). La ejecución de los casos NO es parte de este workflow: los automatizables siguen a los stacks vía `[[calidad-route-test-generation]]`; los manuales, al ciclo de ejecución del plan.

## Criterios de finalización

- [ ] 100% de los CA de las HUs diseñadas con al menos un caso; casos huérfanos: cero o justificados por regla.
- [ ] Técnicas declaradas por HU; BVA aplicado en todo CA con límites; data-driven donde había variantes.
- [ ] Casos con ejecuciones previas en el ALM intactos.
- [ ] Publicación solo tras confirmación; idempotente; con reporte creados/vinculados/omitidos/errores.
- [ ] HUs `not_ready` fuera del lote, reportadas con bloqueantes y camino de remediación.
- [ ] Delivery gate emitido; casos automatizables señalados con su stack sugerido.
