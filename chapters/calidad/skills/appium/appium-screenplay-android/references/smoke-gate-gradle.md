# Smoke Gate (Appium) — `./gradlew test` con `cucumber.filter.tags=@smoke`

Implementación Appium/Serenity-Cucumber de la política universal `[smoke-gate-policy](../../../_all/smoke-gate-policy.md)`. Antes de declarar `status: success`, el agente DEBE correr al menos un escenario etiquetado `@smoke` y validar exit code 0.

## Comando canónico

```bash
./gradlew test -Dcucumber.filter.tags="@smoke"
```

Notas:

- Cucumber JUnit Platform 7.x lee `cucumber.filter.tags` desde system properties; `build.gradle` ya hace `systemProperties System.getProperties()` (ver ``references/templates.md` (sección `build.gradle`)`), por lo que el `-D` se propaga al JVM de tests.
- El task `test` retorna exit code 0 si todos los escenarios `@smoke` pasan; ≠ 0 si alguno falla.
- NUNCA usar `--tests` style filtering (eso es JUnit puro, ignora Cucumber tags). Tampoco usar `--tests "*Smoke*"` por nombre de runner — el escenario `@smoke` puede vivir en cualquier runner.

## Asegurar al menos un escenario `@smoke`

El agente DEBE garantizar ≥1 escenario `@smoke` que represente happy path mínimo end-to-end (típicamente: launch app + assertion del primer elemento crítico, o login con credenciales fake si el SUT lo expone). Ejemplo:

```gherkin
Feature: Health check de la app

  @smoke
  Scenario: La app abre y muestra la pantalla principal
    Given Sergio abre la aplicacion
    Then la pantalla principal esta visible
```

Si no hay escenario `@smoke`, reportar `smoke_gate_missing_scenario_appium`. Convención: el primer feature canónico del scaffold incluye un `@smoke` además de su tag funcional.

## Parsing del resultado

Serenity-Cucumber emite `target/site/serenity/serenity-summary.json` (o `build/reports/serenity/serenity-summary.json` según Gradle layout) tras `serenity-gradle-plugin` ejecutar `aggregate`. Validar primero el exit code; como segunda señal, parsear el JSON:

```bash
EXIT=$?
if [ $EXIT -ne 0 ]; then
  echo "smoke_gate_failed_appium exit=$EXIT" >&2
  exit $EXIT
fi

# Path puede ser target/site/serenity/serenity-summary.json en layout maven-like
# o build/reports/serenity/... según gradle. Detectar:
SUMMARY=$(find . -name "serenity-summary.json" -path "*/serenity/*" | head -1)
if [ -z "$SUMMARY" ]; then
  echo "smoke_gate_missing_scenario_appium (no summary emitido)" >&2
  exit 1
fi

FAILED=$(jq '.results.counts.failure // 0' "$SUMMARY")
ERRORS=$(jq '.results.counts.error // 0' "$SUMMARY")
if [ "$FAILED" != "0" ] || [ "$ERRORS" != "0" ]; then
  echo "smoke_gate_failed_appium failed=$FAILED errors=$ERRORS" >&2
  exit 1
fi
```

Si el filtro `@smoke` no matchea ningún escenario, Cucumber sale con exit 0 pero `serenity-summary.json` reporta total=0 → reclasificar como `smoke_gate_missing_scenario_appium`.

## Wiring con delivery_gate

```yaml
smoke_gate:
  framework: appium
  command: "./gradlew test -Dcucumber.filter.tags=\"@smoke\""
  executed: true
  exit_code: 0
  duration_seconds: 45
```

> Recordar: el smoke gate Appium requiere device/emulator disponible. Si el device no está, el blocker se reclasifica como `environment_device_unavailable` según `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`.

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[smoke-gate-policy](../../../_all/smoke-gate-policy.md)`, `[health-check-pipeline](./health-check-pipeline.md)`.
