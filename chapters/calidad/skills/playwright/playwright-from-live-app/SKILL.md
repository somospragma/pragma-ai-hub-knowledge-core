---
id: calidad-playwright-from-live-app
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [playwright]
description: Genera un proyecto Playwright explorando una aplicación web viva con Playwright Codegen o MCP browser tools, sin depender de spec ni mockups. Extrae páginas, selectores reales y navegación directamente del DOM.
tags: [playwright, live-app, codegen, mcp, ui-first, exploration]
---

# Playwright desde aplicación viva

## Cuándo aplicar

Cuando el usuario quiere generar un proyecto Playwright y:

- La aplicación está accesible vía URL (dev/staging/prod).
- No hay Figma actualizado ni Storybook publicado.
- Se desea capturar selectores reales del DOM, no inferidos.

Es el camino preferido cuando existe una URL viva: produce selectores precisos y rutas frontend reales. Es el complemento natural de `[[calidad-playwright-greenfield]]` para la fuente UI tipo `live-url`.

Antes de activar: confirma intent con `[[calidad-intent-detection]]` y recolecta inputs con `[[calidad-mandatory-inputs-protocol]]`.

## Instrucción

1. **Validar acceso** — Verifica que `base_url` responda (HTTP 200 / 302 a login). Si hay autenticación, recolecta credenciales o `storageState` y aplica `[ver auth](../playwright-greenfield/references/auth-storage-state.md)`.
2. **Elegir herramienta de extracción**:
   - **Playwright Codegen** (`npx playwright codegen {base_url}`) — interactivo; el QA navega la app y Codegen emite selectores y acciones.
   - **MCP browser tools** — si el LLM tiene capacidad de browser, navegar la app y capturar `getByRole` / `getByLabel` / `getByTestId` programáticamente.
   - **Crawler headless** — para apps grandes, ejecutar un script que visite rutas conocidas y extraiga estructura.
3. **Explorar flujos provistos** — Para cada `flow` declarado en `flows_to_explore`, navegar la app y registrar: rutas visitadas, headings, form fields, botones de acción, transiciones, errores observados.
4. **Extraer páginas** — Invoca `[[calidad-playwright-extract-pages-from-live-app-prompt]]` con `base_url`, `auth_credentials` y `flows_to_explore`. Output: JSON con páginas, selectores reales con estrategia `getByTestId > getByRole > getByLabel > getByText`, navegación, form fields.
5. **Validar selectores** — Para cada selector emitido, validar que sea único y estable (no clases generadas, no índices de hijos frágiles). Preferir `getByTestId` si el DOM expone `data-testid`; degradar a `getByRole` con `name`.
6. **Generar POM + tests** — Aplica `[POM](../playwright-greenfield/references/page-object-model.md)` (usando `route` frontend reales) y `[selector-priority](../playwright-greenfield/references/selector-priority.md)`. Por defecto los tests llevan tag `@live` — ver `[execution-modes](../playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`.
7. **Continuar con el workflow** — Delega el resto del proyecto (fixtures, config, README) a `[[calidad-generate-playwright-greenfield]]` con `ui_source_type: live-url` y el JSON de páginas extraído como `ui_source`.

## Inputs mínimos

| Input               | Obligatorio | Descripción                                             |
|---------------------|-------------|---------------------------------------------------------|
| `base_url`          | sí          | URL de la app viva.                                     |
| `flows_to_explore`  | sí          | Lista de user stories / flujos UI a navegar.            |
| `auth_credentials`  | no          | Credenciales si la app exige login.                     |
| `priority_assignments` | no       | Mapa `pageName -> priority` provisto por PO.            |

## Salidas

- JSON estructurado con páginas detectadas (mismo formato que `[[calidad-playwright-detect-pages-from-ui-source-prompt]]`).
- Snippets de Codegen capturados (opcional, para evidencia).
- Recomendaciones de testids faltantes (cuando los selectores caen a estrategias frágiles).

## Restricciones

- **No inventes** flujos no declarados en `flows_to_explore`. Si la exploración detecta páginas adicionales, repórtalas como "discovered, no test plan" para que el usuario decida.
- **Selectores**: prioridad `getByTestId > getByRole > getByLabel > getByText`. Si solo aplican selectores CSS frágiles, marca la página con `needs_testid: true` y deja un TODO en el POM.
- **No mockear** durante la exploración: el objetivo es capturar el DOM real.
- **Rutas frontend**: registrar las que aparecen en `window.location` durante la navegación; no traducir desde paths backend.

## Relación con otros skills

- Si la aplicación viva **ya tiene un proyecto Playwright** en el repo (con `playwright.config.ts`, `tests/`, `pages/`), no generes uno nuevo: usa `[[calidad-playwright-brownfield]]` para extenderlo, y aprovecha la exploración descrita aquí únicamente para **validar selectores actuales contra el DOM real** antes de modificar Page Objects.
- Si no existe proyecto Playwright y la app está viva, este skill es el camino preferido y luego delega la materialización a `[[calidad-generate-playwright-greenfield]]` / `[[calidad-playwright-greenfield]]`.

## Cross-links

- Fuente UI: `[ui-source-priority](../playwright-greenfield/references/ui-source-priority.md)`
- POM: `[page-object-model](../playwright-greenfield/references/page-object-model.md)`
- Selectores: `[selector-priority](../playwright-greenfield/references/selector-priority.md)`
- Modos de corrida: `[execution-modes-live-mocked-hybrid](../playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`
- Extender proyecto existente: `[[calidad-playwright-brownfield]]`
- Continuación: `[[calidad-generate-playwright-greenfield]]`, `[[calidad-playwright-greenfield]]`
- Prompt asociado: `[[calidad-playwright-extract-pages-from-live-app-prompt]]`
