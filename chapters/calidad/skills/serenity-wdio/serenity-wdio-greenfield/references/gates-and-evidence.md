# Compuertas, evidencia y metadata (Serenity WDIO Greenfield)

Mapeo del proyecto generado a los assets transversales `_all` del chapter `calidad`.

## Compuerta smoke

`[[calidad-smoke-gate-policy]]` se satisface ejecutando la suite `@smoke` con el orquestador:

```bash
node ./scripts/run.mjs --tags=@smoke
# equivalente via package.json
npm run test:smoke
```

Si la compuerta smoke no pasa, la ejecucion se marca como fallida, se impide la promocion de resultados y se reporta el criterio incumplido.

## Compuerta de entrega

`[[calidad-delivery-gate-contract]]` se satisface verificando antes de cerrar la entrega: estructura completa del proyecto, configs coherentes (incluido `enforceWebDriverClassic` en web), features que parsean en Cucumber y scripts de ejecucion presentes en `package.json`.

## Evidencia y trazabilidad

`[[calidad-test-evidence-and-traceability]]` se satisface con los reporters del arquetipo:

| Artefacto | Herramienta |
|---|---|
| Reporte Allure | `@wdio/allure-reporter` |
| Reporte Serenity BDD | `@serenity-js/serenity-bdd` |
| JSON de Cucumber | `wdio-cucumberjs-json-reporter` |
| Video de ejecucion | `wdio-video-reporter` (web) |

## Estructura de resultados universal

`[[calidad-results-structure-universal]]` se satisface proyectando los artefactos existentes a `results/{categoria}/{fecha}/` (por ejemplo `results/web/<YYYY-MM-DD>/`) mediante un adaptador post-ejecucion no destructivo que conserva los reportes originales intactos.

## Metadata de ejecucion

`[[calidad-execution-metadata-schema]]` se satisface emitiendo `{ISO}-metadata.json` por corrida con: timestamp ISO, stack (`serenity-wdio`), modo, plataforma, tags, totales pass/fail/skip, duracion, estado del smoke gate y ruta de evidencia. Leer el asset real para la lista exacta de campos obligatorios.

## Generacion incremental de archivos

`[[calidad-streaming-files-protocol]]` se satisface entregando los archivos generados de forma incremental, sin cortes parciales, durante el scaffolding greenfield.
