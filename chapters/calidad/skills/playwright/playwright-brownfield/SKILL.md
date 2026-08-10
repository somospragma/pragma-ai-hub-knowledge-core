---
id: calidad-playwright-brownfield
version: 2.0.0
scope: stack
type: skill
chapter: calidad
stack: [playwright]
description: Extiende o ajusta un proyecto Playwright existente respetando sus convenciones; valida selectores contra la UI real (no contra el spec) y nunca regenera infraestructura.
tags: [playwright, brownfield, conventions, selector-update, page-object-model, ui-first]
---

# Playwright Brownfield

## Cuándo aplicar

Cuando ya existe un proyecto Playwright en el repo del usuario y se quiere extenderlo o ajustarlo. El disparador es la **presencia de infraestructura Playwright previa** (`playwright.config.ts`, `tests/`, `pages/`, fixtures), no la existencia de un spec backend.

Casos típicos:

- Actualizar selectores tras cambios de UI (nuevos labels, reorganización de formularios, rediseño de un componente).
- Agregar tests/Page Objects para nuevas pantallas o flujos UI, respetando el estilo ya presente.
- Cubrir nuevos endpoints backend con tests E2E: los endpoints solo se usan para **mocks opt-in** según el modo `@mocked` / `@hybrid` documentado en `[[calidad-playwright-greenfield]]`; las páginas se siguen derivando de la UI real.

Si el proyecto Playwright no existe todavía, usa `[[calidad-playwright-greenfield]]` (ver `[[calidad-brownfield-vs-greenfield]]`). Si existe pero falta una fuente UI confiable y la app está corriendo, complementa con `[[calidad-playwright-from-live-app]]`.

Antes de activar este skill: confirma intent con `[[calidad-intent-detection]]` y recolecta inputs con `[[calidad-mandatory-inputs-protocol]]`.

## Lectura obligatoria antes de tocar el proyecto

El conocimiento técnico del stack vive en el bundle **greenfield** del mismo stack; brownfield no lo duplica, lo consume. **Abrir antes de generar** y declarar cuáles se leyeron (traza en `[[calidad-pipeline-state-tracking]]`):

| Reference | Para qué |
|---|---|
| [[calidad-playwright-greenfield]] (`references/selector-priority.md`) | Orden de selectores y prohibiciones |
| [[calidad-playwright-greenfield]] (`references/execution-modes-live-mocked-hybrid.md`) | @live/@mocked/@hybrid y qué valida cada modo |
| [[calidad-playwright-greenfield]] (`references/waits-policy.md`) | Política de esperas |
| `references/convention-detection.md` · `references/selector-update-strategy.md` | Convenciones del proyecto (propias de este skill) |

**Cómo se aplica en brownfield**: estas references aportan el **conocimiento técnico** (cómo resolver un locator, cómo interactuar, cómo diagnosticar). Las **convenciones del proyecto del cliente siempre mandan** sobre las del chapter (naming, tags, idioma, estilo, versiones). Nunca se importan las convenciones del greenfield a un proyecto existente.

**Diagnóstico sin imposición**: si al analizar el proyecto detectas un defecto conocido del chapter (p. ej. `OnlineCast` disparando ChromeDriver, runner con tags hardcodeados que anulan el filtro de CLI, falta de `SerenityReporter` en `cucumber.plugin`, imports legacy de Serenity 3.x), **repórtalo al usuario con su evidencia y el fix sugerido — no lo apliques por tu cuenta**. Corregirlo sin permiso viola la regla de no tocar infraestructura ajena; callarlo deja al cliente con un falso verde que ya conocemos.

## Instrucción

1. **Analizar proyecto existente** — Recorre el árbol entregado por el usuario: `playwright.config.ts`, `tsconfig.json`, `package.json`, `tests/`, `pages/`, `fixtures/`, `mocks/`. Identifica archivos representativos de cada categoría y el modo de ejecución actual (`@live` / `@mocked` / `@hybrid` si aplica).
2. **Detectar convenciones** — Aplica ``references/convention-detection.md`` para extraer: `tests_dir`, `pages_dir`, `fixtures_dir`, `test_file_pattern`, `page_object_style`, `selector_strategy`, `import_style`, `path_aliases`, `base_url`, `auth_pattern`, `execution_mode_default`, `existing_page_objects[]`, `existing_tests[]`, `existing_fixtures[]`.
3. **Validar contra UI real** — Para cualquier selector que vayas a modificar o crear, valida contra **la aplicación corriendo (live URL) o screenshots/Figma actualizados** provistos por el usuario. Si no hay forma de ver la UI, detente y pide la fuente UI (ver `[ui-source-priority](../playwright-greenfield/references/ui-source-priority.md)`).
4. **Actualizar selectores manteniendo métodos** — Si hubo cambio UI, aplica ``references/selector-update-strategy.md``: reemplaza ÚNICAMENTE las asignaciones de Locator usando la `selector_strategy` ya detectada en el proyecto. Métodos, types, imports, comments y signatures se preservan literal.
5. **Generar nuevos tests con mismo estilo** — Para tests/Page Objects nuevos, copia exactamente: convención de nombres, estilo de import (alias vs relativo), patrón de fixtures, naming de métodos, granularidad de pasos, tag de ejecución por defecto del proyecto. No introducir patrones nuevos.
6. **Mocks solo opt-in** — Si la feature requiere cubrir un endpoint backend nuevo, materialízalo como handler bajo `@mocked` o `@hybrid` siguiendo `[execution-modes](../playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`. No conviertas la suite existente a mocked por defecto.
7. **Validar coherencia** — Antes de entregar: verificar que cada nuevo archivo respeta la convención detectada en el paso 2. Si el proyecto usa selectores semánticos, no introducir `data-testid` ni CSS frágil; si usa relative imports, no introducir alias.

## Restricciones

- **NO regenerar** `package.json`, `playwright.config.ts`, `tsconfig.json`, `fixtures/base.fixture.ts`, ni cualquier archivo de infraestructura existente.
- **Las páginas y selectores se derivan exclusivamente de la UI real** (live URL, Figma, screenshots, Storybook). Ver `[ui-source-priority](../playwright-greenfield/references/ui-source-priority.md)`.
- **NO asumir** equivalencia entre endpoints backend y rutas frontend; un endpoint puede no tener pantalla y una pantalla puede consumir varios endpoints.
- **Respetar Page Objects existentes** y su `selector_strategy` detectada: si el proyecto usa `getByRole`, los nuevos POM siguen `getByRole`; si usa `data-testid`, idem.
- **Preservar TODO el código no-selector**: métodos, imports, types, comments, signatures, decoradores, orden de propiedades.
- **No subir versiones** de dependencias salvo solicitud explícita del usuario.
- **No agregar dependencias** nuevas salvo que el feature lo requiera y el usuario lo apruebe.
- Si el proyecto no tiene `auth.setup.ts` y el nuevo flujo no requiere login real en browser, no introducirlo (ver `[auth-storage-state](../playwright-greenfield/references/auth-storage-state.md)`).
- Entrega los archivos modificados/nuevos usando `[[calidad-streaming-files-protocol]]`.

## Cross-links

- Fuente UI obligatoria: `[ui-source-priority](../playwright-greenfield/references/ui-source-priority.md)`
- Modos de ejecución (live / mocked / hybrid): `[execution-modes-live-mocked-hybrid](../playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`
- Page Object Model: `[page-object-model](../playwright-greenfield/references/page-object-model.md)`
- Prioridad de selectores: `[selector-priority](../playwright-greenfield/references/selector-priority.md)`
- Auth en browser: `[auth-storage-state](../playwright-greenfield/references/auth-storage-state.md)`
- Cuando la app está viva y conviene re-explorar: `[[calidad-playwright-from-live-app]]`
