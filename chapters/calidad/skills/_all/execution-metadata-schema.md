---
id: calidad-execution-metadata-schema
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Schema universal {ISO}-metadata.json (13 keys) emitido por cada corrida en los stacks del chapter (Karate, Playwright, K6, Appium Serenity, Appium WebdriverIO, serenity-wdio) para que dashboards y delivery-gate procesen evidencia cross-stack."
tags: [evidence, metadata, schema, universal, mandatory]
enforcement: mandatory
---

# Execution Metadata Schema — `{ISO}-metadata.json` universal

Cada corrida (cualquier framework) DEBE emitir un `{ISO}-metadata.json` junto al summary del stack, con un schema idéntico cross-stack. Esto permite que dashboards, comparadores y el delivery-gate procesen evidencia de cualquier framework con el mismo parser.

## Schema JSON universal

```json
{
  "scenario_or_feature": "linea-base | login-flow | retrieve-transactions | addPet",
  "framework": "karate | playwright | k6 | appium | serenity-wdio",
  "version": "v1",
  "environment": "staging | dev | qa | prod-readonly",
  "workload_or_scope": "ramping-vus 5-5-0 over 5min | 12 escenarios | 5 HU | 3 devices",
  "sut_endpoint_or_url": "https://api.example.com | https://app.example.com",
  "auth_strategy": "setup | per-vu | storageState | actor | none",
  "exit_code": 0,
  "started_at": "2026-06-05T10:30:15Z",
  "finished_at": "2026-06-05T10:35:18Z",
  "duration_seconds": 303,
  "totals": { "total": 12, "passed": 12, "failed": 0, "skipped": 0 },
  "thresholds_or_coverage_met": true,
  "blockers": []
}
```

## Notas de campos

- `scenario_or_feature`: identificador legible humano (no path). En Karate es el feature o tag corrido; en Playwright es el nombre del project/grep; en K6 es la categoría del escenario; en Appium es el tag/feature principal.
- `version`: por ahora `"v1"`. Bump solo si cambia el schema breaking.
- `workload_or_scope`: descriptor textual de la magnitud — útil para que un humano entienda qué corrió sin abrir el summary.
- `auth_strategy`: alineado con la nomenclatura nativa de cada stack (`setup` Karate, `per-vu` K6, `storageState` Playwright, `actor` Appium/Screenplay, `none` cuando no hay auth).
- `started_at` / `finished_at`: ISO 8601 UTC con sufijo `Z`.
- `totals`: contadores agregados; semántica común aunque cada framework la derive de su summary nativo.
- `thresholds_or_coverage_met`: K6 → thresholds; Karate/Playwright/Appium → `effective_minimum` cubierto.
- `blockers`: lista de strings tipo `"environment_blocked_waf"`, `"smoke_gate_failed_appium"`, etc. (lista cerrada en `[environment-blocker-evidence](./environment-blocker-evidence.md)`).

## Cómo cada stack lo genera

### Karate

Hook `AfterAll` (vía JS hook en `karate-config.js` o vía clase Java en el runner) que parsea `karate-summary.json` y escribe `metadata.json` al lado. Detalle en [[calidad-karate-greenfield]] (consultar `references/metadata-emitter-karate.md` en su subfolder).

### Playwright

Custom reporter que implementa la interfaz `Reporter` y en `onEnd` escribe `metadata.json` en el mismo directorio que el `results.json`. Detalle en [[calidad-playwright-greenfield]] (consultar `references/metadata-emitter-playwright.md` en su subfolder).

### K6

Dentro de `handleSummary(data)`: construir el objeto metadata y devolverlo como segunda clave del map. Cubierto en oleada K6: [[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder).

### Appium

Serenity expone `ExecutionStateListener` (SPI vía `META-INF/services`) o, alternativa más simple, un `doLast` en el task `test` de Gradle que parsea `serenity-summary.json` y escribe `metadata.json` al lado. Detalle en [[calidad-appium-screenplay-android]] (consultar `references/metadata-emitter-appium.md` en su subfolder).

### serenity-wdio

El hook `onComplete` de WebdriverIO (declarado en `wdio.shared.conf.ts`) parsea el reporte Cucumber JSON generado por Serenity/JS y escribe `{ISO}-metadata.json` junto al summary en `results/serenity-wdio/{YYYY-MM-DD}/{ISO}/`. Los campos `auth_strategy` se mapean a `"actor"` (Screenplay) o `"none"`. Detalle en `[metadata-emitter-serenity-wdio](../serenity-wdio/serenity-wdio-greenfield/references/metadata-emitter-serenity-wdio.md)`.

## Consistencia obligatoria

- Los 5 emitters DEBEN producir un JSON con exactamente las mismas claves de nivel raíz.
- Si el framework no provee un dato (ej. K6 no tiene `auth_strategy="actor"`), usar el valor más cercano del enum o `"none"`. NUNCA omitir la clave.
- El path final es `<results-dir>/{ISO}-metadata.json` siguiendo `[results-structure-universal](./results-structure-universal.md)`.

## Cross-links

`[[calidad-test-evidence-and-traceability]]`, `[[calidad-delivery-gate-contract]]`, `[results-structure-universal](./results-structure-universal.md)`, `[environment-blocker-evidence](./environment-blocker-evidence.md)`.
