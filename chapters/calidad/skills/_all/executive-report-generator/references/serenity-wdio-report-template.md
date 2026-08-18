# Plantilla específica de serenity-wdio para el reporte ejecutivo

Esta plantilla guía las secciones del reporte ejecutivo cuando `framework = serenity-wdio`. Complementa `report-structure.md`. Se invoca desde el Paso 6 del `SKILL.md`. Foco en cumplimiento por plataforma (`web`, `web_movil`, `movil` Android/iOS, `desktop`, `api`), estado del workaround `NATIVE_APP` y locators `DEFERRED` pendientes.

## Fuentes primarias

- `target/site/serenity/` (reporte agregado Serenity/JS) + `allure-results/` (`@wdio/allure-reporter`).
- `results/<plataforma>/<timestamp>/*-cucumber.json` (`wdio-cucumberjs-json-reporter`).
- `results/web/<timestamp>/video/` (`wdio-video-reporter`, solo web).
- `metadata.json` por corrida (timestamp, commit, branch, environment, `mode`, `platform`, tags, app_package/app_activity o bundle_id si mobile).
- `.evidence/preflight-result.json` si hubo degradación de alguna plataforma a `scaffold-only`.

## Sección 2 — Cumplimiento de SLAs (vista serenity-wdio)

Mapear desde `STRATEGY.md`, una fila por plataforma declarada en el proyecto:

- Cumplimiento por plataforma: pasados / totales por `--mode` (y `--platform` en móvil) en `@smoke`.
- `enforceWebDriverClassic: true` presente en el 100% de las capabilities `web` y `web_movil`.
- Locators reales resueltos: `DEFERRED` restantes vs total de selectores declarados (ver `[[complete-deferred-locators]]`).
- Workaround de window handles activo en `wdio.shared.conf.ts` cuando el proyecto incluye alguna plataforma móvil.

Tabla:

| Métrica | Declarado | Observado | Cumple |
|---|---|---|---|
| Escenarios `@smoke` pasando en `web` | 100% | 100% | OK |
| Escenarios `@smoke` pasando en `movil` (android) | 100% | 100% | OK |
| Escenarios `@smoke` pasando en `movil` (ios) | 100% | 0% (sin simulador) | partial |
| Locators reales resueltos | >= 90% | 85% | FAIL |

## Sección 3 — Resultados por plataforma y por feature

Tabla principal por plataforma:

| Plataforma (`--mode` / `--platform`) | Features `@smoke` | Pasados | Fallidos | % éxito | Locators `DEFERRED` | Estado |
|---|---|---|---|---|---|---|
| `web` | 3 | 3 | 0 | 100% | 0 | OK |
| `movil` / `android` | 2 | 2 | 0 | 100% | 1 | parcial |
| `movil` / `ios` | 2 | 0 | 0 | — | 4 | sin ejecutar (`scaffold-only`) |
| `api` | 4 | 4 | 0 | 100% | 0 | OK |

### Sub-tabla: locators `DEFERRED` pendientes por canal

| UI Mapping | Canal | Locators totales | Resueltos | `DEFERRED` (TODO) | Justificación registrada |
|---|---|---|---|---|---|
| `LoginUI` (web) | web | 4 | 4 | 0 | — |
| `LoginUI.android` | movil/android | 4 | 3 | 1 | pendiente `content-desc` en sprint 42 |
| `LoginUI.ios` | movil/ios | 4 | 0 | 4 | binario `.app` no disponible en esta corrida |

Los locators `DEFERRED` pendientes deben completarse con `[[complete-deferred-locators]]` antes de promover a `success`.

### Sub-tabla: estado del workaround `NATIVE_APP` (solo si el proyecto incluye móvil)

| Verificación | Estado |
|---|---|
| `overwriteCommand('getWindowHandle', ...)` en `wdio.shared.conf.ts` | presente |
| `overwriteCommand('getWindowHandles', ...)` en `wdio.shared.conf.ts` | presente |
| Acotado a `browser.isMobile === true` | sí |
| Replicado indebidamente en Tasks/Interactions/Steps | no detectado |

## Sección 4 — Comparación entre corridas (vista serenity-wdio)

| Plataforma | Corrida anterior | Corrida actual | Delta | Locators `DEFERRED` resueltos nuevos |
|---|---|---|---|---|
| `web` | 2/3 | 3/3 | +1 | `button_submit` |
| `movil` / `android` | 1/2 | 2/2 | +1 | `input_password` |

## Sección 7 — Anexos específicos serenity-wdio

- Comando exacto por plataforma (`node ./scripts/run.mjs --mode=<modo> [--platform=<android|ios>] --tags=@smoke`).
- Path al reporte Serenity: `target/site/serenity/index.html`; Allure: `allure-results/` → `allure-report/`.
- Capabilities aplicadas por config (`configs/wdio.<modo>.conf.ts`): `browserName`/`enforceWebDriverClassic` (web/web_movil), `platformName`/`automationName`/`app` (movil/desktop), `baseUrl` (api).
- Bundle ID / Package verificado (`aapt dump badging` / `PlistBuddy`) por corrida móvil.
- Video de la corrida web (`wdio-video-reporter`), si está habilitado.
- `.evidence/preflight-result.json` si alguna plataforma quedó en `scaffold-only` por falta de ambiente (device, simulador, navegador, URL).
