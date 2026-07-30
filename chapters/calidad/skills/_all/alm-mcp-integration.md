---
id: calidad-alm-mcp-integration
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Integración con Azure DevOps y Jira vía MCP: traer insumos (HUs, work items, test plans) y llevar resultados (test cases, links, estados, comentarios, defectos) desde el agente del IDE. Setup guiado por IDE, permisos mínimos y reglas de escritura segura en el ALM del cliente."
tags: [alm, azure-devops, jira, mcp, work-items, test-plans, integration, setup, traceability]
---

# ALM MCP Integration — Azure DevOps y Jira desde el Agente

## Problema que resuelve

Los insumos del proceso (HUs, criterios, test plans) y los resultados (casos diseñados, estados, defectos, reportes) viven en el ALM del cliente — Azure DevOps o Jira. Copiarlos a mano en ambas direcciones es lento y desincroniza. Este skill define cómo el agente se conecta vía **MCP**, qué puede leer y escribir, y con qué salvaguardas. Es la puerta ALM de todo el chapter: la usa el stack funcional (análisis, refinamiento, casos, planes) y los stacks de automatización (publicar resultados y defectos).

## Servidores MCP (verificados contra doc oficial)

| Plataforma | Server | Conexión | Auth | Capacidades relevantes |
|---|---|---|---|---|
| **Azure DevOps** | `@azure-devops/mcp` (oficial Microsoft, preview) | stdio: `npx -y @azure-devops/mcp {organizacion}` — activar dominios con `-d` (ej. `-d core work work-items test-plans`) | Interactiva Microsoft o `--authentication azcli` (sesión `az login`) | Dominios: `core`, `work`, `work-items`, `search`, `test-plans`, `repositories`, `wiki`, `pipelines` |
| **Jira / Confluence** | Atlassian Remote MCP Server (oficial) | HTTP remoto: `https://mcp.atlassian.com/v1/mcp/authv2` | OAuth 2.1 (gestionado por el cliente MCP); opción API token | Buscar/resumir, crear y editar work items, comentar, transicionar estados; Confluence para publicar documentos |

Config por IDE: mismo patrón que `[[calidad-figma-mcp-integration]]` — Kiro `.kiro/settings/mcp.json` (raíz `mcpServers`; server remoto con `"url"` + OAuth), Claude Code `claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp/authv2` o stdio para Azure, VS Code `.vscode/mcp.json` (raíz `servers`, bloque `inputs` para la organización). El MCP actúa **con los permisos del usuario autenticado**: pedir el principio de menor privilegio y jamás persistir tokens en el repo.

## Flujo del agente

```
1. ¿Hay server MCP del ALM configurado y autenticado?
   ├── Sí → probar con una lectura inocua (el work item/plan que el usuario citó). OK → continuar.
   └── No → ofrecer setup guiado (snippet por IDE + auth) y reintentar. Si el usuario no puede/quiere:
            fallback manual — pedir los insumos pegados (HU completa con CA) y entregar los
            resultados como markdown listo para copiar. El flujo NUNCA se bloquea por falta de MCP.
2. TRAER insumos: work items por ID, query/WIQL/JQL, o test plan → HUs con título, descripción,
   CA, estado, prioridad, links. Traer TODO el work item, no solo el título.
3. LLEVAR resultados según la operación (tabla abajo), siempre bajo las reglas de escritura.
```

## Operaciones por dirección

| Operación | Azure DevOps | Jira |
|---|---|---|
| Leer HUs/work items (insumo de análisis/diseño) | work item por ID, WIQL, items de un test plan/suite | issue por key, JQL, issues de un épic/sprint |
| Publicar análisis/refinamiento | Comentario en el work item; actualización de descripción/CA SOLO post-aprobación | Ídem (comment / edit post-aprobación) |
| Crear HUs hijas (splitting aprobado) | Work items con link parent-child | Issues con link al épic/parent |
| Crear test cases y vincular | Test case + link "Tests" a la HU + asignación a suite del test plan (dominio `test-plans`) | Issue de test (nativo limitado; con **Xray/Zephyr** el tipo Test y el requirement coverage — verificar qué expone la instancia del cliente antes de prometer) |
| Publicar resultados de ejecución | Estado de test points/runs; comentario con evidencia y link al executive report | Transición del test/issue + comentario con evidencia |
| Crear defectos | Bug linkeado al test case y a la HU | Bug/Defect linkeado |
| Publicar documentos (plan, estrategia, cierre) | Wiki del proyecto (dominio `wiki`) | Confluence |

## Reglas de escritura (innegociables)

1. **Leer es libre; escribir tiene gate**: toda escritura que modifique contenido existente (descripción, CA, estados de HU) exige aprobación humana previa — el patrón propuesta→aprobación de `[[calidad-funcional-story-refinement]]`. Crear elementos nuevos (comentarios, test cases, defectos) requiere confirmación del lote antes de ejecutarlo ("voy a crear 14 test cases vinculados a 3 HUs en la suite X — ¿confirmas?").
2. **Nunca borrar** work items, casos ni runs del cliente. Lo obsoleto se marca/comenta; borrar es decisión humana ejecutada por humanos.
3. **No tocar casos ya ejecutados**: un test case con ejecuciones registradas no se edita para "alinearlo" — se crea versión/caso nuevo y se referencia (extensión al ALM de la regla anti-cheating brownfield del chapter).
4. **Idempotencia**: antes de crear, buscar si ya existe (mismo título + link a la misma HU) — re-correr un flujo no duplica casos. Reportar "existentes: X, creados: Y, actualizados: Z".
5. **Trazabilidad siempre**: nada se crea suelto — todo test case linkeado a su HU, todo defecto a su caso. Los links son la RTM ([[calidad-funcional-test-plan]], consultar `references/traceability-rtm.md` en su subfolder).
6. **Batch con reporte**: operaciones masivas van por fases con confirmación y resumen final (creados/vinculados/omitidos/errores) — el flujo por fases lo gobierna cada workflow que use este skill.
7. Errores de permiso o rate limit se reportan con causa exacta y se detiene el lote a mitad SIN dejar estado a medias sin reportar (listar qué alcanzó a crearse).

## Cross-links

`[[calidad-funcional-story-analysis]]`, `[[calidad-funcional-story-refinement]]`, `[[calidad-funcional-test-design]]`, `[[calidad-funcional-test-plan]]`, `[[calidad-design-test-cases]]`, `[[calidad-analyze-and-refine-stories]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-test-evidence-and-traceability]]`.
