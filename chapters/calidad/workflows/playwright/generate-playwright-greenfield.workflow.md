---
id: generate-playwright-greenfield
version: 2.0.0
scope: stack
type: workflow
chapter: calidad
stack: [playwright]
description: Workflow orquestador para generar un proyecto Playwright greenfield desde una fuente UI real (URL viva, Figma, user story, Storybook).
tags: [playwright, greenfield, workflow, ui-first, live-app, figma]
---

# Workflow — Generar proyecto Playwright greenfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica la petición como **automation E2E web** y `[[calidad-brownfield-vs-greenfield]]` determina **greenfield Playwright** (no existe proyecto previo entregado por el usuario).

## Inputs

| Input               | Obligatorio | Descripción                                                                                                       |
|---------------------|-------------|-------------------------------------------------------------------------------------------------------------------|
| `ui_source`         | sí          | Insumo principal que describe la UI (URL, Figma, texto de user story, URL Storybook, o combinación).               |
| `ui_source_type`    | sí          | `live-url | figma | user-story | storybook | hybrid`.                                                              |
| `project_name`      | sí          | Nombre kebab-case del proyecto (raíz de la estructura).                                                            |
| `output_path`       | sí          | Ruta donde se materializará el proyecto.                                                                           |
| `base_url`          | no          | URL del frontend bajo prueba. Si falta, usar `process.env.BASE_URL`.                                               |
| `backend_url`       | no          | URL del backend que el frontend consume. Si falta, usar `process.env.BACKEND_URL`.                                 |
| `priority_assignments` | no       | Mapa `pageName -> CRITICAL | HIGH | MEDIUM | LOW` provisto por usuario/PO. Si falta, preguntar.                  |
| `mock_mode`         | no          | `off | full | partial`. Default `off`. Solo declarar si el usuario quiere mocks.                                  |
| `mock_endpoints`    | no          | Lista declarativa de paths a mockear cuando `mock_mode != off`. Fuentes válidas en orden de preferencia: captura live app → Postman → OpenAPI/Swagger del backend → lista manual (ver [[playwright-greenfield]] (consultar `references/mocks-page-route.md`)). |
| `spec`              | no          | OpenAPI/Swagger del backend. Solo se usa, si se provee, como insumo del prompt de mocks cuando `mock_mode != off`. |
| `user_story`        | no          | Contexto funcional adicional.                                                                                      |
| `firma`             | no          | Identidad del autor para README/reporte.                                                                           |

La recolección sigue `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

### Paso 1 (OBLIGATORIO) — Pre-flight check del stack

Antes de cualquier otra acción, ejecutar el pre-flight según [[playwright-greenfield]] (consultar `references/preflight.md` en su subfolder):
- Si pasa: continuar al paso 2.
- Si falla: aplicar las degradaciones documentadas en `preflight.md` y reportar al usuario antes de proceder.
- Persistir el resultado en `.evidence/preflight-result.json`.

Este paso es enforcement obligatorio según `[[calidad-pre-generation-protocol]]`.

### Paso 2 — Análisis previo (STRATEGY.md)

Antes de generar cualquier código, generar `STRATEGY.md` en el `output_path` según `references/templates/STRATEGY.md.tpl` y `[[calidad-pre-design-strategy-document]]`. Presentar al usuario y esperar:
- "aprobado" → continuar al siguiente paso.
- "modificar X" → iterar el documento; volver a presentar.

NUNCA generar código sin STRATEGY.md aprobado explícitamente.

### Pasos restantes

3. **Validar UI source** — Verifica que `ui_source` describa UI real según `ui_source_type`:
   - `live-url`: URL accesible y autenticable si aplica.
   - `figma`: link público o screenshots con jerarquía de páginas.
   - `user-story`: historia con flujos UI explícitos (no solo reglas backend).
   - `storybook`: URL del Storybook publicada.
   - Si no hay `ui_source` (aunque venga un `spec` o una colección Postman), **detente**: el insumo principal debe describir UI. Solicita una fuente UI según [[playwright-greenfield]] (consultar `references/ui-source-priority.md`). Si la intención del usuario es validar el contrato backend o medir performance, deriva a `[[karate-greenfield]]` o `[[k6-greenfield]]`.
4. **Detectar páginas** — Invoca `[[playwright-detect-pages-from-ui-source-prompt]]` con `ui_source_type`, `ui_source_content = ui_source`, `user_story` y `priority_assignments`. Output: lista de páginas con `route` (frontend), `form_fields`, `navigation`, `selectors_hint`, `page_type` y `priority`.
5. **Resolver prioridades faltantes** — Para cada página con `priority: UNKNOWN`, pregunta al usuario/PO antes de continuar. Nunca infieras prioridad desde el nombre.
6. **Detectar flujos de usuario** — Clasifica navegación, formularios, auth, listados/paginación a partir de la UI detectada. Cada flujo mapeará a uno o más `.spec.ts`.
7. **Decidir `mock_mode`** — Pregunta explícita al usuario si no lo declaró:
   - `off` (default) → suite 100% `@live`; no se genera carpeta `mocks/`.
   - `full` → genera mocks y suite `@mocked` además de `@live`.
   - `partial` → genera mocks dirigidos para `mock_endpoints` y suite `@hybrid`.
8. **Planificar tests** — Para cada página: 5-8 escenarios funcionales con tag `@live` por defecto. Marcar visual + a11y en páginas `CRITICAL` y `HIGH`. Aplicar `[[calidad-route-test-generation]]` para mapear flujo UI → test.
9. **Generar Page Objects** — Por cada página, invoca `[[playwright-generate-page-object-prompt]]` siguiendo [[playwright-greenfield]] (consultar `references/page-object-model.md`) + [[playwright-greenfield]] (consultar `references/selector-priority.md`). `navigate()` usa la `route` frontend detectada (anti-patrón rutas inventadas).
10. **Generar mocks (opt-in)** — SOLO si `mock_mode != off`, invoca `[[playwright-generate-mock-handlers-prompt]]` con `endpoints = mock_endpoints` (o derivados del `spec` si se aportó) y `mock_mode`. Sigue [[playwright-greenfield]] (consultar `references/mocks-page-route.md`). Si `mock_mode = off`, **no se crea** la carpeta `mocks/` ni el fixture `mockApi`.
11. **Generar tests** — Emite primero los `tests/*.spec.ts` con tag `@live` por defecto (`[[playwright-greenfield]]` paso 6). Tests que ejerciten error states con mocks llevan `@mocked` o `@hybrid` y declaran `mockApi` en la firma. Para suites de accesibilidad invoca `[[playwright-generate-a11y-prompt]]`; para visual aplica [[playwright-greenfield]] (consultar `references/visual-regression.md`).
12. **Emitir infraestructura** — `playwright.config.ts`, `tsconfig.json`, `package.json`, `.gitignore`, `README.md` según [[playwright-greenfield]] (consultar `references/playwright-config-strict-ts.md`) y [[playwright-greenfield]] (consultar `references/project-structure.md`). Incluir `BASE_URL`, `BACKEND_URL` y projects filtrados por tag (`@live`, `@mocked`, `@hybrid`). Si la UI tiene login real, además `fixtures/auth.setup.ts` y projects con `dependencies: ['setup']` según [[playwright-greenfield]] (consultar `references/auth-storage-state.md`).
13. **Entregar y trazar** — Usa `[[calidad-streaming-files-protocol]]` para la entrega ordenada. Vincula la evidencia con `[[calidad-test-evidence-and-traceability]]`. Documenta los modos en [[playwright-greenfield]] (consultar `references/execution-modes-live-mocked-hybrid.md`) y referencia `[[playwright-run-and-modes]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.**

0. **Smoke gate 1:1 (obligatorio)** — Antes de ejecutar la suite completa, validar que el scaffold corre end-to-end con un solo escenario `@smoke`. Aplicar [[calidad-smoke-gate-policy]] y [[playwright-greenfield]] (consultar `references/smoke-gate-playwright.md`). Comando: `npx playwright test --grep @smoke --project=chromium-live --workers=1 --max-failures=1`. Si falla con exit ≠ 0 → status `partial` con `blocker: "smoke_gate_failed_playwright"` y escalar al usuario; NO continuar a ejecución completa de la suite.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin navegadores instalados, sin red al frontend, sin `BASE_URL` accesible), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` el proyecto correspondiente según `mock_mode` (`npx playwright test --project=live-chromium`, o `mocked-*`/`hybrid-*` cuando aplique). Capturar `playwright-report/`, `test-results/` y traces como evidencia.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky y diagnosticar causa raíz (selector stale, race con red, auth state expirado, bug del SUT, snapshot visual desactualizado).
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` (multi-locator fallback, LLM-driven selector repair, visual AI healing) cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca convertir aserciones de negocio en `toBeVisible()` triviales, ni inflar `timeout` para esconder race conditions reales, ni reemplazar `expect` por `try/catch` silenciosos.
5. Reportar estado final: `success` (todos los tests pasan determinísticamente) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con test, paso fallido, locator, trace, screenshot e hipótesis).
6. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`.

### Paso final — Reporte ejecutivo

Invocar `[[generate-executive-report]]` con `results_path`, `strategy_md_path` y `output_format` (preguntar al usuario o usar default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y se referencia en el `delivery_gate.evidence_persisted.executive_report`. Si modo es `scaffold-only` o `dry-run` → omitir este paso y registrar `null`.

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
- [ ] Tests ejecutados al menos una vez. Estado: `success` / `partial` / `failed` reportado.
- [ ] Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
- [ ] Si hubo correcciones aplicadas (selector repair, healing visual, fixture ajustada): audit log persistido con anti-cheating guardrails verificados.
- [ ] Si el modo es `dry-run` o `scaffold-only`: scaffold + comandos `npx playwright test ...` + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
- [ ] Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@a11y` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra). Aserciones WCAG y reglas axe quedan intocables.
