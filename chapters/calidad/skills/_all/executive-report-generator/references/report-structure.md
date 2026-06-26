# Estructura canónica del reporte ejecutivo

El reporte ejecutivo se genera SIEMPRE con las 7 secciones siguientes, en este orden. Aplica a los 4 stacks (Karate, Playwright, K6, Appium). Las plantillas específicas de stack (`karate-report-template.md`, `playwright-report-template.md`, `k6-report-template.md`, `appium-report-template.md`) detallan el contenido por sección.

## 1. Resumen ejecutivo

Estado global con un único badge prominente (verde / amarillo / rojo) y un párrafo (3-5 líneas, español, audiencia stakeholders) que responde:

- ¿La entrega cumple los SLAs declarados?
- ¿Cuántos escenarios pasan vs total?
- ¿Hay bloqueadores que impidan promover a siguiente ambiente?
- ¿Cuál es la recomendación accionable de alto nivel?

Reglas de color:

- **Verde**: 100% de los tests pasan determinísticamente y todos los SLAs declarados se cumplen.
- **Amarillo**: hay fallos no críticos (THRESHOLD_TOO_STRICT, UNKNOWN flaky, ENVIRONMENT_BLOCKED sin impacto en SUT) o SLAs incumplidos no críticos. La entrega es promovible con observaciones.
- **Rojo**: hay al menos un SUT_BUG confirmado, o un SLA crítico incumplido, o más del 20% de los tests fallan determinísticamente.

Si no hay `STRATEGY.md`, el badge se marca como **amarillo: parcial — sin SLAs declarados** y se documenta en el párrafo.

## 2. Cumplimiento de SLAs

Tabla con todos los SLAs declarados en `STRATEGY.md` versus lo observado. Cada fila es un SLA:

| SLA | Declarado | Observado | Cumple |
|---|---|---|---|
| p95 latencia GET /pets | < 800 ms | 742 ms | OK |
| Error rate global | < 1% | 1.8% | FAIL |
| Disponibilidad smoke | 100% | 100% | OK |

Convención: `OK` para cumplido, `FAIL` para incumplido, `N/A` para no aplica, `no medido` para sin evidencia. En la conversión a HTML, `OK` se renderiza con badge verde y `FAIL` con badge rojo (ver ``references/templates.md` (sección `report.html-style.css`)`).

Si un SLA es no aplicable al stack actual (p. ej. latencia p95 en Appium), marcar `N/A`. Si un SLA no fue medido por falta de evidencia, marcar `no medido` (NO inferir). Esta sección se omite si no hay `STRATEGY.md` y se sustituye por nota de "sección omitida — STRATEGY.md ausente".

## 3. Resultados por escenario / HU / feature

Tabla agrupada según el stack:

- Karate: por feature y por endpoint (ver `karate-report-template.md`).
- Playwright: por HU (`@user-story:HUT-XXX`) y por página (ver `playwright-report-template.md`).
- K6: por escenario (smoke / load / stress / spike / soak) y por endpoint (ver `k6-report-template.md`).
- Appium: por feature y por device (ver `appium-report-template.md`).

Columnas mínimas: nombre, total, pasados, fallidos, % éxito, duración, estado (verde/amarillo/rojo). Filas ordenadas por prioridad (CRITICAL primero) y luego por % de éxito ascendente.

## 4. Comparación entre corridas

Solo si existe N>1 carpetas timestamp bajo `results/<stack>/`. Tabla delta entre última corrida y la penúltima:

| Métrica | Corrida anterior | Corrida actual | Delta |
|---|---|---|---|
| % éxito global | 87% | 92% | +5 pp |
| Tests pasados | 24/28 | 26/28 | +2 |
| p95 GET /pets | 921 ms | 742 ms | -179 ms |

Subsección de movimientos cualitativos:

- **Recuperados** (rojo a verde): lista de tests que estaban fallando y ahora pasan.
- **Regresiones** (verde a rojo): lista de tests que pasaban y ahora fallan. Las regresiones siempre se destacan en rojo y son el primer foco de las recomendaciones.
- **Nuevos** y **eliminados**: tests añadidos o removidos respecto a la corrida anterior.

Si solo hay 1 corrida, omitir esta sección con la nota literal "primera corrida — no hay baseline".

## 5. Hallazgos clasificados

Listado de fallos. Cada hallazgo incluye:

- **Identificador**: nombre del test / scenario / feature.
- **Clasificación**: una de `SUT_BUG | THRESHOLD_TOO_STRICT | ENVIRONMENT_BLOCKED | TEST_DESIGN_ISSUE | DATA_ISSUE | UNKNOWN` (ver `failure-classification-rules.md`).
- **Causa raíz sugerida** (1-2 líneas en español, audiencia técnica).
- **Evidencia**: ruta a screenshot / trace / stack trace / status code / métrica K6. Sin evidencia no se clasifica: se marca `UNKNOWN`.
- **Severidad**: CRITICAL / HIGH / MEDIUM / LOW (deriva de la prioridad del test y la naturaleza de la clasificación).

Ordenar por severidad descendente y luego por clasificación (los `SUT_BUG` primero).

## 6. Recomendaciones por rol

Bloque agrupado por rol con acciones concretas, accionables y verificables. Cada acción incluye el hallazgo origen.

- **Dev** (SUT_BUG, TEST_DESIGN_ISSUE que revela ambigüedad del contrato): corregir lógica, ajustar contrato, documentar comportamiento esperado.
- **Infra** (ENVIRONMENT_BLOCKED): desbloquear WAF, ampliar rate limits, abrir red, renovar certificados.
- **QA** (TEST_DESIGN_ISSUE, UNKNOWN flaky): ajustar locator, repensar fixture, agregar `retry` controlado, programar ejecución repetida para caracterizar flakiness.
- **PO** (cobertura insuficiente, HUs sin escenarios): priorizar nuevas HUs, aprobar deferred scope, validar criterios de aceptación.

Si una categoría no tiene recomendaciones, omitirla con nota explícita "sin acciones para <rol>".

## 7. Anexos

Material de respaldo, sin interpretación:

- Comandos exactos ejecutados (`mvn test ...`, `npx playwright test ...`, `k6 run ...`, `./gradlew test ...`).
- Listado de archivos de evidencia (paths relativos).
- Versiones de herramientas (`metadata.json` de la corrida).
- Configuración resumida (`STRATEGY.md` referenciado, no embebido).
- Links a reportes técnicos nativos (Karate HTML, Playwright report, K6 summary JSON, Serenity).
