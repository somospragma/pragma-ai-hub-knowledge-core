
# Payloads cifrados — detección y escenarios

## Señales que indican cifrado

- Header `X-Encrypted: true` en el spec o en la firma.
- `Content-Type: application/jose` o `application/jwt`.
- Campo `encryptedPayload` (o equivalente) en el body del request/response.
- La firma del servicio menciona cifrado, JWE/JWS, llave pública, KMS.
- Cliente del dominio banca/fintech: **preguntar siempre** si los endpoints usan cifrado a nivel aplicación.

Si detectas al menos una señal, añade los escenarios de esta sección.

## Escenarios obligatorios (mínimo 3, óptimo 4)

| Tag | Propósito |
|---|---|
| `@happy-path @encrypted` | Request cifrado válido con llave de test → respuesta correcta. |
| `@negative @invalid-encryption` | Payload cifrado con llave incorrecta o formato JWE inválido. |
| `@negative @plaintext-body-on-encrypted-contract` | Enviar body plano cuando el contrato exige cifrado. |
| `@negative @missing-encryption-header` | Omitir `X-Encrypted: true` o `Content-Type` cifrado. |

## Patrón de llamada al helper

```gherkin
@happy-path @encrypted
Scenario: Transfer - happy path encrypted
  * def plainBody = read('classpath:com/testing/bodies/transfer.json')
  * def encrypted = karate.call('classpath:helpers/encrypt.feature', { payload: plainBody })
  Given path '/transfers'
  And header X-Encrypted = 'true'
  And header Content-Type = 'application/jose'
  And request encrypted.cipherText
  When method post
  Then status 201
```

## Restricciones

- **NUNCA hardcodear** payloads cifrados literales en el `.feature` o en archivos JSON. El cipherText cambia por timestamp/IV y se vuelve no reproducible.
- **NUNCA usar llaves de producción.** Sólo test keys provistas por el cliente, almacenadas fuera del repo (variables de entorno, vault, archivo no versionado).
- Si el cliente no provee llaves de test, detente y solicítalas; no inventes llaves.
