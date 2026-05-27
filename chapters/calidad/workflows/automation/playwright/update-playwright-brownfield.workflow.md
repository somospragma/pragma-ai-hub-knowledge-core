---
id: update-playwright-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Workflow para extender o ajustar un proyecto Playwright existente respetando convenciones detectadas, sin regenerar infraestructura.
tags: [playwright, brownfield, workflow, conventions, selector-update]
---

# Workflow — Actualizar proyecto Playwright brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica la petición como **automation E2E web** y `[[calidad-brownfield-vs-greenfield]]` determina **brownfield Playwright** (el usuario provee archivos del proyecto existente).

## Inputs

| Input                | Obligatorio | Descripción                                                                     |
|----------------------|-------------|---------------------------------------------------------------------------------|
| `project_files`      | sí          | Archivos relevantes: `playwright.config.ts`, `tsconfig.json`, `package.json`, muestra de `pages/`, `fixtures/`, `tests/` |
| `change_request`     | sí          | Uno de: (a) cambios UI (screenshot, nuevos labels), (b) nuevos endpoints/páginas (spec parcial) |
| `affected_pages`     | no          | Lista explícita de páginas afectadas, si el usuario la provee                   |

Recolección según `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

1. **Analizar proyecto existente** — Recorre los archivos entregados. Identifica `tests/`, `pages/`, `fixtures/`, `mocks/`.
2. **Extraer convenciones** — Aplica `[[playwright-convention-detection]]` para producir el objeto de convenciones. Output mandatorio antes de generar nada.
3. **Aplicar selector-update si la UI cambió** — Si `change_request` es de tipo (a), aplica `[[playwright-selector-update-strategy]]` página por página. Solo cambian las cadenas dentro de los `getBy*`. Preservar TODO lo demás.
4. **Generar nuevos tests con mismo estilo** — Si `change_request` es de tipo (b), invoca `[[playwright-brownfield]]` paso 4: copia exactamente el estilo de imports, naming, fixtures y granularidad de los specs existentes.
5. **Validar coherencia** — Recorre cada archivo nuevo/modificado y verifica que respeta cada campo del objeto de convenciones (selector strategy, import style, file pattern, page object style).
6. **Entregar SIN regenerar infraestructura** — Usa `[[calidad-streaming-files-protocol]]` para entregar exclusivamente los archivos cambiados o nuevos. No emitir `playwright.config.ts`, `tsconfig.json`, `package.json` ni `fixtures/base.fixture.ts` salvo que el usuario lo pida explícitamente.

## Criterios de finalización

- [ ] Objeto de convenciones extraído y documentado en el reporte de salida.
- [ ] Cada archivo nuevo/modificado respeta `selector_strategy`, `import_style`, `test_file_pattern`, `page_object_style` y `path_aliases` del objeto de convenciones.
- [ ] Ningún archivo de infraestructura (`playwright.config.ts`, `tsconfig.json`, `package.json`, `fixtures/base.fixture.ts`) fue modificado.
- [ ] En cambios de selector: métodos, imports, types, comments y signatures de los Page Objects originales permanecen idénticos.
- [ ] No se introdujeron dependencias nuevas sin aprobación explícita.
- [ ] No se introdujo `auth.setup.ts` si no existía y el flujo no lo requiere.
