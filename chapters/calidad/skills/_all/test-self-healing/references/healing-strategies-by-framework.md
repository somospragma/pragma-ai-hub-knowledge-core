# Healing Strategies por Framework

Matriz operativa de estrategias de self-healing soportadas por cada framework del chapter. La columna **Telemetría obligatoria** marca el formato del log estructurado requerido (ver paso 4 del SKILL).

## Matriz por framework

| Framework | Estrategias permitidas | Implementación primaria | Implementación de respaldo | Telemetría obligatoria | Estrategias prohibidas |
|---|---|---|---|---|---|
| Playwright (web) | auto-wait, soft locators, multi-locator fallback, fixtures recovery, visual AI opcional | `getByTestId` con fallback chain | `ResilientLocator` (ver `multi-locator-fallback-pattern.md`) | `{event:"healing", framework:"playwright", test_id, strategy_idx, locator_original, locator_resolved}` | nunca curar selectors en `@security` o `@regression-strict`; nunca usar XPath como primario |
| Appium (mobile native/híbrido) | `AppiumBy` chain alternatives, accessibility-id como primary, Healenium para Selenium/Appium legacy | `AppiumBy.accessibilityId` con fallback chain | Healenium server para selectors antiguos sin `accessibility-id` | `{event:"healing", framework:"appium", test_id, platform, locator_original, locator_resolved}` | xpath absoluto como primary; ignorar permisos del OS curándolos como modal accidental |
| Karate (REST / GraphQL) | `##optional`, `karate.match` permisivo controlado, retry hooks para timeouts transitorios | `match response == { id: '#number', name: '##string' }` (opcional explícito) | `karate.retry(count, intervalMs)` para 5xx transitorios | `{event:"healing", framework:"karate", scenario, feature, field_optional_changed, status_retried}` | aflojar `#string` requerido a `##string`; retry para 4xx (es bug del cliente del test); reintentar contract tests |
| K6 (perf) | response shape validation con `check()` permisivo, alerta si shape drift, retry hooks de transient errors | `check(res, { 'shape ok': r => r.json().items !== undefined })` con shape baseline | logger custom que emite warning sin fallar el VU si la shape drift es no-breaking | `{event:"healing", framework:"k6", test_id, endpoint, drift_type:"shape_optional_added"}` | aflojar thresholds; ignorar `http_req_failed`; convertir 5xx en check warning |

## Decisiones operativas

- **Playwright**: el orden del fallback chain es regla del chapter, no preferencia. Saltarlo viola `[[calidad-chapter-perspective]]`.
- **Appium**: `accessibility-id` debe pedirse al equipo de desarrollo como entregable inicial — si no existe, se documenta como deuda y se prioriza con el cliente.
- **Karate**: el matcher `##type` (opcional con type-check) es la única forma aceptada de tolerar drift de campos opcionales. Nunca usar `#ignore` para esconder campos faltantes.
- **K6**: el shape drift detectado debe emitir un evento que el orquestador (`[[calidad-test-execution-orchestration]]`) escala como warning de release, no como falla.

## Telemetría: pipeline mínimo

Todo log estructurado sale por `stdout` en formato JSON, es capturado por el runner del CI y enviado al colector de evidencia (`[[calidad-test-evidence-and-traceability]]`). El dashboard de healing agrega por `test_id` y dispara la regla de >3 healings/semana definida en `over-healing-guardrails.md`.
