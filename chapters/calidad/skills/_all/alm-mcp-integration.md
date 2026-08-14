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

## Vías de conexión, en orden

El MCP remoto oficial es el default, **no la única vía**. En entornos corporativos con proxies, restricciones de red o políticas que bloquean los callbacks de OAuth, puede autenticar y aun así no exponer proyectos. Cuando eso pasa, se baja de nivel en vez de declarar el flujo bloqueado:

| # | Vía | Cuándo | Auth |
|---|---|---|---|
| 1 | MCP remoto oficial | default | OAuth gestionado por el cliente MCP |
| 2 | **MCP local por token de API** (servidor stdio comunitario) | el remoto no expone proyectos, o el entorno bloquea OAuth | token de API + correo del usuario, por variables de entorno |
| 3 | **REST directa** | ningún MCP viable, o se necesitan capacidades que el MCP no expone | token de API con autenticación básica |

La vía 2 es de **primera clase**, no un último recurso: es la que funciona en muchos entornos corporativos. Y la vía 3 es, en escritura, **más capaz que el MCP**: el MCP típicamente no expone adjuntos, campos personalizados completos ni las APIs de los productos de gestión de pruebas. Si el repositorio del cliente ya tiene scripts que hablan por REST con el ALM, están en el mapa de `[[calidad-repo-capability-discovery]]` y **se usan en vez de reimplementarlos**.

## Scopes mínimos del token de API

| Uso | Scopes |
|---|---|
| Solo lectura (recomendado para el agente) | leer trabajo (incidencias, proyectos, campos, comentarios), leer usuarios, validar la propia identidad |
| Lectura y escritura | los anteriores más escribir trabajo (crear y actualizar incidencias, comentar, transicionar) |

El token clásico sin scopes y el token con scopes **no se comportan igual**: pedir el de scopes acotados y recordar expiración corta.

## Verificación post-conexión (obligatoria antes de prometer capacidades)

Que el panel del IDE diga "conectado" no significa que la conexión sirva. Antes de ofrecer cualquier operación, ejecutar los tres chequeos **de lectura**:

1. **Identidad**: ¿devuelve el usuario autenticado?
2. **Visibilidad**: ¿lista proyectos? Una lista vacía con autenticación correcta significa scopes insuficientes o sesión sin permisos sobre el sitio.
3. **Lectura concreta**: ¿trae el work item o la incidencia que el usuario citó?

Si cualquiera falla, **la conexión no está operativa** aunque el estado diga lo contrario. Se reporta cuál falló y se baja a la vía siguiente.

**Síntomas conocidos y su lectura:** información de servidor correcta pero identidad fallida → sesión sin permisos efectivos, no problema de red. Búsqueda de proyectos vacía → scopes o sitio equivocado. Mensajes de error en un idioma inesperado → se está hablando con un sitio distinto del que se cree. Herramientas de un servidor local que no aparecen conviviendo con un servidor remoto activo → conflicto de servidores; probar el local aislado antes de descartarlo.

## Capacidades: verificar, no suponer

Las capacidades de escritura se **verifican con una operación real** sobre un elemento desechable y se registran; hasta entonces se declaran `sin verificar`. Dos capacidades que suelen confundirse y hay que probar por separado: **crear incidencias del tipo que usan los casos de prueba** en el gestor de proyectos, y **escribir en el gestor de pruebas**, que normalmente es un producto aparte con su propia API y su propia autenticación, independiente de los permisos del usuario. Detalle del escalonado en `[[calidad-alm-test-publishing-cycle]]`.

"Creemos que no tenemos permisos" no es un diagnóstico: o se probó y se registró, o está sin verificar.

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

1. **Leer es libre; TODA escritura tiene gate.** Sin distinción entre crear y modificar: crear, editar, transicionar, comentar, vincular, mover, subir o adjuntar exigen autorización humana explícita, previa y específica, pedida con la ficha de operación de `[[calidad-alm-write-authorization-gate]]` — que incluye conteo exacto y efectos colaterales. Esa regla **reemplaza** la distinción más laxa que traía este asset, en la que crear elementos nuevos bastaba con una confirmación de lote informal.
2. **Nunca borrar** work items, casos ni runs del cliente. Lo obsoleto se marca/comenta; borrar es decisión humana ejecutada por humanos.
3. **No tocar casos ya ejecutados**: un test case con ejecuciones registradas no se edita para "alinearlo" — se crea versión/caso nuevo y se referencia (extensión al ALM de la regla anti-cheating brownfield del chapter).
4. **Idempotencia**: antes de crear, buscar si ya existe (mismo título + link a la misma HU) — re-correr un flujo no duplica casos. Reportar "existentes: X, creados: Y, actualizados: Z".
5. **Trazabilidad siempre**: nada se crea suelto — todo test case linkeado a su HU, todo defecto a su caso. Los links son la RTM ([[calidad-funcional-test-plan]], consultar `references/traceability-rtm.md` en su subfolder).
6. **Batch con reporte**: operaciones masivas van por fases con confirmación y resumen final (creados/vinculados/omitidos/errores) — el flujo por fases lo gobierna cada workflow que use este skill.
7. Errores de permiso o rate limit se reportan con causa exacta y se detiene el lote a mitad SIN dejar estado a medias sin reportar (listar qué alcanzó a crearse).

## Cross-links

`[[calidad-alm-write-authorization-gate]]`, `[[calidad-alm-test-publishing-cycle]]`, `[[calidad-funcional-story-analysis]]`, `[[calidad-funcional-story-refinement]]`, `[[calidad-funcional-test-design]]`, `[[calidad-funcional-test-plan]]`, `[[calidad-design-test-cases]]`, `[[calidad-analyze-and-refine-stories]]`, `[[calidad-figma-mcp-integration]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-repo-capability-discovery]]`.
