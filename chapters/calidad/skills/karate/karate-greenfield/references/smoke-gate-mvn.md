# Smoke Gate (Karate) — `mvn test` con `--tags @smoke`

Implementación Karate de la política universal `[[calidad-smoke-gate-policy]]`. Antes de declarar `status: success`, el agente DEBE correr al menos un escenario etiquetado `@smoke` y validar exit code 0.

## Comando canónico

```bash
mvn test -f pom.xml -Dkarate.options="--tags @smoke" -Dtest=TestRunner
```

Notas:

- `-f pom.xml` resuelve el POM de forma explícita; evita que `mvn` busque ascendiendo el árbol y termine corriendo el módulo equivocado en monorepos.
- `-Dkarate.options="--tags @smoke"` filtra escenarios a aquellos con tag `@smoke` exclusivamente.
- `-Dtest=TestRunner` limita el ciclo a la clase runner única del proyecto (ver ``references/templates.md` (sección `TestRunner.java`)`); evita escaneos de tests anexos generados por terceros.
- Surefire devuelve exit code 0 si todos los escenarios `@smoke` pasan; ≠ 0 si alguno falla.

## Asegurar al menos un escenario `@smoke`

El agente DEBE garantizar que existe ≥1 feature con un Scenario etiquetado `@smoke` que represente un happy path mínimo end-to-end. Convención: el primer feature canónico generado (típicamente `health` o un GET feliz del endpoint principal) lleva `@smoke` además de su tag funcional.

Ejemplo:

```gherkin
# cobertura: 1
Feature: Health check
  Background:
    * url baseUrl

  @smoke @health
  Scenario: GET /health responde 200
    Given path '/health'
    When method get
    Then status 200
```

Si el agente no puede emitir un escenario `@smoke` (porque ninguna HU lo justifica o el SUT no expone health), DEBE generar un escenario sintético `@smoke` que pegue al endpoint más simple del risk_map y validar 2xx/3xx. Sin escenario `@smoke` no hay smoke gate.

## Parsing del resultado

El reporter Surefire emite XML en `target/surefire-reports/TEST-*.xml` y Karate emite `target/karate-reports/karate-summary-json.txt`. Validar primero el exit code del proceso `mvn`; como segunda señal, parsear el JSON resumen:

```bash
EXIT=$?
if [ $EXIT -ne 0 ]; then
  echo "smoke_gate_failed_karate exit=$EXIT" >&2
  exit $EXIT
fi

FAILED=$(jq '.featuresFailed // 0' target/karate-reports/karate-summary-json.txt)
if [ "$FAILED" != "0" ]; then
  echo "smoke_gate_failed_karate failed=$FAILED" >&2
  exit 1
fi
```

Si `target/karate-reports/karate-summary-json.txt` no existe tras correr `mvn`, es señal de que ningún escenario `@smoke` matcheó → reportar `smoke_gate_missing_scenario_karate`.

## Wiring con delivery_gate

```yaml
smoke_gate:
  framework: karate
  command: "mvn test -f pom.xml -Dkarate.options=\"--tags @smoke\" -Dtest=TestRunner"
  executed: true
  exit_code: 0
  duration_seconds: 12
```

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-smoke-gate-policy]]`.
