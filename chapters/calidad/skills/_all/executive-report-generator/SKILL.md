---
id: calidad-executive-report-generator
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
enforcement: mandatory
description: "OBLIGATORIO. Post-procesa los outputs técnicos de los stacks del chapter (Karate/Playwright/K6/Appium Serenity/Appium WebdriverIO/serenity-wdio) y genera un reporte ejecutivo consolidado en Markdown convertible a HTML/PPTX/DOC con narrativa, comparación entre corridas, cumplimiento de SLAs y recomendaciones para stakeholders."
tags: [executive-report, post-processing, stakeholders, html, pptx, doc, pandoc, narrative, mandatory, serenity-wdio]
verification:
  - check: "Lee múltiples corridas en results/ y produce 1 reporte consolidado"
    failure_message: "Bloqueado: sin reporte ejecutivo la entrega no es presentable a stakeholders"
  - check: "Identifica clasificación de fallos: SUT bug | threshold issue | env blocker | test design"
    failure_message: "Bloqueado: el reporte debe incluir root cause sugerido por fallo"
  - check: "Reporta cumplimiento de SLAs declarados en STRATEGY.md"
    failure_message: "Bloqueado: el reporte debe contrastar resultados vs SLAs declarados"
---

# Executive Report Generator — Reporte Ejecutivo Post-Corrida Universal

## Cuándo aplicar

Aplica este skill al final de toda generación de tests (todos los workflows greenfield y brownfield de los 5 stacks: Karate, Playwright, K6, Appium, serenity-wdio), una vez que la suite ha sido ejecutada (modo `full` o `execute-only`). En modo `scaffold-only` o `dry-run` no aplica, porque no hay outputs de ejecución que post-procesar.

El skill convierte los JSON, XML y reportes técnicos de cada stack en un informe ejecutivo presentable: un documento con narrativa en español, tablas de cumplimiento de SLAs, comparación entre corridas, fallos clasificados con causa raíz sugerida y recomendaciones concretas por rol (Dev / Infra / QA / PO).

Es invocado por el workflow `[[calidad-generate-executive-report]]` como último paso del ciclo de entrega.

## Instrucción

Sigue los 7 pasos en orden estricto. Cada paso produce un artefacto intermedio que el siguiente consume.

### Paso 1 — Leer outputs técnicos según stack

Localiza y parsea los outputs primarios. La estructura exacta depende del stack:

- **Karate**: `results/karate/<timestamp>/karate-summary.json` + `metadata.json` + JUnit XML (`results/karate/<timestamp>/junit/*.xml`). Ver `references/karate-report-template.md`.
- **Playwright**: `results/playwright/<timestamp>/results.json` + `metadata.json` + reporte HTML (`playwright-report/index.html`) + traces. Ver `references/playwright-report-template.md`.
- **K6**: `results/<scenario>/<timestamp>/summary.json` + `metadata.json` por cada escenario ejecutado (smoke, load, stress, spike, soak). Ver `references/k6-report-template.md`.
- **Appium**: `results/appium/<timestamp>/serenity-results/` (JSON agregado de Serenity) + `metadata.json` + screenshots Serenity. Ver `references/appium-report-template.md`.
- **serenity-wdio**: `results/serenity-wdio/<timestamp>/` con Allure results (`allure-results/`), Serenity BDD report (`serenity/`), Cucumber JSON (`cucumber/`), video (modo web) y `metadata.json`. Ver `references/serenity-wdio-report-template.md`.

Si una corrida no tiene `metadata.json` (timestamp, commit, branch, environment), reportar como `corrida con metadata incompleta` en el reporte y continuar.

### Paso 2 — Leer STRATEGY.md del proyecto

Buscar `STRATEGY.md` en la raíz del proyecto (generado por la oleada previa de planning). Extraer:

- SLAs declarados por escenario / HU / endpoint (latencia p95/p99, error rate, disponibilidad, throughput).
- Criterios de aceptación por funcionalidad.
- Umbrales de cobertura mínima por endpoint / página / feature.

Si no existe `STRATEGY.md` → el reporte se genera sin sección "Cumplimiento de SLAs" y se marca como **parcial** en el resumen ejecutivo, con advertencia visible.

### Paso 3 — Consolidar métricas por escenario / feature / HU

Agrupar resultados por unidad funcional según el stack:

- Karate: por feature y por endpoint.
- Playwright: por HU (tag `@user-story:HUT-XXX`) y por página.
- K6: por escenario K6 (smoke, load, stress, spike, soak) y por endpoint.
- Appium: por feature y por device matrix.
- serenity-wdio: por canal (`@web`, `@mobile`, `@api`) y por HU (tag `@user-story:HUT-XXX`); si hay múltiples modos ejecutados (`web`, `movil`, `api`), consolidar por canal primero y luego por HU.

Calcular: pasados / totales, % éxito, duración, número de fallos.

### Paso 4 — Comparar entre corridas

Si existen N>1 carpetas timestamp bajo `results/<stack>/`, comparar la última con la penúltima:

- Cambio en % éxito (delta absoluto + %).
- Cambio en latencias (solo K6 y Playwright performance).
- Tests nuevos, eliminados, recuperados (estaban rojos, ahora verdes), regredidos (estaban verdes, ahora rojos).

Si solo existe 1 corrida → omitir la sección "Comparación entre corridas" y anotar "primera corrida — no hay baseline".

### Paso 5 — Clasificar fallos con root cause sugerido

Para cada fallo determinístico (ver `[[calidad-failure-triage-and-classification]]`), aplicar las reglas de `references/failure-classification-rules.md` y asignar una de:

- `SUT_BUG` — bug real del sistema bajo prueba (status code consistente distinto al esperado, lógica de negocio rota).
- `THRESHOLD_TOO_STRICT` — el threshold declarado es irreal para el ambiente actual (típico K6 inicial).
- `ENVIRONMENT_BLOCKED` — bloqueo de infraestructura (WAF 403, conectividad, TLS, certificados).
- `TEST_DESIGN_ISSUE` — error en el test (locator stale, payload mal construido, fixture mal cargada).
- `DATA_ISSUE` — estado de datos inconsistente (registros previos no limpiados, IDs colisionando).
- `UNKNOWN` — flaky sin patrón claro tras N=3 re-runs.

NUNCA clasificar sin evidencia explícita (status code, stack trace, screenshot, métrica). Si la evidencia no alcanza, marcar `UNKNOWN` y escalar a humano.

### Paso 6 — Generar reporte Markdown desde plantilla

Renderizar ``references/templates.md` (sección `report.md`)` rellenando los slots `{{summary}}`, `{{slas_table}}`, `{{scenarios_table}}`, `{{runs_comparison_table}}`, `{{findings}}`, `{{recommendations}}`, `{{annexes}}`. La estructura canónica está en `references/report-structure.md`. Usar la plantilla específica del stack para las secciones "Resultados por escenario" y "Anexos":

- Karate → `references/karate-report-template.md`.
- Playwright → `references/playwright-report-template.md`.
- K6 → `references/k6-report-template.md`.
- Appium → `references/appium-report-template.md`.
- serenity-wdio → `references/serenity-wdio-report-template.md`.

### Paso 7 — Convertir a formato final

Según `output_format` solicitado:

- `html` (default) — `pandoc report.md -o report.html --standalone --self-contained --css=report.html-style.css`.
- `pptx` — `pandoc report.md -o report.pptx`.
- `doc` — `pandoc report.md -o report.docx --reference-doc=template.docx`.
- `md` — emitir directamente sin conversión.

Si `pandoc` no está disponible en el ambiente del agente: emitir solo el `.md` y documentar el comando exacto de conversión manual en el mensaje al usuario.

Persistir el resultado en `.evidence/report-{ISO}.{ext}`.

## Restricciones

- **NUNCA** inventar métricas no presentes en los outputs técnicos. Si una métrica falta, el reporte dice "no reportada" explícitamente; no se interpola ni se infiere.
- **NUNCA** clasificar fallos sin evidencia concreta (status code, stack trace, screenshot, métrica de K6). Sin evidencia → `UNKNOWN` con nota para escalar.
- **NUNCA** modificar los outputs técnicos originales: el reporte es read-only sobre `results/`.
- Si no hay `STRATEGY.md` → reportar sin comparación vs SLAs y marcar el resumen ejecutivo como **parcial**. No inventar SLAs por defecto.
- Si no hay corridas previas → omitir sección "Comparación" y anotar "primera corrida — no hay baseline".
- El reporte debe estar en español (audiencia stakeholders) salvo nombres técnicos (test IDs, endpoints, métricas K6) que se preservan tal cual.
- Cross-link obligatorio a `[[calidad-failure-triage-and-classification]]` para utilizar el catálogo de patrones de fallo como insumo de la clasificación.

## Verificación

Asset de **cumplimiento obligatorio**. Antes de cerrar la fase que lo invoca, comprobar cada punto. Si alguno no se cumple, se detiene y se reporta con el mensaje indicado.

| # | Comprobación | Si no se cumple |
|---|---|---|
| 1 | Lee múltiples corridas en results/ y produce 1 reporte consolidado | Bloqueado: sin reporte ejecutivo la entrega no es presentable a stakeholders |
| 2 | Identifica clasificación de fallos: SUT bug | threshold issue | env blocker | test design | Bloqueado: el reporte debe incluir root cause sugerido por fallo |
| 3 | Reporta cumplimiento de SLAs declarados en STRATEGY.md | Bloqueado: el reporte debe contrastar resultados vs SLAs declarados |

## Cross-links

References específicas del skill:

- `references/report-structure.md`
- `references/failure-classification-rules.md`
- `references/karate-report-template.md`
- `references/playwright-report-template.md`
- `references/k6-report-template.md`
- `references/appium-report-template.md`
- `references/serenity-wdio-report-template.md`
- ``references/templates.md` (sección `report.md`)`
- ``references/templates.md` (sección `report.html-style.css`)`

Otros assets del chapter:

- `[[calidad-failure-triage-and-classification]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-delivery-gate-contract]]`
- `[[calidad-generate-executive-report]]`
