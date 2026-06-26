# Step Isolation — Karate

Implementación del patrón universal `[step-isolation-pattern](../../../_all/step-isolation-pattern.md)` en Karate. El mecanismo nativo es `Background:` para setup compartido + tags por scenario para aislar criterios.

## Mecanismo

- **Setup**: `Background:` ejecuta antes de cada `Scenario:`. Aquí van `* url baseUrl`, configuración de headers globales, no aserciones de dominio.
- **Auth**: escenario etiquetado `@auth` que valida sólo que el token se obtuvo. NO codifica contrato del SUT.
- **Main**: escenario etiquetado `@main` (puede combinarse con `@happy-path`, `@contract`, `@data-driven`, `@negative-*`) que codifica el contrato del SUT.
- **Cleanup**: opcional; cuando aplica, escenario `@cleanup` separado al final, con su propia evaluación.

## Snippet

```gherkin
@main
Feature: Retrieve transactions

  Background:
    # setup compartido — NO se mide como aserción de dominio
    * url baseUrl
    * configure headers = { 'Content-Type': 'application/json' }

  @auth
  Scenario: setup auth (no contractual)
    Given path '/auth/login'
    And request { username: 'user', password: 'pass' }
    When method post
    Then status 200
    * def token = response.access_token
    # Token guardado para reuso por el main; este Scenario NO valida el contrato del SUT.

  @happy-path @main
  Scenario: retrieve transactions successfully
    Given path '/transactions'
    And header Authorization = 'Bearer ' + token
    When method get
    Then status 200
    And match each response.data contains { id: '#string', amount: '#number' }
    And match response.metadata == { totalItems: '#number', currentPage: '#number' }

  @contract @main
  Scenario: response schema matches contract
    Given path '/transactions'
    And header Authorization = 'Bearer ' + token
    When method get
    Then status 200
    And match response == read('classpath:schemas/transactions-match.json')

  @cleanup
  Scenario: revoke token
    Given path '/auth/logout'
    And header Authorization = 'Bearer ' + token
    When method post
    Then status 204
```

## Reglas Karate-específicas

- `Background:` NO debe contener aserciones de dominio (`match`, `assert`). Sólo configuración (url, headers, helpers).
- Cada `Scenario:` declara su tag de step. Un escenario con tag `@main` que también tenga `@happy-path` cuenta para cobertura; un `@auth` no cuenta.
- La fórmula de cobertura ``negative-coverage-formula.md`` cuenta SOLO escenarios `@main` (con sus tags refinados `@happy-path`, `@contract`, etc.). NO cuenta `@auth` ni `@cleanup`.
- Filtrado en `mvn test`: `mvn test -Dkarate.options="--tags @main"` corre sólo el flujo principal; útil para smoke gates.
- En el `karate-summary.json`, separar el conteo por tag permite reportar "main passed / auth passed / cleanup failed" en el `metadata.json` (ver `[metadata-emitter-karate](./metadata-emitter-karate.md)`).

## Cross-links

`[step-isolation-pattern](../../../_all/step-isolation-pattern.md)`, `[feature-design-dsl](./feature-design-dsl.md)`, ``negative-coverage-formula.md``, `[metadata-emitter-karate](./metadata-emitter-karate.md)`, `[[calidad-karate-greenfield]]`.
