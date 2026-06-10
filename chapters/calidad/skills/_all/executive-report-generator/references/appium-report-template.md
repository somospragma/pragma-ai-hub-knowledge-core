# Plantilla específica de Appium para el reporte ejecutivo

Esta plantilla guía las secciones del reporte ejecutivo cuando `framework = appium`. Complementa `report-structure.md`. Se invoca desde el Paso 6 del `SKILL.md`. Foco en cumplimiento por feature, locators auto-discovery vs deferred, y matrix device-a-device.

## Fuentes primarias

- `target/site/serenity/` (reporte agregado Serenity con JSON y HTML).
- `target/site/serenity/serenity-summary.json` con totales por feature y device.
- `.evidence/locators-discovered.json` (si se aplicó auto-discovery).
- `metadata.json` por corrida (timestamp, commit, branch, environment, devices, app_package, app_activity).

## Sección 2 — Cumplimiento de SLAs (vista Appium)

Mapear desde `STRATEGY.md`:

- Cumplimiento por feature: pasados / totales por feature en `@android @smoke`.
- Cumplimiento por device en la matrix declarada (no mezclar — un device puede pasar y otro fallar).
- Locators cubiertos: auto-discovery resueltos vs deferred pendientes (`TODO: update real locator`).

Tabla:

| Métrica | Declarado | Observado | Cumple |
|---|---|---|---|
| Features pasando en device Pixel 6 emulador | 100% | 100% | OK |
| Features pasando en device Galaxy S22 real | 100% | 80% | FAIL |
| Locators reales resueltos | >= 90% | 72% | FAIL |

## Sección 3 — Resultados por feature y por device

Tabla principal por feature:

| Feature | Escenarios @smoke | Pasados | Fallidos | % éxito | Locators TODO | Estado |
|---|---|---|---|---|---|---|
| login.feature | 2 | 2 | 0 | 100% | 0 | OK |
| dashboard.feature | 4 | 3 | 1 | 75% | 2 | parcial |

### Matrix device-a-device (pass / fail por device y feature)

| Feature | Pixel 6 (emulador) | Galaxy S22 (real) | Galaxy A52 (real) |
|---|---|---|---|
| login.feature | pass | pass | pass |
| dashboard.feature | pass | fail | pass |
| checkout.feature | pass | pass | fail |

Cualquier "fail" en una celda se desglosa en la sección de hallazgos con stage, logcat y screenshot Serenity.

### Sub-tabla: locators auto-discovery resueltos vs deferred

Si el workflow eligió auto-discovery en el Paso 4:

| Page Object | Locators totales | Resueltos (auto-discovery) | Deferred (TODO) | Score promedio confianza |
|---|---|---|---|---|
| LoginPage | 5 | 5 | 0 | 0.94 |
| DashboardPage | 12 | 9 | 3 | 0.78 |
| CheckoutPage | 8 | 4 | 4 | 0.61 |

Los locators deferred pendientes deben completarse con `[[complete-deferred-locators]]` antes de promover.

## Sección 4 — Comparación entre corridas (vista Appium)

| Feature | Device | Corrida anterior | Corrida actual | Delta | Locators resueltos nuevos |
|---|---|---|---|---|---|
| login.feature | Pixel 6 emulador | 2/2 | 2/2 | 0 | (ninguno) |
| dashboard.feature | Galaxy S22 real | 2/4 | 3/4 | +1 | btn_continue, lbl_total |

## Sección 7 — Anexos específicos Appium

- Comando exacto (`./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`).
- Path al reporte Serenity: `target/site/serenity/index.html`.
- Capabilities aplicados (`app_package`, `app_activity`, `platform_version`, `device_name`, `automation_name`, `appium_server_url`).
- Versión de Appium server, Android SDK, Java, Gradle.
- APK ejecutado (path y checksum si está en metadata).
- `.evidence/locators-discovered.json` si aplica.
