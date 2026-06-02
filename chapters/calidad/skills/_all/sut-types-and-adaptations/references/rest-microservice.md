# REST Microservice — Patrones y Adaptación

## Patrones canónicos

- **OpenAPI-first**: el contrato OpenAPI 3.x (o Swagger 2.0 en legacy) es la fuente única de verdad. Los tests deben validar request/response contra el schema, no contra ejemplos congelados.
- **Idempotencia**: `GET`, `PUT`, `DELETE` deben ser idempotentes. `POST` usualmente no lo es salvo que use `Idempotency-Key` (Stripe-style). Validar con escenarios que repitan la misma operación con la misma clave.
- **Paginación**: cursor-based (recomendada para consistencia) vs offset/limit. Validar `next`, `prev`, `total`, comportamiento en el último page y cuando el set cambia entre requests.
- **Versionado**: en path (`/v1/...`), en header (`Accept: application/vnd.api+json;version=1`) o en query (`?version=1`). Validar coexistencia de versiones y deprecation headers (`Sunset`, `Deprecation`).
- **ETag / If-None-Match / If-Match**: caching y optimistic concurrency. Validar `304 Not Modified` con `If-None-Match` y `412 Precondition Failed` con `If-Match` divergente.
- **Content negotiation**: `Accept` y `Content-Type`. Validar al menos `application/json`; si el endpoint soporta `application/xml` o `text/csv`, escenarios por cada tipo.
- **Status codes**: usar los códigos correctos (`201 Created` con `Location`, `204 No Content` sin body, `409 Conflict` para violaciones de estado, `422 Unprocessable Entity` para validación semántica).

## Framework primario

**Karate**. El DSL es declarativo, soporta JSON/XML/multipart/form, tiene matchers profundos (`match response ==`, `match each`, `#regex`, `##null`), reutiliza features como background, soporta llamadas paralelas y reportes Cucumber-style listos para evidencia.

## Complementarios

- **k6** para perf: derivar VUs/stages del peak QPS real (ver `[[k6-thresholds-three-tiers]]`).
- **Pact** para contract testing consumer-driven cuando hay múltiples consumidores y se quiere prevenir breaking changes.
- **Schemathesis** para fuzzing del contrato OpenAPI (cubre OWASP API1, API3, API8 parcial).

## Antipatrones

- Hardcodear IDs y tokens en los `.feature` (rompe en cada ambiente).
- Validar solo el happy path; sin cobertura negativa documentada (`[[karate-negative-coverage-formula]]`).
- Validar respuestas contra ejemplos del Swagger en lugar de contra el schema (los ejemplos suelen estar desactualizados).
- Tests que dependen del orden de ejecución (cada feature debe ser independiente o explícitamente encadenado vía `karate.callSingle`).
- Asumir que `POST` repetido produce el mismo recurso sin `Idempotency-Key`.
