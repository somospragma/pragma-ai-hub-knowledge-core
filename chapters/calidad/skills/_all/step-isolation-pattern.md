---
id: calidad-step-isolation-pattern
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Aislamiento de métricas y criterios por step (setup/auth/main/cleanup) usando tags. Anti-pattern: mezclar criterio de auth con criterio del flow objetivo."
tags: [pattern, step-isolation, metrics, universal]
---

# Step Isolation Pattern — Aislamiento de métricas y criterios por step

## Principio

Cuando un test tiene múltiples steps (setup, auth, main, cleanup), las métricas y los criterios de éxito DEBEN aislarse por step. Mezclar el criterio de éxito de la autenticación con el criterio del flow objetivo es un anti-pattern frecuente que produce:

- **Falsos positivos**: el flow main funciona pero el cleanup falla → test rojo aunque el contrato bajo prueba esté OK.
- **Falsos negativos**: el setup falla intermitentemente, el main nunca se ejecuta, pero el test reporta "passed" porque el step main no llegó a fallar.
- **Métricas contaminadas**: latencia agregada de auth + main impide ver tendencias del endpoint real bajo prueba.

La regla: **cada step tiene sus propias aserciones, sus propias métricas y su propio tag**. El test final reporta el estado de cada step de forma independiente, y la métrica de performance/cobertura del flow principal NO incluye el ruido del setup ni del cleanup.

## Tabla por stack

| Stack | Mecanismo |
|---|---|
| Karate | `Background:` para setup compartido; tags por step (`@auth`, `@main`, `@cleanup`); las assertions del cleanup se evalúan en escenarios separados. |
| Playwright | `test.beforeEach` para setup; `test.afterEach` para cleanup; assertions main en el cuerpo del test; tags `@auth-step`, `@main-step` para filtrar métricas. |
| K6 | `tags: { step: 'auth' \| 'main' \| 'cleanup' }` en cada check; thresholds aislados por tag (`http_req_failed{step:main}: ['rate<0.01']`). |
| Appium | Tasks separadas para setup vs main; Questions de dominio (las que codifican el contrato) se evalúan SOLO en el step main; setup usa Questions estructurales. |

## Anti-pattern

```javascript
// MAL — el check de auth contamina la métrica del main
check(loginRes, { 'login ok': r => r.status === 200 });
check(mainRes,  { 'transactions ok': r => r.status === 200 });
// threshold global: http_req_failed: ['rate<0.01']
// Si el IdP falla, "rate<0.01" rompe aunque las transacciones no se hayan probado.
```

```javascript
// BIEN — métricas aisladas por step
check(loginRes, { 'login ok': r => r.status === 200 },
  { step: 'auth' });
check(mainRes,  { 'transactions ok': r => r.status === 200 },
  { step: 'main' });
// thresholds:
//   http_req_failed{step:main}: ['rate<0.01']  // criterio del SUT
//   http_req_failed{step:auth}: ['rate<0.05']  // criterio del ambiente
```

## Reglas universales

- **Una métrica, un step**: cada métrica/check debe portar su tag de step. NO existe una métrica global "del test"; existen métricas por step que se agregan en el reporte.
- **Setup no contaminado**: las aserciones de setup (login obtuvo token, base de datos sembrada) son estructurales — no son aserciones del contrato del SUT.
- **Cleanup es opcional para el veredicto**: si el cleanup falla pero el main pasó, el delivery_gate puede reportar `success` con `warning: cleanup_failed` en lugar de `failed`.
- **Tag obligatorio cuando hay ≥2 steps**: si el test sólo tiene un step (smoke 1-endpoint), el tag se omite. A partir de 2 steps, es obligatorio.
- **Cobertura sólo cuenta steps main**: la fórmula de `effective_minimum` por HU cuenta escenarios de main, NO de setup ni cleanup.

## Cross-links por stack

- `[step-isolation-karate](../karate/karate-greenfield/references/step-isolation-karate.md)`
- `[step-isolation-playwright](../playwright/playwright-greenfield/references/step-isolation-playwright.md)`
- `[tag-policy-and-metrics-isolation](../k6/k6-greenfield/references/tag-policy-and-metrics-isolation.md)` (K6 ya cubierto)
- `[step-isolation-appium](../appium/appium-screenplay-android/references/step-isolation-appium.md)`

## Cross-links generales

`[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[execution-metadata-schema](./execution-metadata-schema.md)`.
