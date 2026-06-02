---
id: playwright-greenfield
version: 2.0.0
scope: stack
type: skill
chapter: calidad
stack: [playwright]
description: Genera un proyecto Playwright E2E web completo a partir de fuentes UI reales (URL viva, Figma, user stories con flujos UI, Storybook).
tags: [playwright, greenfield, e2e, typescript, page-object-model, ui-first, live-app]
---

# Playwright Greenfield

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto Playwright **desde cero** para automatización E2E web. A diferencia de pruebas de API, Playwright valida la **capa de presentación**, por lo que el insumo principal debe describir la UI, no el contrato backend.

Si el usuario ya cuenta con un proyecto Playwright previo y quiere extender o ajustar selectores, usa `[[playwright-brownfield]]` en su lugar (ver `[[calidad-brownfield-vs-greenfield]]`).

Antes de activar este skill: confirma intent con `[[calidad-intent-detection]]`, recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]` y aplica la perspectiva del chapter con `[[calidad-chapter-perspective]]`.

### Fuentes UI válidas (en orden de preferencia)

1. **URL de aplicación viva** (preferida) — usa Playwright Codegen (`npx playwright codegen URL`), MCP browser tools o un crawler para extraer páginas, selectores reales y navegación. Ver `[[playwright-from-live-app]]`.
2. **Figma, wireframes o mockups UI** — descripciones visuales con jerarquía de componentes, rutas tentativas y form fields.
3. **User stories con flujos UI explícitos** — historias que enumeran páginas, transiciones y acciones (no historias que solo describen reglas de negocio).
4. **Storybook o sistema de diseño existente** — componentes catalogados con sus rutas demo.
## Instrucción

1. **Validar UI source** — Verifica que el insumo describa UI real:
   - Si es URL: que sea accesible y autenticable (si aplica).
   - Si es Figma: link público o screenshots con jerarquía de páginas.
   - Si es user story: que liste páginas y flujos UI explícitos (no solo reglas backend).
   - Si no hay descripción de UI, **detente** y pide una fuente válida según `[ui-source-priority](references/ui-source-priority.md)`.
2. **Detectar páginas** — Invoca `[[playwright-detect-pages-from-ui-source-prompt]]` con `ui_source_type`, `ui_source_content`, `user_story` y `priority_assignments`. Extrae `route` (frontend), `page_type`, `form_fields`, `navigation` y `selectors_hint` directamente desde la fuente UI.
3. **Detectar flujos** — Clasifica los flujos de usuario observados en la UI: navegación entre páginas, formularios multi-paso, autenticación, listados con paginación. Cada flujo se traducirá en uno o más `.spec.ts`.
4. **Decidir modo de ejecución** — Pregunta al usuario: `@live` (default, contra backend real), `@mocked` (opt-in, mocks via `page.route()`) o `@hybrid` (live + mock de endpoints específicos). Ver `[execution-modes-live-mocked-hybrid](references/execution-modes-live-mocked-hybrid.md)`.
5. **Planificar tests** — Para cada página: 5 a 8 escenarios funcionales con tag `@live` por defecto. Para páginas `CRITICAL` y `HIGH` (según `priority_assignments` provistas por el usuario/PO), añade visual regression (`[ver visual](references/visual-regression.md)`) y accesibilidad WCAG 2.1 AA (`[ver a11y](references/accessibility-axe-wcag.md)`).
6. **Emitir archivos en orden de prioridad** — Primero `tests/*.spec.ts`, luego Page Objects, después fixtures, y por último infraestructura (`playwright.config.ts`, `tsconfig.json`, `package.json`, `.gitignore`, `README.md`). Los mocks (`mocks/api-handlers.ts`) se emiten SOLO si el usuario declaró `mock_mode != off` con su lista `mock_endpoints` (ver `[mocks-page-route](references/mocks-page-route.md)` para fuentes válidas y orden de preferencia). Usa `[[calidad-streaming-files-protocol]]` para la entrega.
7. **Validar** — Recorre `[[generate-playwright-greenfield]]` (criterios de finalización) y enlaza la traza según `[[calidad-test-evidence-and-traceability]]`.

## Modo de ejecución

Cada test debe declarar explícitamente su modo de ejecución mediante un tag en el título o en `test.describe`:

- **`@live` (default)** — La suite corre contra el backend real apuntado por `BACKEND_URL` y el frontend en `BASE_URL`. Captura bugs de integración. Es la única forma de validar contratos reales. Es la suite de smoke obligatoria.
- **`@mocked` (opt-in)** — La suite intercepta toda la red con `page.route()` usando los handlers generados en `mocks/api-handlers.ts`. Útil para: aislamiento unitario de UI, regresión de contrato del mock, desarrollo sin backend disponible. **Riesgo**: pasa aunque el backend esté roto.
- **`@hybrid` (opt-in)** — Live por default, pero mock dirigido a endpoints específicos (ej. servicios externos lentos o no disponibles en dev). Útil para reducir flake puntual sin perder cobertura de integración.

El filtrado se hace vía `--grep` en CLI o `grep` por project en `playwright.config.ts`:

```bash
npx playwright test --grep @live      # smoke / CI por defecto
npx playwright test --grep @mocked    # corrida sin backend
npx playwright test --grep @hybrid    # mix
```

Detalle en `[execution-modes-live-mocked-hybrid](references/execution-modes-live-mocked-hybrid.md)`.

## Asignación de prioridad (business-driven)

La prioridad de cada página (`CRITICAL | HIGH | MEDIUM | LOW`) **no se infiere por keyword** (`login` no es automáticamente `CRITICAL`, `profile` no es automáticamente `MEDIUM`). La fuente de verdad es:

1. La user story / criterio de aceptación provisto.
2. El risk assessment del Product Owner.
3. Una pregunta explícita al usuario cuando no exista ninguno de los anteriores.

El prompt `[[playwright-detect-pages-from-ui-source-prompt]]` recibe `priority_assignments` como input externo y NUNCA infiere prioridad desde el nombre de la página.

## Salidas

Estructura de proyecto TypeScript completa (detalle en `[ver estructura](references/project-structure.md)`):

```
{project_name}/
├── package.json
├── playwright.config.ts
├── tsconfig.json
├── .gitignore
├── README.md
├── tests/
│   ├── {resource}.spec.ts          # tag @live por defecto
│   ├── visual.spec.ts
│   └── accessibility.spec.ts
├── pages/
│   ├── NavigationBar.ts
│   ├── {Resource}Page.ts
│   └── {Resource}DetailPage.ts
├── fixtures/
│   ├── base.fixture.ts             # mockApi como fixture opt-in (NO auto)
│   └── auth.setup.ts               # solo si la UI tiene login real
├── mocks/                          # SOLO si el usuario pidió mock_mode
│   ├── api-handlers.ts
│   └── data/
└── utils/
    └── test-data.ts
```

## Restricciones

- **Selectores**: `getByRole`, `getByLabel`, `getByPlaceholder`, `getByText` y selectores semánticos primero. `getByTestId` solo si el HTML real ya lo expone. Nunca XPath salvo último recurso. Detalle en `[selector priority](references/selector-priority.md)`.
- **Rutas**: las rutas en `navigate()` de cada Page Object deben provenir de la fuente UI real (URL crawled, ruta documentada en Figma, definición de router del frontend). **Nunca** inferidas de un path backend. Ver `[POM](references/page-object-model.md)` (anti-patrón rutas inventadas).
- **Auth setup**: generar `fixtures/auth.setup.ts` y configuración `storageState` SOLO si la UI real expone un flujo de login. La existencia de `security` en un OpenAPI **no implica** que la UI tenga LoginPage. Ver `[auth storage state](references/auth-storage-state.md)`.
- **Page Objects**: una clase por página, constructor `(private page: Page)`, propiedades `readonly` para Locators, métodos `async`, sufijo `Page` en el nombre. Ver `[POM](references/page-object-model.md)`.
- **Fixtures**: componer Page Objects con `test.extend<Pages>()`. `mockApi` se declara como fixture **opt-in** (NO `auto`), de modo que cada test elige si quiere mocks. Ver `[fixtures](references/fixtures-composition.md)`.
- **TypeScript strict**: `tsconfig.json` con `strict: true` y path aliases (`@pages/*`, `@fixtures/*`, `@mocks/*`, `@utils/*`). Ver `[config TS](references/playwright-config-strict-ts.md)`.
- **No inventes** páginas, rutas frontend, campos ni selectores que no estén presentes en la fuente UI provista.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]`.
