# CDC vs Schema-First — Cuándo Usar Cada Enfoque

Dos enfoques fundamentales de contract testing con tradeoffs distintos.

## Consumer-Driven Contracts (Pact)

El **consumer** declara qué espera del provider. El contrato (pact) se genera desde el test del consumer y se publica al broker. El provider luego verifica que cumple el contrato.

**Flujo:**
1. Consumer escribe test con mock del provider — declara la interaccion esperada.
2. Test genera `consumer-provider.json` (el pact).
3. Pact se publica al broker (Pactflow o self-hosted).
4. Provider corre `pact verify` contra los pacts del broker.
5. Si el provider no cumple, falla — el provider sabe que romperia al consumer.

**Ventajas:**
- El provider conoce con certeza qué consumers depende de él.
- El consumer no necesita esperar al provider para desarrollar — usa el mock.
- Detección temprana de breaking changes desde el lado del provider.

**Desventajas:**
- Requiere coordinacion organizacional (provider debe correr verifications).
- Solo funciona si los consumers son conocidos y dueños internos.
- Para APIs publicas con N consumers anónimos, NO escala.

## Schema-First (OpenAPI diff)

El **provider** publica la especificación (OpenAPI 3.x). Los consumers se generan o validan contra el spec. Los breaking changes se detectan comparando versiones del spec.

**Flujo:**
1. Provider mantiene `openapi.yaml` versionado en el repo.
2. CI corre `oasdiff breaking previous.yaml current.yaml`.
3. Si hay breaking change, falla el PR.
4. Consumers usan el spec para generar clients (`openapi-generator`) o validar respuestas (Karate `match schema`).

**Ventajas:**
- Funciona para APIs publicas (consumers desconocidos).
- Single source of truth (el spec).
- Tooling maduro (oasdiff, openapi-generator, Swagger UI).

**Desventajas:**
- El provider puede cambiar el spec sin saber que rompera a un consumer (si el consumer no esta declarado).
- No hay gate `can-i-deploy` por consumer — solo "este cambio es breaking en general".

## Matriz de decisión

| Criterio                                  | CDC (Pact)        | Schema-First (OpenAPI) |
| ----------------------------------------- | ----------------- | ---------------------- |
| Consumers internos conocidos              | Si, ideal         | Funciona               |
| Consumers externos / publicos             | No escala         | Si, ideal              |
| Mismo team consumer + provider            | Sobre-ingenieria  | Si                     |
| Diferentes teams / orgs                   | Si, ideal         | Funciona               |
| API publica con N consumers anonimos      | No                | Si, unica opcion       |
| Provider en Spring Java/Kotlin            | Si, con SCC       | Si                     |
| Detección breaking change per-consumer    | Si                | No (general)           |
| Setup inicial                             | Medio (broker)    | Bajo                   |
| Curva de aprendizaje                      | Media-alta        | Baja                   |
| Eventos asincronos                        | Pact Messaging    | AsyncAPI               |

## Recomendación por contexto Pragma

- **Cliente bancario con microservicios internos cross-team** (consumer team A, provider team B): **CDC con Pact**.
- **Cliente que expone API publica para partners** (consumers desconocidos): **Schema-First con OpenAPI diff**.
- **Monolito con un solo equipo**: probablemente **NINGUNO** — Karate `match schema` es suficiente.
- **Cliente con Kafka + microservicios** (eventos asincronos): **Schema Registry Confluent** para los topics + **Pact Messaging** o **AsyncAPI** para los contratos de payload.
- **Cliente Spring con varios microservicios**: **Spring Cloud Contract** como evolucion natural (contratos en el provider, stubs auto-publicados).

## Hibrido (frecuente en clientes grandes)

Combinar ambos:
- **OpenAPI** como source of truth de la API publica + diff para gates generales.
- **Pact** para los consumers internos criticos que necesitan gate `can-i-deploy`.

Esto da: defensa en profundidad (general breaking detection + per-consumer guarantees) a costo de doble mantenimiento.

## Anti-patterns

- Pact con consumers desconocidos — no se puede generar el pact si el consumer no lo escribe.
- OpenAPI diff sin versionado del spec — comparas contra nada.
- CDC sin broker — los pacts viven en filesystem, no hay can-i-deploy.
- Schema-First sin client generation — los consumers se desincronizan del spec.
