# Contract Testing vs Karate `match` — Cuándo Cada Uno

Una confusión frecuente: "ya tenemos Karate `match schema` validando las respuestas, ¿necesitamos Pact?"

Respuesta: **son complementarios**. Resuelven problemas distintos.

## Karate `-match`/`match schema`

Karate valida la respuesta de **un provider concreto** en pruebas locales o de CI del consumer.

```gherkin
Scenario: Get user returns expected schema
    Given path '/users/42'
    When method GET
    Then status 200
    And match response ==
    """
    {
      id: '#number',
      name: '#string',
      email: '#regex [a-z]+@[a-z]+\\.[a-z]+',
      createdAt: '#? _ =~ /^\\d{4}-\\d{2}-\\d{2}T/'
    }
    """
```

**Alcance:**
- Vive en el repo del consumer (o del team de QA centralizado).
- Se ejecuta contra el provider real (staging/QA).
- Si el provider cambia su contrato, el match falla → consumer team se entera.

**Limitaciones:**
- El **provider no sabe** que ese match existe — puede romper el contrato sin saber a quién afecta.
- No hay gate `can-i-deploy` — el provider deploya sin validar consumers.
- No hay catálogo de contratos versionados — cada consumer hace su propio match.

## Pact (CDC)

Pact distribuye el contrato al provider y bloquea su deploy si rompe a un consumer.

**Alcance:**
- El contrato (pact) se publica al broker.
- El provider corre `pact verify` contra el broker → sabe explícitamente qué consumers tiene.
- Gate `can-i-deploy` bloquea el deploy si rompe a algún consumer en el ambiente target.

**Limitaciones:**
- Requiere broker + setup organizacional.
- Solo valida contrato, NO comportamiento.
- Mock provider en consumer tests — NO valida que el provider real esté operativo.

## Tabla comparativa

| Dimensión                           | Karate `match`              | Pact                          |
| ----------------------------------- | --------------------------- | ----------------------------- |
| Validación contra provider real     | Si                          | No (solo verifier en provider)|
| Conocimiento del provider sobre consumer | No                     | Si                            |
| Gate de deploy del provider         | No                          | Si                            |
| Validación de schema                | Si                          | Si                            |
| Validación de comportamiento        | Si (assertions sobre datos) | No                            |
| Tests funcionales E2E               | Si                          | No                            |
| Versionado del contrato             | No (cambia con el test)     | Si (broker + versions)        |
| Setup                               | Trivial (parte de Karate)   | Medio (broker + libs)         |

## Recomendación Pragma — combinar

### En el repo del consumer

```
src/test/karate/
  contracts/             # Karate match contra provider real (smoke + schema)
    users-api.feature
  functional/            # Karate funcional (comportamiento, flujos)
    create-order.feature

tests/contracts/         # Pact consumer tests (mock provider, generate pact)
  users-api.pact.test.ts
```

- **Karate contracts**: validan schema y disponibilidad contra el provider real desplegado. Detectan que el provider rompió algo (después del hecho).
- **Pact**: genera contrato versionado, lo publica al broker. Previene que el provider rompa algo (antes del hecho).
- **Karate funcional**: valida flujos de negocio E2E. Único responsable de "el sistema hace lo correcto".

### En el repo del provider

```
src/test/java/
  contract/              # Pact verifier (download pacts, verify)
    UsersServiceProviderTest.java
  integration/           # Tests de integración propios (DB, mocks)
```

- **Pact verifier**: gate de deploy. Bloquea si rompe a algún consumer registrado en el broker.

### En el pipeline

```yaml
# Consumer pipeline
jobs:
  - karate-contracts          # validación contra provider real
  - karate-functional         # comportamiento E2E
  - pact-consumer-test        # genera pact
  - publish-pact              # publica al broker

# Provider pipeline
jobs:
  - unit-tests
  - integration-tests
  - pact-verify               # download + verify all pacts
  - can-i-deploy              # gate antes de deploy
  - deploy
  - record-deployment         # registra en broker
```

## Cuándo Karate `match` ES suficiente

- Cliente con **un solo team** y un solo consumer del provider.
- Provider **monolito** sin necesidad de gate `can-i-deploy`.
- Proyecto **corto** (POC, prototipo) donde el overhead de Pact no se justifica.
- Cliente sin **infraestructura para broker** (ni Pactflow ni self-hosted Pact Broker viable).

## Cuándo Karate `match` NO ES suficiente

- Microservicios con **N consumers** por provider — necesitas saber a quién rompes.
- Equipos distribuidos donde provider y consumer son **cross-team** o **cross-company**.
- Sistemas con **deploys independientes** (provider y consumer deployan en pipelines distintos).
- Sistemas con compliance estricto (financiero, salud, gobierno, certificaciones SOC 2/ISO 27001) donde el contrato debe ser **versionado y auditable**.

## Recomendación final

**En proyectos Pragma típicos (microservicios, deploys frecuentes, equipos cross-team): usar AMBOS.**

- Karate `-match.json` aporta validación local + schema validation barato.
- Pact aporta gate de deploy + traceability + per-consumer awareness.

El overhead de Pact se paga 10x cuando previene un breaking change en producción que habría afectado a 5 consumers descubiertos solo en triage post-incident.

## Cross-link

- Para detalle de Pact, ver `pact-consumer-tests.md` y `pact-provider-verification.md`.
- Para el equivalente schema-first (sin Pact), ver `openapi-diff-breaking-changes.md`.
- Karate match patterns están documentados en el reference `karate-contract-testing-match-patterns.md` del dominio Karate.
