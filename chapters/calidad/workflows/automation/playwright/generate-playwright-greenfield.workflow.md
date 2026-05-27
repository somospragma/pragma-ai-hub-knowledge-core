---
id: generate-playwright-greenfield
version: 2.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Workflow orquestador para generar un proyecto Playwright greenfield desde una fuente UI real (URL viva, Figma, user story, Storybook). OpenAPI es opcional solo para generar mocks.
tags: [playwright, greenfield, workflow, ui-first, live-app, figma]
---

# Workflow — Generar proyecto Playwright greenfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica la petición como **automation E2E web** y `[[calidad-brownfield-vs-greenfield]]` determina **greenfield Playwright** (no existe proyecto previo entregado por el usuario).

## Inputs

| Input               | Obligatorio | Descripción                                                                                                       |
|---------------------|-------------|-------------------------------------------------------------------------------------------------------------------|
| `ui_source`         | sí          | Insumo principal que describe la UI (URL, Figma, texto de user story, URL Storybook, o combinación).               |
| `ui_source_type`    | sí          | `live-url | figma | user-story | storybook | hybrid | opt-mock-from-spec`. El último solo cuando se mockea desde OpenAPI sin generar pages. |
| `project_name`      | sí          | Nombre kebab-case del proyecto (raíz de la estructura).                                                            |
| `output_path`       | sí          | Ruta donde se materializará el proyecto.                                                                           |
| `base_url`          | no          | URL del frontend bajo prueba. Si falta, usar `process.env.BASE_URL`.                                               |
| `backend_url`       | no          | URL del backend que el frontend consume. Si falta, usar `process.env.BACKEND_URL`.                                 |
| `priority_assignments` | no       | Mapa `pageName -> CRITICAL | HIGH | MEDIUM | LOW` provisto por usuario/PO. Si falta, preguntar.                  |
| `mock_mode`         | no          | `off | full | partial`. Default `off`. Solo declarar si el usuario quiere mocks.                                  |
| `mock_endpoints`    | no          | Lista de paths a mockear cuando `mock_mode = partial`.                                                             |
| `spec`              | no          | OpenAPI/Swagger. **Opcional** y se usa SOLO como insumo del prompt de mocks. Nunca como fuente de páginas.         |
| `user_story`        | no          | Contexto funcional adicional.                                                                                      |
| `firma`             | no          | Identidad del autor para README/reporte.                                                                           |

La recolección sigue `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

1. **Validar UI source** — Verifica que `ui_source` describa UI real según `ui_source_type`:
   - `live-url`: URL accesible y autenticable si aplica.
   - `figma`: link público o screenshots con jerarquía de páginas.
   - `user-story`: historia con flujos UI explícitos (no solo reglas backend).
   - `storybook`: URL del Storybook publicada.
   - Si el usuario solo provee `spec` (OpenAPI) sin `ui_source`, **detente** y solicita una fuente UI según `[ui-source-priority](../../../skills/automation/playwright/playwright-greenfield/references/ui-source-priority.md)`.
2. **Detectar páginas** — Invoca `[[playwright-detect-pages-from-ui-source-prompt]]` con `ui_source_type`, `ui_source_content = ui_source`, `user_story` y `priority_assignments`. Output: lista de páginas con `route` (frontend), `form_fields`, `navigation`, `selectors_hint`, `page_type` y `priority`.
3. **Resolver prioridades faltantes** — Para cada página con `priority: UNKNOWN`, pregunta al usuario/PO antes de continuar. Nunca infieras prioridad desde el nombre.
4. **Detectar flujos de usuario** — Clasifica navegación, formularios, auth, listados/paginación a partir de la UI detectada. Cada flujo mapeará a uno o más `.spec.ts`.
5. **Decidir `mock_mode`** — Pregunta explícita al usuario si no lo declaró:
   - `off` (default) → suite 100% `@live`; no se genera carpeta `mocks/`.
   - `full` → genera mocks y suite `@mocked` además de `@live`.
   - `partial` → genera mocks dirigidos para `mock_endpoints` y suite `@hybrid`.
6. **Planificar tests** — Para cada página: 5-8 escenarios funcionales con tag `@live` por defecto. Marcar visual + a11y en páginas `CRITICAL` y `HIGH`. Aplicar `[[calidad-route-test-generation]]` para mapear flujo UI → test.
7. **Generar Page Objects** — Por cada página, invoca `[[playwright-generate-page-object-prompt]]` siguiendo `[POM](../../../skills/automation/playwright/playwright-greenfield/references/page-object-model.md)` + `[selector-priority](../../../skills/automation/playwright/playwright-greenfield/references/selector-priority.md)`. `navigate()` usa la `route` frontend detectada (anti-patrón rutas inventadas).
8. **Generar mocks (opt-in)** — SOLO si `mock_mode != off`, invoca `[[playwright-generate-mock-handlers-prompt]]` con `endpoints = mock_endpoints` (o subset del `spec`) y `mock_mode`. Sigue `[mocks-page-route](../../../skills/automation/playwright/playwright-greenfield/references/mocks-page-route.md)`. Si `mock_mode = off`, **no se crea** la carpeta `mocks/` ni el fixture `mockApi`.
9. **Generar tests** — Emite primero los `tests/*.spec.ts` con tag `@live` por defecto (`[[playwright-greenfield]]` paso 6). Tests que ejerciten error states con mocks llevan `@mocked` o `@hybrid` y declaran `mockApi` en la firma. Para suites de accesibilidad invoca `[[playwright-generate-a11y-prompt]]`; para visual aplica `[visual-regression](../../../skills/automation/playwright/playwright-greenfield/references/visual-regression.md)`.
10. **Emitir infraestructura** — `playwright.config.ts`, `tsconfig.json`, `package.json`, `.gitignore`, `README.md` según `[config-strict-ts](../../../skills/automation/playwright/playwright-greenfield/references/playwright-config-strict-ts.md)` y `[project-structure](../../../skills/automation/playwright/playwright-greenfield/references/project-structure.md)`. Incluir `BASE_URL`, `BACKEND_URL` y projects filtrados por tag (`@live`, `@mocked`, `@hybrid`). Si la UI tiene login real, además `fixtures/auth.setup.ts` y projects con `dependencies: ['setup']` según `[auth-storage-state](../../../skills/automation/playwright/playwright-greenfield/references/auth-storage-state.md)`.
11. **Entregar y trazar** — Usa `[[calidad-streaming-files-protocol]]` para la entrega ordenada. Vincula la evidencia con `[[calidad-test-evidence-and-traceability]]`. Documenta los modos en `[execution-modes-live-mocked-hybrid](../../../skills/automation/playwright/playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)` y referencia `[[playwright-run-and-modes]]`.

## Criterios de finalización (DoD)

- [ ] ≥1 `tests/{resource}.spec.ts` por página detectada, con tag `@live` por defecto.
- [ ] ≥1 Page Object (`pages/{Resource}Page.ts`) por página detectada; `navigate()` usa la ruta frontend de la fuente UI, NO un path backend.
- [ ] `fixtures/base.fixture.ts` compone TODOS los Page Objects. `mockApi` se declara como fixture **opt-in** (sin `{ auto: true }`) SOLO si `mock_mode != off`; de lo contrario, no se declara.
- [ ] `mocks/api-handlers.ts` SOLO existe si el usuario declaró `mock_mode` o `mock_endpoints`. En modo `off`, la carpeta `mocks/` NO se genera.
- [ ] `tests/visual.spec.ts` cubre páginas `CRITICAL` y `HIGH` con tag `@live` (skip de firefox/webkit).
- [ ] `tests/accessibility.spec.ts` cubre páginas `CRITICAL` y `HIGH` con WCAG 2.1 AA y tag `@live`.
- [ ] `playwright.config.ts` con projects filtrados por tag (`live-*`, `mocked-*`, `hybrid-*`), `baseURL` desde `process.env.BASE_URL`, `BACKEND_URL` disponible vía `process.env`, y bloque `webServer` comentado.
- [ ] `tsconfig.json` con `strict: true` y path aliases (`@pages/*`, `@fixtures/*`, `@mocks/*`, `@utils/*`).
- [ ] `package.json` con scripts `test`, `test:live`, `test:mocked`, `test:hybrid`, `test:all`, `test:headed`, `test:ui`, `test:debug`, `test:visual`, `test:a11y`, `report`.
- [ ] `README.md` en español con comandos de install, modos `@live/@mocked/@hybrid`, override de `BASE_URL` y `BACKEND_URL`.
- [ ] Si la UI tiene login real: `fixtures/auth.setup.ts` y projects con `dependencies: ['setup']` + `storageState: '.auth/user.json'`. La existencia de `security` en un OpenAPI **no** justifica por sí sola este bloque.
- [ ] Prioridades de páginas provienen de `priority_assignments` o consulta directa al usuario; ninguna inferida por keyword.
- [ ] `.gitignore` excluye `node_modules/`, `test-results/`, `playwright-report/`, `.auth/`, `**/.env`.
