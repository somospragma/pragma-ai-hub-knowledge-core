---
id: update-playwright-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [playwright]
description: Workflow para extender o ajustar un proyecto Playwright existente respetando convenciones detectadas, sin regenerar infraestructura.
tags: [playwright, brownfield, workflow, conventions, selector-update]
---

# Workflow — Actualizar proyecto Playwright brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` clasifica la petición como **automation E2E web** y `[[calidad-brownfield-vs-greenfield]]` determina **brownfield Playwright** (el usuario provee archivos del proyecto existente).

### Pre-flight (OBLIGATORIO)

Antes de cualquier acción, ejecutar `[ver preflight](../../skills/playwright/playwright-greenfield/references/preflight.md)` del stack. En brownfield aplica los mismos checks de versión/tooling. Si falla → degradar a `scaffold-only` con razón documentada.

Cumplir el protocolo `[[calidad-pre-generation-protocol]]` incluso en brownfield: confirmar inputs (incluido `modo`), declarar coverage de los archivos NUEVOS (no de los preexistentes), esperar confirmación del usuario.

### Regla brownfield específica — Auto-corrección

La auto-corrección y self-healing aplican EXCLUSIVAMENTE a los archivos NUEVOS que este workflow genera. Los archivos preexistentes del cliente (tests, Page Objects, fixtures, configs) son INTOCABLES bajo ningún concepto, aunque fallen. Si tests preexistentes fallan en la ejecución:

1. Reportar el fallo al usuario con triage (deterministic vs flaky).
2. NUNCA modificar el test preexistente.
3. NUNCA modificar fixtures, data o configs preexistentes para hacer pasar tests.
4. Escalar a humano con el contexto completo del fallo.

Esta regla es non-negotiable y es enforcement obligatorio del `[[calidad-test-self-correction-loop]]` y sus `references/anti-cheating-guardrails.md`.

Refuerzos adicionales:
- **Step isolation** (ver `[step-isolation-pattern](../../skills/_all/step-isolation-pattern.md)`) aplica a los specs y Page Objects NUEVOS. Los specs preexistentes mantienen su estructura aunque no cumplan el patrón; no se les aplica refactor.
- **Validación contractual no superficial** según `[contractual-checks-from-ui](../../skills/playwright/playwright-greenfield/references/contractual-checks-from-ui.md)` aplica solo a specs nuevos. NO re-escribir aserciones de specs preexistentes.

### Paso previo — Análisis condicional con STRATEGY.md

Si el alcance del brownfield es **grande** (≥3 historias/páginas/flujos nuevos, o cambios cross-cutting que afectan multiple Page Objects preexistentes): generar `STRATEGY.md` según el template `[STRATEGY.md.tpl](../../skills/playwright/playwright-greenfield/references/templates/STRATEGY.md.tpl)` y el skill `[[calidad-pre-design-strategy-document]]`. Esperar aprobación del usuario antes de continuar.

Si el alcance es **pequeño** (1-2 cambios puntuales, p. ej. un selector-update o un único spec nuevo): omitir STRATEGY.md y proceder directo a generación, documentando la decisión en `.evidence/scope-decision.md`.

Respetar convenciones del proyecto cliente: el STRATEGY del brownfield documenta lo NUEVO, no rediseña lo existente.

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
7. **Invocar `[[calidad-post-generation-protocol]]`** para coherence checks post-emisión (find paths, grep de imports cruzados entre fixtures/data/tests nuevos, `npx tsc --noEmit` si modo=full) antes de cerrar.
8. **Smoke gate universal (tests nuevos)**: antes de declarar `success`, ejecutar el smoke gate del stack según [smoke-gate-policy](../../skills/_all/smoke-gate-policy.md). En brownfield Playwright, el gate ejecuta **únicamente los specs nuevos/modificados** filtrados por tag o path: `npx playwright test --grep "@smoke @new" --project=chromium-live --max-failures=1` o filtrado por path del spec recién generado. Los specs preexistentes NO se ejecutan en el gate para no inflar tiempo ni contaminar resultados. Si fallan tests preexistentes al correr la suite completa después, eso NO bloquea la entrega — se reporta como issue separado.
9. **Evidencia de bloqueo de ambiente**: si la ejecución sufre bloqueo de ambiente (WAF/network/auth/rate limit/browser launch failure), emitir `.evidence/execution-status.json` según [environment-blocker-evidence](../../skills/_all/environment-blocker-evidence.md). El estado pasa a `partial` con razón.
10. **Metadata por corrida**: emitir `results/playwright/{date}/{ISO}-metadata.json` según el schema universal [execution-metadata-schema](../../skills/_all/execution-metadata-schema.md). En brownfield, el campo `workload_or_scope` debe distinguir "N specs nuevos sobre M preexistentes".
11. **Reporte ejecutivo**: invocar `[[generate-executive-report]]` para producir reporte consolidado en `.evidence/report-{ISO}.{html|pptx|docx|md}`, usando `playwright-report-template.md`. El reporte debe segregar explícitamente "specs/Page Objects nuevos (en scope de esta sesión)" de "specs preexistentes (referencia, no ejecutados en el gate)".
12. **Emitir el bloque `delivery_gate` yaml** según `[[calidad-delivery-gate-contract]]` con: status declarado coherente con execution, manifest de archivos nuevos/modificados, evidencia (`.evidence/session-config.json`, `.evidence/generation-manifest.json`, execution log + traces si modo=full, `.evidence/execution-status.json` si hubo bloqueo de ambiente, metadata por corrida, reporte ejecutivo, audit log si hubo correcciones), blockers (fallos en specs preexistentes del cliente reportados como blocker con status `partial`, jamás auto-corregidos).

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
