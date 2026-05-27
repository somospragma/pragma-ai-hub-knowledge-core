
# Diseño de Feature Files — DSL y tipos de escenario

## Matriz de escenarios obligatorios

| Tipo | Tag(s) obligatorios | Propósito |
|---|---|---|
| Happy Path | `@happy-path` | Request válido → respuesta exitosa con significado de negocio (no sólo status). |
| Contract | `@contract` | `match response == read('classpath:schemas/{resource}-match.json')`. |
| Negative — bad request | `@negative @bad-request` | Respuestas 400/404/422 según contrato. |
| Negative — missing field | `@negative @missing-field` | Uno por cada required field (campo ausente). |
| Negative — null field | `@negative @null-field` | Uno por cada required field (valor `null`). |
| Negative — invalid type | `@negative @invalid-type` | Uno por cada required field tipado. |
| Negative — missing header | `@negative @missing-header` | Uno por cada header obligatorio. |
| Negative — invalid header format | `@negative @invalid-header-format` | Uno por cada header con formato (UUID, email, date). |
| Data-driven | `@data-driven` | `Scenario Outline` + `Examples` con al menos 3 filas. |
| Encrypted happy | `@happy-path @encrypted` | Sólo si hay señales de cifrado. |
| Encryption invalid | `@negative @invalid-encryption` | Llave incorrecta o payload no descifrable. |

Naming convention en inglés: `Scenario: Create transaction - happy path`, `Scenario: Create transaction - missing field amount`. Para Mercantil se usa otra convención (ver `[[karate-mercantil-conventions]]`).

## Snippet completo

```gherkin
Feature: Create transaction API

  Background:
    * url baseUrl
    * def validBody = read('classpath:com/testing/bodies/create-transaction.json')

  @happy-path
  Scenario: Create transaction - happy path
    Given path '/transactions'
    And header X-Channel = 'web'
    And request validBody
    When method post
    Then status 201
    And match response.transactionId == '#uuid'
    And match response.status == 'APPROVED'

  @contract
  Scenario: Create transaction - contract validation
    Given path '/transactions'
    And header X-Channel = 'web'
    And request validBody
    When method post
    Then status 201
    And match response == read('classpath:schemas/transaction-match.json')

  @negative @missing-field
  Scenario: Create transaction - missing field amount
    * def body = karate.merge(validBody, {})
    * remove body.amount
    Given path '/transactions'
    And header X-Channel = 'web'
    And request body
    When method post
    Then status 400

  @negative @null-field
  Scenario: Create transaction - null field amount
    * def body = karate.merge(validBody, { amount: null })
    Given path '/transactions'
    And header X-Channel = 'web'
    And request body
    When method post
    Then status 400

  @negative @invalid-type
  Scenario: Create transaction - invalid type amount
    * def body = karate.merge(validBody, { amount: 'not-a-number' })
    Given path '/transactions'
    And header X-Channel = 'web'
    And request body
    When method post
    Then status 400

  @negative @missing-header
  Scenario: Create transaction - missing header X-Channel
    Given path '/transactions'
    And request validBody
    When method post
    Then status 400

  @data-driven
  Scenario Outline: Create transaction - data driven amounts
    Given path '/transactions'
    And header X-Channel = 'web'
    And request karate.merge(validBody, { amount: <amount> })
    When method post
    Then status <expectedStatus>

    Examples:
      | amount  | expectedStatus |
      | 1       | 201            |
      | 999999  | 201            |
      | -1      | 400            |
```

Sin lógica condicional (`if`) en aserciones. `Examples` sin celdas vacías.
