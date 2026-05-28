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

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Brownfield: la auto-corrección aplica **EXCLUSIVAMENTE** a los Page Objects y `*.spec.ts` recién generados/modificados por este workflow; NUNCA a los tests preexistentes del cliente, aunque fallen (ver `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin navegadores, sin red al frontend), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` filtrado a los specs nuevos/modificados (`npx playwright test tests/<spec>.spec.ts` o por tag de la nueva historia). Capturar `playwright-report/`, traces y screenshots como evidencia.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky y diagnosticar causa raíz. Si un spec preexistente del cliente falla por daño colateral (p. ej. cambio compartido en un Page Object reusado), detenerse y reportar — NO auto-corregir el legado.
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` (multi-locator fallback, LLM-driven selector repair) cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar aserciones de negocio ni inflar timeouts para esconder race conditions. Las correcciones deben preservar las convenciones detectadas (selector strategy, import style, file pattern, page object style).
5. Reportar estado final: `success` | `partial` | `failed` con contexto completo si se escala a humano.
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`.

## Criterios de finalización

- [ ] Objeto de convenciones extraído y documentado en el reporte de salida.
- [ ] Cada archivo nuevo/modificado respeta `selector_strategy`, `import_style`, `test_file_pattern`, `page_object_style` y `path_aliases` del objeto de convenciones.
- [ ] Ningún archivo de infraestructura (`playwright.config.ts`, `tsconfig.json`, `package.json`, `fixtures/base.fixture.ts`) fue modificado.
- [ ] En cambios de selector: métodos, imports, types, comments y signatures de los Page Objects originales permanecen idénticos.
- [ ] No se introdujeron dependencias nuevas sin aprobación explícita.
- [ ] No se introdujo `auth.setup.ts` si no existía y el flujo no lo requiere.
- [ ] Tests nuevos/modificados ejecutados al menos una vez. Estado: `success` / `partial` / `failed` reportado.
- [ ] Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada. Fallos de tests preexistentes del cliente reportados al humano, NO auto-corregidos.
- [ ] Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Auto-corrección sólo tocó archivos generados/modificados por este workflow y respetó las convenciones detectadas.
- [ ] Si el modo es `dry-run` o `scaffold-only`: scaffold + comandos de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
- [ ] Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@a11y` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
