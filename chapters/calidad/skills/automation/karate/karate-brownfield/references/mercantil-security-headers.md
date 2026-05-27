
# Headers obligatorios Mercantil

Estos headers son **obligatorios en todos los endpoints Mercantil**, incluso cuando el spec OpenAPI no los marca como required. Tratarlos siempre como `required` para fines de cobertura.

| Header | Valor / formato | Notas |
|---|---|---|
| `Transaction-Id` | UUID v4 | Formato validable: cobertura `@invalid-header-format`. |
| `Sid` | string opaco (session id) | Asignado por el canal. |
| `Auth-Id` | string opaco (auth context) | Token interno post-login. |
| `Content-Type` | `application/json` (o `application/jose` si cifrado) | |
| `X-Channel` | uno de `web` \| `mobile` \| `atm` | Enum: cobertura `@invalid-header-format` con valor fuera del enum. |

## Cobertura obligatoria por header

Para CADA header de la tabla:

- **1 escenario** `@negative @missing-header` — omitir el header.
- **1 escenario adicional** `@negative @invalid-header-format` — sólo si el header tiene formato validable (UUID, enum). Aplica a `Transaction-Id` y `X-Channel`.

Total mínimo de escenarios de headers para un endpoint Mercantil: `5 missing-header + 2 invalid-header-format = 7`. Súmalos a la fórmula de `[[karate-negative-coverage-formula]]`.

## Ejemplo de escenario `@invalid-header-format`

```gherkin
@negative @regression @invalid-header-format
Scenario: PN-PR-BFF-1234 solicitud fallida - Transaction-Id con formato invalido
  Given path '/cuentas/123456789/saldo'
  And header Transaction-Id = 'no-es-un-uuid'
  And header Sid = 'SID-001'
  And header Auth-Id = 'AUTH-001'
  And header Content-Type = 'application/json'
  And header X-Channel = 'web'
  * def body = {}
  * set body.tipoCuenta = 'AHORRO'
  * set body.moneda = 'VES'
  And request body
  When method post
  Then status 400
```
