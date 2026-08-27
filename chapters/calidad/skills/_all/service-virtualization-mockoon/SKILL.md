---
id: calidad-service-virtualization-mockoon
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Service virtualization con Mockoon para construir y validar pruebas antes de que el backend exista: environment JSON versionable, mock desde OpenAPI, CRUD stateful, templating determinista, proxy/hybrid, CLI en CI y switchover a integraciones reales."
tags: [mockoon, mock, service-virtualization, shift-left, openapi, soap, cli, determinism, switchover]
---

# Service Virtualization con Mockoon — Mock de Servicios para Construir Pruebas

## Cuándo aplicar

Aplica cuando `[[calidad-sut-readiness-gate]]` resolvió `execution_target: mock | hybrid` y el mock requerido es a nivel de red/backend (API REST o SOAP). Cubre los stacks:

- **Karate**: el mock es el SUT temporal; la suite completa corre contra él.
- **K6**: el mock valida la construcción de los scripts (smoke 1:1); jamás métricas de carga.
- **Playwright**: mock a nivel backend cuando `page.route()` no alcanza (webviews, tráfico que no pasa por el browser context, mock compartido con la suite Karate). `page.route()` sigue siendo la primera opción front-level — ver [[calidad-playwright-greenfield]] (consultar `references/execution-modes-live-mocked-hybrid.md` en su subfolder).
- **Appium** (Serenity o WebdriverIO): solo si el APK existe y permite override de base URL hacia el mock.
- **serenity-wdio**: mock a nivel backend para el canal `api`, o para `web`/`web_movil`/`movil` cuando el backend no está listo y el punto de configuración lo permite (mismo patrón que Playwright/Appium: mock compartido si aplica).

**Por qué Mockoon**: open source MIT (todo lo necesario para CI es gratis; lo pago es Mockoon Cloud, que no se necesita), data file JSON único versionable en git, arranque directo desde OpenAPI, CRUD stateful con correlación de IDs, templating Faker con seed determinista, proxy mode para hybrid, CLI + Docker para CI. Alternativas solo en sus nichos: WireMock (verificación de invocaciones nativa, fault injection), Prism (validación estricta contra spec), MSW (front-end puro, inútil como SUT de red).

## Instrucción

1. **Generar el environment** — Invocar `[[calidad-generate-mockoon-environment-prompt]]` con el spec y la user story. El data file se persiste en `mocks/mockoon/environment.json` dentro del proyecto de tests y **se versiona en git** junto a la suite (es parte del entregable). Formato en `references/mockoon-environment-file.md`; semilla desde OpenAPI en `references/openapi-to-mock.md`; SOAP en `references/soap-xml-mocking.md`.
2. **Modelar estado para CRUDs** — Todo recurso con flujo create → read → update → delete se modela como CRUD route ligada a un data bucket, para que la correlación de IDs del test funcione contra el mock igual que contra el SUT real. Ver `references/stateful-crud-and-data-buckets.md`.
3. **Hacer el mock determinista** — Templating con Faker usa el mismo seed que la suite (`--faker-seed` = `FAKER_SEED` de `[[calidad-test-data-management]]`) y locale de la jurisdicción. Entre corridas, purgar estado vía Admin API (`POST /mockoon-admin/state/purge`). Ver `references/dynamic-templating-and-faker-seed.md`.
4. **Levantar el mock** — Local: `mockoon-cli start --data mocks/mockoon/environment.json --port 3010`. CI: Docker `mockoon/cli` o GitHub Action `mockoon/cli-action@v3`. Comandos verificados (incluido cómo detenerlo: no existe `stop`) en `references/cli-docker-and-ci.md`.
5. **Apuntar la suite por configuración** — El único cambio permitido entre mock y real es la URL objetivo en el punto de configuración del stack (env/profile). Mecanismo por stack y checklist de certificación en `references/mock-vs-real-switchover.md`.
6. **Hybrid (partial mocking)** — Con desarrollo parcial, activar `proxyMode` con `proxyHost` al backend real: rutas declaradas se mockean, el resto hace passthrough. Documentar en STRATEGY.md qué rutas están mockeadas.
7. **Registrar en el delivery gate** — `execution_target`, `certification: pending_real_integration`, path del data file y seed usado. Ver `[[calidad-delivery-gate-contract]]`.

## Limitaciones que el agente debe conocer

- No mockea gRPC ni GraphQL nativo (workaround GraphQL: ruta HTTP `POST /graphql` con rules sobre el body); sin SSE ni mTLS. WebSockets sí desde v9.
- No valida requests contra el spec automáticamente (eso es Prism); desde v9 hay regla opt-in "valid JSON Schema" por ruta.
- Sin `verify()` de invocaciones nativo: se consulta `GET /mockoon-admin/logs` desde el test si hace falta.
- Estado en memoria: se pierde al reiniciar — es una ventaja para determinismo (purge entre corridas), no un bug.
- Sin benchmarks publicados de performance bajo carga: por eso K6 contra mock se limita a smoke 1:1.

## Restricciones

- **NUNCA** presentar resultados contra mock como certificación del SUT (`[[calidad-sut-readiness-gate]]`, regla maestra).
- **NUNCA** ejecutar `load/stress/spike/soak` K6 contra el mock ni reportar sus métricas como evidencia de performance.
- **NUNCA** enriquecer el mock con reglas de negocio que no estén en el spec, la firma o la user story: el mock refleja el contrato, no lo inventa.
- **NUNCA** dejar el mock como dependencia permanente de la suite: el switchover a real es parte del contrato de entrega y se demuestra en `next_steps`.
- **SIEMPRE** versionar el data file junto al proyecto de tests y regenerar/actualizar cuando el spec cambie (el mock desactualizado produce falsos verdes, el equivalente de un contrato drift silencioso).
- En brownfield, el mock sirve solo a los tests nuevos de la corrida; tests preexistentes no se reapuntan ni se modifican.

## Cross-links

- `references/mockoon-environment-file.md`
- `references/openapi-to-mock.md`
- `references/stateful-crud-and-data-buckets.md`
- `references/dynamic-templating-and-faker-seed.md`
- `references/soap-xml-mocking.md`
- `references/cli-docker-and-ci.md`
- `references/mock-vs-real-switchover.md`
- `[[calidad-sut-readiness-gate]]`, `[[calidad-generate-mockoon-environment-prompt]]`, `[[calidad-test-data-management]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-delivery-gate-contract]]`
