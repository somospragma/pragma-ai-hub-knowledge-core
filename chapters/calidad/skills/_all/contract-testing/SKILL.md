---
id: calidad-contract-testing
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Estrategia de contract testing: consumer-driven (Pact), schema-first (OpenAPI diff), provider-side (Spring Cloud Contract), y registry de esquemas."
tags: [contract-testing, pact, spring-cloud-contract, openapi-diff, schema-registry, pactflow]
---

# Contract Testing — Estrategia de Contratos entre Servicios

## Cuándo aplicar

Aplica este skill cuando:

- La arquitectura del cliente es de **microservicios** y un cambio en un provider puede romper a uno o más consumers sin que las pruebas E2E lo detecten.
- Hay **integración con sistemas externos versionados** (APIs públicas, APIs de partners, sistemas legacy que publican esquemas).
- Se necesita **detección temprana de breaking changes** antes de que lleguen a integración o producción.
- Las pruebas E2E o de integración son lentas, caras o frágiles — los contract tests dan feedback en segundos.
- El cliente tiene equipos distribuidos donde consumer y provider son **propiedad de teams distintos** (Conway's Law aplica).

No aplica como **único** mecanismo: contract testing valida el contrato (estructura, tipos, requeridos), no el comportamiento funcional. Siempre se combina con suites funcionales (`[[karate-greenfield]]`, `[[karate-brownfield]]`, `[[playwright-greenfield]]`).

Activa este skill en combinación con `[[calidad-chapter-perspective]]` para confirmar que el contexto del cliente justifica la inversión (un monolito sin integraciones externas raramente lo necesita) y con `[[calidad-mandatory-inputs-protocol]]` para inventariar pares consumer-provider antes de elegir herramienta.

## Instrucción

1. **Inventariar consumer-provider pairs** — Mapea cada API documentada contra sus consumers conocidos. Para cada par: ¿quién es dueño del consumer?, ¿quién del provider?, ¿comparten organización o son cross-team/cross-company?, ¿la API es interna o pública?. Documenta el inventario como artefacto inicial.
2. **Elegir enfoque** según el inventario:
    - **CDC con Pact** si consumers son conocidos, internos al cliente, y se quiere que ellos manden el contrato (consumer-driven).
    - **Schema-first con OpenAPI diff** si la API es pública o el provider manda el contrato (API-first).
    - **Provider-driven con Spring Cloud Contract** si el stack del provider es Spring (Java/Kotlin) y se quieren stubs auto-generados para los consumers.
    - Detalle de decisión en `references/cdc-vs-schema-first.md`.
3. **Setup del broker o registry** según el enfoque:
    - Pact: Pactflow (managed, recomendado) o Pact Broker self-hosted Docker. Ver `references/pact-broker-pactflow.md`.
    - OpenAPI diff: repositorio Git con spec versionado + CI step de diff.
    - Spring Cloud Contract: Maven repository o Pact Broker para distribuir stubs.
    - Schema Registry (Avro/Protobuf/JSON Schema en Kafka): Confluent Schema Registry. Ver `references/schema-registry-confluent.md`.
4. **Escribir consumer tests que generan pacts** — En el repo del consumer, mock del provider con expectations explícitas. Cada test ejecutado genera/actualiza el pact JSON. Snippet por lenguaje en `references/pact-consumer-tests.md`.
5. **Verificar provider contra pacts** — En el repo del provider, ejecutar `pact verify` contra los pacts publicados. Cada interacción debe pasar contra el provider real (o con state handlers). Snippets en `references/pact-provider-verification.md`.
6. **Integrar gate `can-i-deploy` en pipeline** — Antes de deploy, ejecutar `pact-broker can-i-deploy --pacticipant X --version Y --to-environment prod`. Si algún pact compatible falla, el deploy se bloquea. Detalle en `references/pact-broker-pactflow.md`.
7. **Versionar contratos** — Cada pact se etiqueta con la versión del consumer (típicamente el git SHA) y el ambiente al que se promociona (`dev`, `qa`, `prod`). El broker mantiene la matriz de compatibilidad entre versiones.

## Restricciones

- **Contract testing ≠ E2E ni integration testing.** Solo valida que la forma del contrato se respeta — NO valida lógica de negocio. Por ejemplo, un pact puede pasar verificando que `POST /orders` devuelve `{id, status}`, pero NO valida que el `status` sea correcto según las reglas de negocio.
- **NO sustituye tests funcionales** generados con Karate/Playwright. Contract tests responden "¿el provider rompe el contrato?"; tests funcionales responden "¿el sistema hace lo correcto?".
- **NO usar Pact para casos no-RPC**. Pact está diseñado para request/response síncrono. Para eventos asíncronos (Kafka, RabbitMQ, SNS/SQS), usar **Pact Messaging** o **AsyncAPI**. Detalle en `references/asyncapi-event-contracts.md`.
- **NO publicar pacts desde branches feature** al broker de producción sin tagging adecuado. Usar tags (`feature/X`, `main`, `prod`) para aislar.
- **NO confundir Karate `-match.json` con contract testing**. Karate match valida la respuesta de UN provider en pruebas locales; NO comparte contrato versionado entre teams. Detalle en `references/contract-testing-vs-karate-match.md`.
- Para schemas en streaming (Kafka), usar **compatibility modes estrictos** (BACKWARD o FULL) para evitar consumer breakage. Ver `references/schema-registry-confluent.md`.
- Integrar contratos como artefactos de evidencia siguiendo `[[calidad-test-evidence-and-traceability]]` — los pacts versionados son auditables.

## Cross-links

- `references/cdc-vs-schema-first.md`
- `references/pact-consumer-tests.md`
- `references/pact-provider-verification.md`
- `references/pact-broker-pactflow.md`
- `references/openapi-diff-breaking-changes.md`
- `references/spring-cloud-contract.md`
- `references/asyncapi-event-contracts.md`
- `references/schema-registry-confluent.md`
- `references/contract-testing-vs-karate-match.md`
