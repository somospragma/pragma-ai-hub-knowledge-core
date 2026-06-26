# Reglas de clasificación de fallos

Estas reglas son determinísticas: dada la evidencia disponible (status code, stack trace, screenshot, métrica K6, logs), la clasificación debe ser reproducible entre corridas. Sin evidencia concreta, la clasificación es `UNKNOWN` y el caso se escala a humano. Este documento alimenta el Paso 5 de `SKILL.md` y debe usarse junto a `[[calidad-failure-triage-and-classification]]`.

## Tabla síntomas a clasificación

| Síntoma observable | Clasificación | Heurística |
|---|---|---|
| Status code distinto al esperado, consistente entre N re-runs, response body coherente con un bug de negocio (campo faltante, total mal calculado) | `SUT_BUG` | El SUT responde rápido y de forma reproducible, pero el valor es incorrecto. NO es problema del test ni del ambiente. |
| Body o headers diferentes al contrato declarado en el spec OpenAPI y consistente | `SUT_BUG` | Drift de contrato del SUT respecto al spec aprobado. |
| K6: p95 incumplido pero p50 dentro del SLA, error rate < 1%, ningún 5xx | `THRESHOLD_TOO_STRICT` | El SUT responde correctamente; el SLA p95 inicial era irreal para el ambiente. Calibrar con `[[calidad-calibrate-k6-thresholds]]`. |
| Status 403 con headers tipo `X-Permitted-Cross-Domain-Policies`, `Server: cloudfront`, `cf-mitigated`, `incap_ses_*`, body con captcha o página HTML | `ENVIRONMENT_BLOCKED` | WAF / CDN intercepta. NO es bug del SUT ni del test. |
| Timeouts de red consistentes, DNS no resuelve, TLS handshake falla, certificado expirado | `ENVIRONMENT_BLOCKED` | Infraestructura. Escalar a Infra. |
| Status 429 sostenido | `ENVIRONMENT_BLOCKED` (rate limit). Si el test es K6 con carga real planificada, puede ser `SUT_BUG` (rate limit mal dimensionado) — diferenciar por el SLA declarado en STRATEGY.md. |
| Playwright/Appium: locator no encontrado, `TimeoutError: locator.click`, screenshot muestra UI presente pero con DOM distinto | `TEST_DESIGN_ISSUE` | Selector stale: el SUT cambió el DOM (ej. id renombrado). El SUT funciona, el test apunta a algo viejo. |
| Karate: payload mal construido, `path is not defined`, `feature script failed` por sintaxis del feature | `TEST_DESIGN_ISSUE` | El bug está en el `.feature`. |
| Aserción falla porque el dato esperado no existe (lookup de id que ya fue borrado por un test previo, secuencia rota) | `DATA_ISSUE` | Estado inconsistente entre tests. Resolver con fixtures aisladas. |
| Status 409 / 422 en POST por colisión de unique constraint que el test no limpió | `DATA_ISSUE` | Test data setup/teardown incompleto. |
| Fallo intermitente: pasa en N=1, falla en N=2, pasa en N=3, sin patrón en evidencia | `UNKNOWN` | Flaky sin causa raíz aislable. Marcar para investigación. NUNCA forzar verde. |
| No hay evidencia adjunta (sin screenshot, sin stack trace, sin status code en log) | `UNKNOWN` | Sin evidencia no se clasifica. Escalar. |

## Heurísticas clave: SUT_BUG vs TEST_DESIGN_ISSUE

La diferencia es crítica porque la acción correctiva va a roles distintos (Dev vs QA). Aplicar estas heurísticas antes de clasificar:

1. **¿El comportamiento es reproducible en cliente manual (curl, Postman, navegador, Appium Inspector)?**
   - Si reproduce manualmente con el mismo input: `SUT_BUG`.
   - Si manualmente funciona y solo el test falla: `TEST_DESIGN_ISSUE`.

2. **¿El test usa un contrato (OpenAPI / firma / spec) que el SUT no cumple?**
   - Si el spec dice `status: 201` y el SUT devuelve `200` consistentemente: `SUT_BUG` (drift de contrato). El test refleja el spec, el SUT no.
   - Si el spec dice `status: 200` y el test esperaba `201` por error de quien escribió el test: `TEST_DESIGN_ISSUE`.

3. **¿La aserción evalúa significado de negocio o solo estructura?**
   - Aserción de negocio fallida (total != suma de items, fecha inválida): tiende a `SUT_BUG`.
   - Aserción estructural fallida con response semánticamente correcta: tiende a `TEST_DESIGN_ISSUE` (contrato mal asumido).

4. **¿Cambió el DOM/contrato recientemente?**
   - Sí + el test no se actualizó: `TEST_DESIGN_ISSUE` (test desfasado).
   - No + el test estaba verde antes: `SUT_BUG` (regresión real del SUT).

5. **¿La evidencia muestra que el test reaccionó a algo no previsto (modal nuevo, redirect, intersticial)?**
   - Sí: `TEST_DESIGN_ISSUE` (cobertura defensiva incompleta).
   - No: continuar evaluando.

En ambigüedad real, NO adivinar: marcar `UNKNOWN` con la pregunta abierta documentada y escalar.

## Severidad por clasificación

| Clasificación | Severidad por defecto |
|---|---|
| `SUT_BUG` | CRITICAL si el test es prioridad CRITICAL/HIGH; HIGH en el resto. |
| `ENVIRONMENT_BLOCKED` | HIGH (bloquea entrega aunque no sea bug del SUT). |
| `THRESHOLD_TOO_STRICT` | MEDIUM (recalibración pendiente, no bug). |
| `DATA_ISSUE` | MEDIUM (fixture mal diseñada, recurrente). |
| `TEST_DESIGN_ISSUE` | LOW-MEDIUM (mantenimiento de test). |
| `UNKNOWN` | HIGH (riesgo no caracterizado, requiere investigación). |

La severidad puede ser elevada por el agente con justificación documentada en el hallazgo.
