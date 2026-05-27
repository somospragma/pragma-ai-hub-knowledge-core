
# Convenciones Karate — cliente Mercantil

Aplica únicamente cuando el proyecto pertenece al cliente Mercantil. Sobrescribe las convenciones autodetectadas si hay conflicto.

## Naming de feature

`{jira-prefix}-{us-description}.feature`

Ejemplo: `PN-PR-BFF-1234-consulta-saldo.feature`

## Naming de scenario

- Positivo: `PN-PR-BFF-{jira} solicitud exitosa - {description}` con tags `@happyPath @regression @smoke`.
- Negativo: `PN-PR-BFF-{jira} solicitud fallida - {descripción del error}` con tags `@negative @regression`.

## Estilo obligatorio

- **Headers one-by-one**: `And header X-Name = 'value'`. NO `* configure headers = {...}`.
- **Body step-by-step**: `* def body = {}` + `* set body.field = value`. NO body inline tipo `* def body = { field: value, ... }` ni `read('classpath:...json')`.
- **Assertions field-by-field**: `And match response.field == '#type'`. NO `match response == read('classpath:schemas/...-match.json')`.

Razón: Mercantil exige visibilidad granular por campo en el pipeline (cada step se imprime con su valor), lo que permite auditoría línea por línea sin tener que abrir archivos auxiliares.

## Snippet completo

```gherkin
Feature: PN-PR-BFF-1234 Consulta saldo

  Background:
    * url mercantilUrl

  @happyPath @regression @smoke
  Scenario: PN-PR-BFF-1234 solicitud exitosa - consulta saldo cuenta ahorro
    Given path '/cuentas/123456789/saldo'
    And header Transaction-Id = '550e8400-e29b-41d4-a716-446655440000'
    And header Sid = 'SID-001'
    And header Auth-Id = 'AUTH-001'
    And header Content-Type = 'application/json'
    And header X-Channel = 'web'
    * def body = {}
    * set body.tipoCuenta = 'AHORRO'
    * set body.moneda = 'VES'
    And request body
    When method post
    Then status 200
    And match response.codigoRespuesta == '00'
    And match response.saldoDisponible == '#number'
    And match response.moneda == 'VES'

  @negative @regression
  Scenario: PN-PR-BFF-1234 solicitud fallida - tipo de cuenta invalido
    Given path '/cuentas/123456789/saldo'
    And header Transaction-Id = '550e8400-e29b-41d4-a716-446655440000'
    And header Sid = 'SID-001'
    And header Auth-Id = 'AUTH-001'
    And header Content-Type = 'application/json'
    And header X-Channel = 'web'
    * def body = {}
    * set body.tipoCuenta = 'INVALIDO'
    * set body.moneda = 'VES'
    And request body
    When method post
    Then status 400
    And match response.codigoRespuesta == 'E001'
```
