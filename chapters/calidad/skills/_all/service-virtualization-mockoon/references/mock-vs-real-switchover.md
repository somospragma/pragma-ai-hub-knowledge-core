
# Switchover mock → real — contrato de reemplazo

El mock existe para la fase de **construcción**; la certificación formal corre contra integraciones reales. Este documento define el contrato que hace ese reemplazo práctico y seguro: **el switchover es 100% configuración; si exige tocar un archivo de test, el diseño está mal y se corrige antes de entregar.**

## Principio de diseño: un único punto de verdad para la URL objetivo

Cada stack ya tiene un punto canónico de configuración; el mock se integra ahí como un ambiente más, nunca hardcodeado en tests:

| Stack | Punto de configuración | Contra mock | Contra real |
|---|---|---|---|
| Karate | `karate-config.js` con env `mock` (junto a `dev`/`qa`) que fija `baseUrl: 'http://localhost:3010/api'` | `mvn test -Dkarate.env=mock` | `mvn test -Dkarate.env=qa` |
| K6 | `config.js` lee `__ENV.BASE_URL` | `k6 run -e BASE_URL=http://localhost:3010/api tests/smoke-test.js` | `k6 run -e BASE_URL=https://api.qa.cliente.com tests/...` |
| Playwright (backend-level) | `BACKEND_URL` en `playwright.config.ts` / Page Objects | `BACKEND_URL=http://localhost:3010` | `BACKEND_URL=https://api.qa.cliente.com` |
| Appium (Serenity o WebdriverIO) | Base URL del backend en config del proyecto de tests (o build variant del APK acordado con dev) | APK apuntando al mock (si soporta override) | APK contra ambiente real |
| serenity-wdio | Variable de entorno por modo (`.env.<modo>`) cargada por `scripts/run.mjs` / config WDIO | `BASE_URL=http://localhost:3010` en el `.env.<modo>` correspondiente | `BASE_URL=https://api.qa.cliente.com` en el `.env.<modo>` correspondiente |

Reglas:

- Los tests referencian rutas relativas y la config resuelve el host (los stacks ya lo exigen; el mock no introduce excepciones).
- Auth: contra mock, el token puede ser dummy (`AUTH_TOKEN=mock-token`) porque Mockoon no lo valida, pero el test DEBE enviarlo igual que contra el real — así el switchover no cambia el shape del request.
- El data file del mock y la config del ambiente `mock` se entregan versionados: cualquier miembro del equipo reproduce la corrida de construcción con un comando.

## Datos: el switchover de data_strategy

- Contra mock: datos sintéticos (Faker + seed) alimentan tanto los payloads del test como los buckets del mock — coherencia por diseño.
- Contra real: los mismos builders/factories generan los payloads, pero el estado inicial lo provee el ambiente (seeding/cleanup de `[[calidad-test-data-management]]`). Si el ambiente real exige datasets del cliente, ese es un input del checklist de certificación, no un cambio de código.
- Aserciones: validar **contrato y reglas de negocio**, no valores que solo existen en el mock (ej. nunca asertar `email == 'test@example.com'` si el email lo generó Faker; asertar formato/presencia/eco del request).

## Checklist de certificación (gate para pasar de mock a real)

Antes de declarar `certification: certified`:

1. Ambiente real desplegado y accesible; `execution_target: real` en la corrida.
2. Config apuntada al ambiente real; **cero diffs** en archivos de test respecto a la corrida contra mock (verificable con `git diff --stat -- tests/ src/`).
3. Credenciales/tokens reales provistos por el canal seguro del proyecto (`[[calidad-security-testing]]`, secrets management) — jamás en el data file ni en el repo.
4. Si es front: validación de drift del locator map contra el DOM/jerarquía real ejecutada ANTES de la suite (`[[calidad-ui-locator-map-contract]]`).
5. Smoke gate 1:1 contra el real. Los fallos aquí se trían con `[[calidad-failure-triage-and-classification]]`; la categoría típica es **contract drift** (el desarrollo divergió del spec con que se construyó el mock) — eso es hallazgo reportable, no un bug del test, y NO se "arregla" relajando aserciones.
6. Suite completa (y en K6, la ejecución real de load/stress vía `[[calidad-calibrate-k6-thresholds]]` bajo ventana coordinada).
7. Delivery gate actualizado: `execution_target: real`, `certification: certified`, evidencia de la corrida real persistida.

## Ciclo de vida del mock después del switchover

El mock no se borra: queda como herramienta de (a) reproducción determinista de bugs de contrato, (b) desarrollo offline de nuevos tests, (c) pipelines de construcción en PRs donde el ambiente real no está disponible. Lo que cambia es su rol: deja de ser el target del delivery y pasa a ser tooling — los pipelines de certificación y los reportes ejecutivos solo consumen corridas `execution_target: real`.
