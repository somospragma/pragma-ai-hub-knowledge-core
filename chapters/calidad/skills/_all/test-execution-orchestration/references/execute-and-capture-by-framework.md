# Execute and Capture by Framework

Comandos exactos por framework, con captura completa de stdout/stderr y rutas de los artefactos resultantes. La salida de `tee` queda en disco como respaldo del log textual; los artefactos estructurados (JSON, XML, HTML) quedan en las rutas del framework para ser parseados por `output-parsers.md`.

## Karate

Comando base:

```bash
mvn test -Dkarate.options="--tags @smoke" 2>&1 | tee target/run.log
```

Variantes útiles:

```bash
# Suite completa
mvn test 2>&1 | tee target/run.log

# Tag específico + entorno
mvn test -Dkarate.env=qa -Dkarate.options="--tags @regression" 2>&1 | tee target/run.log

# Paralelización
mvn test -Dkarate.options="--tags @smoke" -Dtest=TestRunner 2>&1 | tee target/run.log
```

Outputs y artefactos:

- `target/karate-reports/karate-summary-json.txt` — summary en JSON con totales y por feature.
- `target/karate-reports/karate-summary.html` — dashboard HTML navegable.
- `target/surefire-reports/*.xml` — JUnit XML por test runner (input para CI test result publishers).
- `target/karate-reports/*.html` — reportes detallados por feature.
- `target/run.log` — log textual completo de la ejecución (stdout + stderr).

Exit code: `0` si todos los tests pasan; `≠ 0` si hay fallos o errores de runtime.

## Playwright

Configuración previa en `playwright.config.ts`:

```ts
export default defineConfig({
  reporter: [
    ['json', { outputFile: 'results.json' }],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list']
  ],
  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  }
});
```

Comando base:

```bash
npx playwright test --reporter=json,html 2>&1 | tee playwright-run.log
```

Variantes útiles:

```bash
# Project específico (browser)
npx playwright test --project=chromium 2>&1 | tee playwright-run.log

# Sharding nativo
npx playwright test --shard=1/4 2>&1 | tee playwright-run.log

# Solo tests marcados
npx playwright test --grep @smoke 2>&1 | tee playwright-run.log
```

Outputs y artefactos:

- `results.json` — JSON reporter con suites, tests, errores, duración (input principal del parser).
- `playwright-report/index.html` — dashboard HTML.
- `test-results/<test-id>/trace.zip` — trazas Playwright para inspección con `npx playwright show-trace`.
- `test-results/<test-id>/test-failed-*.png` — screenshots de fallo.
- `test-results/<test-id>/video.webm` — videos de la sesión.
- `playwright-run.log` — log textual.

Exit code: `0` si todos pasan; `1` si hay fallos.

## K6

Comando base:

```bash
k6 run --summary-export=summary.json tests/smoke-test.js 2>&1 | tee k6-run.log
```

Variantes útiles:

```bash
# Con umbrales adicionales y output a Prometheus remoto
k6 run --summary-export=summary.json \
       -o experimental-prometheus-rw \
       tests/load-test.js 2>&1 | tee k6-run.log

# Con handleSummary custom (recomendado)
k6 run tests/load-test.js 2>&1 | tee k6-run.log
```

Patrón `handleSummary` recomendado en el script:

```js
export function handleSummary(data) {
  return {
    'results/summary.json': JSON.stringify(data, null, 2),
    'results/summary.html': htmlReport(data),
    stdout: textSummary(data, { indent: ' ', enableColors: false }),
  };
}
```

Outputs y artefactos:

- `summary.json` (o `results/summary.json` con handleSummary) — métricas agregadas, checks, thresholds.
- `results/summary.html` — dashboard HTML cuando se usa `htmlReport`.
- `k6-run.log` — log textual con métricas en tiempo real.

Exit code: `0` si todos los thresholds pasan; `99` si algún threshold falla; `≠ 0/99` si hay error de runtime.

## Appium (Serenity / Gradle)

Comando base:

```bash
./gradlew clean test aggregate 2>&1 | tee gradle-run.log
```

Variantes útiles:

```bash
# Tag específico
./gradlew clean test aggregate -Dtags="@smoke" 2>&1 | tee gradle-run.log

# Device específico
./gradlew clean test aggregate -Ddevice=pixel_7_api_34 2>&1 | tee gradle-run.log
```

Outputs y artefactos:

- `target/site/serenity/index.html` — dashboard Serenity navegable.
- `target/site/serenity/results.json` — JSON consolidado de la ejecución (input principal del parser).
- `target/site/serenity/*.json` — un JSON por test scenario con steps, screenshots y duración.
- `target/site/serenity/screenshots/` — capturas por step.
- `gradle-run.log` — log textual.

Exit code: `0` si todos los scenarios pasan; `≠ 0` si hay fallos.

## Convenciones comunes

- Redirección `2>&1 | tee <log>` para preservar stdout y stderr fusionados en un archivo único, manteniendo además la visibilidad en consola.
- El log textual (`*.log`) es respaldo; los parsers deben preferir el output estructurado (JSON/XML).
- Los artefactos grandes (videos, traces, HTML reports) se archivan según `evidence-archival.md`, no se inlinean en el contexto del agente.
- Si la herramienta corre dentro de un contenedor, montar volumen para persistir los artefactos fuera del contenedor antes de parsear.
