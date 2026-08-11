# Metadata Emitter — Appium (Serenity + Gradle)

Serenity genera `serenity.summary.json` al finalizar la tarea `aggregate`. Este reference define cómo derivar el `{ISO}-metadata.json` universal definido en `[[calidad-execution-metadata-schema]]` mediante un task Gradle que corre después de `test`.

## Mecanismo

`build.gradle` declara una task `emitMetadata` que:

1. Lee `target/site/serenity/serenity.summary.json` (default output del plugin `serenity-gradle-plugin` 4.1.14).
2. Construye el objeto metadata respetando el schema universal.
3. Escribe `results/appium/{YYYY-MM-DD}/{ISO}-metadata.json`.
4. Se enlaza vía `test.finalizedBy emitMetadata` para garantizar que corre incluso si `test` falla.

## Snippet `build.gradle`

```gradle
task emitMetadata {
  doLast {
    def ts = new Date().format("yyyy-MM-dd'T'HH-mm-ss'Z'", TimeZone.getTimeZone('UTC'))
    def date = ts.substring(0, 10)
    def base = file("results/appium/$date")
    base.mkdirs()

    def summary = file("target/site/serenity/serenity.summary.json")
    def data = summary.exists()
      ? new groovy.json.JsonSlurper().parse(summary)
      : [:]

    def totalScenarios  = (data.totalScenarios  ?: 0) as Integer
    def passedScenarios = (data.passedScenarios ?: 0) as Integer
    def failedScenarios = (data.failedScenarios ?: 0) as Integer
    def skippedScenarios = (data.skippedScenarios ?: 0) as Integer

    def metadata = [
      scenario_or_feature: (project.findProperty('scenario') ?: 'all'),
      framework: 'appium',
      version: 'v1',
      environment: (System.getenv('ENV') ?: 'staging'),
      workload_or_scope: "${totalScenarios} escenarios",
      sut_endpoint_or_url: (System.getenv('APP_PACKAGE') ?: System.getenv('APPIUM_SERVER_URL') ?: ''),
      auth_strategy: 'actor',
      exit_code: (failedScenarios == 0 ? 0 : 1),
      started_at: ts,
      finished_at: ts,
      totals: [
        total:   totalScenarios,
        passed:  passedScenarios,
        failed:  failedScenarios,
        skipped: skippedScenarios,
      ],
      thresholds_or_coverage_met: (failedScenarios == 0),
      blockers: []
    ]

    def json = groovy.json.JsonOutput.prettyPrint(groovy.json.JsonOutput.toJson(metadata))
    new File(base, "${ts}-metadata.json").text = json
  }
}

test.finalizedBy emitMetadata
```

## Mapeo de campos

| Campo metadata | Origen Appium/Serenity |
|---|---|
| `scenario_or_feature` | `-Pscenario=login-flow` (property Gradle) o `'all'`. |
| `framework` | Constante `appium`. |
| `workload_or_scope` | `"<N> escenarios"` con N = `totalScenarios`. |
| `sut_endpoint_or_url` | `APP_PACKAGE` (identificador de la app) o `APPIUM_SERVER_URL`. |
| `auth_strategy` | `actor` — Screenplay usa Actors que portan credenciales. `none` si la app no requiere auth. |
| `totals` | `serenity.summary.json` → `totalScenarios`, `passedScenarios`, `failedScenarios`, `skippedScenarios`. |
| `thresholds_or_coverage_met` | `failedScenarios == 0`. |
| `blockers` | Vacío si OK; llenado desde `execution-status.json` cuando el preflight falla (device unavailable, JDK wrong). |

## Reglas

- Path final: `results/appium/{YYYY-MM-DD}/{ISO}-metadata.json` (alineado con `[[calidad-results-structure-universal]]`).
- `test.finalizedBy emitMetadata` garantiza ejecución incluso ante falla del `test` task — clave para evidencia de corridas rojas.
- NUNCA registrar la task con `tasks.register('aggregate')` ni redefinirla; respeta ``no-aggregate-collision.md``. `emitMetadata` es una task nueva, no choca con `aggregate`/`reports`/`clean`.
- Si el preflight (`preflight-appium.sh`) reporta device unavailable o JDK wrong, NO se ejecuta `test`; el script preflight escribe directamente `.evidence/execution-status.json` con `reason=environment_device_unavailable` o `environment_jdk_missing_or_wrong`.
- NO omitir claves: si Appium no aplica una semántica, usar enum o valor neutro del schema (ej. `auth_strategy: "none"`).

## Cross-links

`[[calidad-execution-metadata-schema]]`, `[[calidad-results-structure-universal]]`, `[[calidad-environment-blocker-evidence]]`, ``no-aggregate-collision.md``, `[[calidad-appium-screenplay-android]]`, `[[calidad-delivery-gate-contract]]`.
