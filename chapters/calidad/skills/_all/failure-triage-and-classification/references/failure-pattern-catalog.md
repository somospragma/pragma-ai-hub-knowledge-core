# Failure Pattern Catalog

Catálogo canónico de patrones de fallo usados por el chapter. Cada fallo del CI debe mapearse a uno de estos patrones antes de decidir acción. Si no encaja en ninguno, escalar al lead del chapter para ampliar el catálogo (no inventar categoría ad-hoc).

## Cómo usar el catálogo

1. Tomar la evidencia del fallo (mensaje de error, stack, trace, request/response).
2. Buscar en la tabla el patrón cuyos síntomas observables coincidan.
3. Validar la causa probable contra la evidencia adicional listada.
4. Aplicar la acción recomendada. Si la acción es "reportar bug", **NO modificar el test**.

## Catálogo

| # | Patrón | Síntomas observables | Causa probable | Evidencia a recolectar | Acción recomendada |
|---|---|---|---|---|---|
| 1 | **Stale locator** | `Element not found`, `Locator did not resolve` en Playwright/Appium; XPath retorna vacío. | UI cambió selectores (refactor de componentes, nuevo design system). | DOM snapshot, screenshot, locator chain usado. | Auto-healing vía `[[calidad-test-self-healing]]` con multi-locator fallback. |
| 2 | **Assertion mismatch deterministic** | `expected X but got Y` consistente en N re-runs. El valor `Y` es estable. | Cambio de contrato del SUT (lógica de negocio modificada). | Request, response, valor esperado vs actual, diff. | **NO corregir el test**. Reportar bug al equipo dev del cliente. |
| 3 | **Race condition (parallel)** | Falla solo cuando los tests corren en paralelo; pasa en `--workers=1`. | Tests comparten estado global (DB, archivos, env vars). | Lista de tests que corrieron en paralelo en el mismo runner. | Aislar fixtures por test; ver `[[calidad-test-data-management]]`. |
| 4 | **Network blip** | `ETIMEDOUT`, `ECONNRESET`, `socket hang up` esporádicos sin patrón. | Infraestructura de red transitoria (DNS, proxy, NAT). | Logs de red, timestamp del fallo, status de la VPN/proxy. | Retry con backoff exponencial; si persiste >3 veces/día, escalar a plataforma cliente. |
| 5 | **Stale data** | Test esperaba un registro/entidad que ya no existe (404, "no rows found"). | Cleanup de un run previo falló o teardown incompleto. | Estado de la DB/storage del SUT antes del test, log del teardown previo. | Robustecer teardown; usar fixtures self-contained (`[[calidad-test-data-management]]`). |
| 6 | **Cold start (serverless)** | Primer request del run lento (>3s), resto rápido (<300ms). Solo en Lambda/Cloud Run/Functions. | Función serverless en cold-start. | Latencia request 1 vs request 2..N. | Smoke warmup antes del test; o ajustar el SLA para incluir cold start. |
| 7 | **Auth token expired** | `401 Unauthorized` esporádico en runs largos (>30 min). | Token JWT/OAuth vence durante la ejecución del run. | TTL del token, hora de emisión, hora del fallo. | Refresh token automático en un fixture `beforeEach` o helper compartido. |
| 8 | **Schema drift no-breaking** | Campo nuevo opcional en la response que rompe `expect(response).toEqual(...)`. | API evolucionó añadiendo campos opcionales. | Diff del schema esperado vs actual. | Tolerar con `##optional` (Karate) o `expect.objectContaining(...)` / ignore extra (Playwright). Validar que el campo nuevo no afecte la lógica del SUT. |
| 9 | **Schema drift breaking** | Campo requerido faltante; tipo cambió (string → number); endpoint movido. | Bug de regresión o breaking change no anunciado. | Diff del schema esperado vs actual, changelog del SUT si existe. | **NO corregir el test**. Reportar bug; coordinar versión de API. |
| 10 | **Timing inconsistente** | `expected URL after redirect` falla a veces; "modal not visible" esporádico. | Falta `waitForLoadState('networkidle')` o wait explícito. | Trace de Playwright/Appium mostrando el orden de eventos. | Agregar wait explícito sobre el evento correcto (no `sleep()`); auto-corregible. |
| 11 | **Env config drift** | Tests pasaban ayer, fallan hoy sin cambios en el repo de tests. | Config de staging del cliente cambió (URL, feature flag, datos seed). | Diff de variables de entorno entre run anterior y actual; ticket de cambio del cliente. | Escalar a plataforma del cliente; no es bug del test ni del SUT del equipo. |
| 12 | **Mobile device-specific** | Falla en device X (ej. Pixel 4 Android 10), pasa en device Y (Pixel 6 Android 13). | Bug device-specific (resolución, OS API, fragment manager). | Logs de Appium en ambos devices, screenshot comparativo. | Reportar bug al cliente; marcar test como `@skip-device:pixel-4` en quarantine si no es crítico. |
| 13 | **Flaky high-variance** | Errores diferentes en cada re-run (a veces timeout, a veces 500, a veces assertion). | Race condition severo en el SUT o en el setup del test. | Lista de errores únicos en N re-runs. | Refactor arquitectural del test o del SUT; sin fix mecánico simple. Escalar a lead. |
| 14 | **K6 threshold breach intermittent** | P95 supera el threshold en 1 de cada 4 corridas. | Threshold mal calibrado o noise del runner. | Distribución de latencias en runs históricos. | Calibrar con `[[calidad-calibrate-k6-thresholds]]`; **nunca aflojar threshold sin justificación**. |
| 15 | **Visual regression false positive** | Diff de pixels en bordes por antialiasing; cambio de fuente del sistema operativo. | Threshold visual demasiado estricto o entorno gráfico inestable. | Imagen baseline vs actual, área diff resaltada. | Ajustar `maxDiffPixels` o cambiar Match Level (Applitools); fijar el runner OS para baselines. |

## Notas de uso

- Los patrones 2, 9, 12 (parcial) **siempre** implican reportar al cliente; no auto-corregir.
- Los patrones 1, 8, 10 son los más comunes en suites Playwright/Karate maduras; tener fixtures de healing pre-armados.
- Los patrones 3 y 5 suelen ser síntoma del mismo problema raíz (data sharing); revisar `[[calidad-test-data-management]]`.
- El patrón 11 es zona gris: no es bug del SUT ni del test, pero el cliente debe coordinar; documentar siempre.
