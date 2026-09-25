# Pre-flight check — Serenity WDIO greenfield

Antes de generar cualquier artefacto del stack `serenity-wdio` el agente debe validar el toolchain local (Node.js, WebdriverIO, Appium cuando aplique) y la accesibilidad del sistema bajo prueba declarado en `platform_context`. Si una validacion falla, aplicar la degradacion documentada y reportar al usuario antes de continuar. El protocolo de enforcement esta descrito en `[[calidad-pre-generation-protocol]]`.

## Validaciones obligatorias (todas las plataformas)

- `node --version` debe reportar Node.js 18 o superior. WebdriverIO v9 y Cucumber 11 requieren Node 18 LTS como minimo.
- `npx wdio --version` debe estar disponible (verifica que el CLI resuelva via `npx` o que `@wdio/cli` este en `package.json`).
- TypeScript `>=5.x` instalable (`npx tsc --version`); el arquetipo usa `strict: true`.
- Tras `npm install`, verificar que no exista duplicacion de `@cucumber/cucumber`: `find node_modules -name "@cucumber" -type d`. Si aparece mas de una ruta con `cucumber/` dentro, aplicar el fix de `overrides` documentado en `references/package-dependencies.md` antes de generar codigo — la duplicacion produce el error `instance of Cucumber that isn't running (status: PENDING)` al ejecutar, no al instalar, y es dificil de diagnosticar despues (ver `[[serenity-wdio-troubleshooting]]` Problema 10).

## Validaciones especificas por `platform_context`

- **`web` / `web_movil`**: `base_url` accesible via `curl -sI --max-time 5 "$BASE_URL"`. Timeout de 5 segundos. Si no responde, degradar la suite `web`/`web_movil` a `scaffold-only`.
- **`movil` (`android`)**: `adb devices` debe listar al menos un device o emulador cuando el modo de operacion pide runtime real. `aapt dump badging <apk>` debe leer `app_package` y `app_activity` reales; si difieren de los inputs declarados, ofrecer al usuario sobrescribir antes de generar. `appium --version` debe responder con Appium V2 (>= 2.0.0) y el driver `UiAutomator2` instalado.
- **`movil` (`ios`)**: requiere macOS con Xcode instalado. `/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" <app>/Info.plist` debe leer el `bundle_id` real; nunca suponerlo a partir del nombre del repositorio. `xcrun simctl list devices` debe listar al menos un simulador cuando el modo pide runtime real. El driver Appium requerido es `XCUITest`.
- **`desktop`**: requiere Windows con Appium Windows Driver instalado y la ruta al binario `.exe` verificada.
- **`api`**: `API_BASE_URL` accesible con la misma validacion de timeout que `base_url` web. Si hay auth, validar que el endpoint de token responda antes de generar `ChangeApiConfig`.

## Degradacion cuando el binario o el ambiente no estan disponibles

Si el device/emulador, el simulador iOS o la URL declarada no responden dentro del timeout:

1. Reportar el error exacto (timeout, DNS fail, 4xx/5xx, `adb` sin devices, simulador ausente).
2. Degradar a `scaffold-only` para la plataforma afectada. Los selectores quedan con el patron `DEFERRED` (ver `[[complete-deferred-locators]]`) y las configs WDIO se generan igual, sin ejecutar runtime.
3. Documentar la razon en `.evidence/preflight-result.json`.
4. Recordar al usuario que la compuerta smoke de esa plataforma no puede ejecutarse hasta resolver el bloqueo de ambiente.

## Script shippeable

El agente debe copiar `templates/preflight-serenity-wdio.sh` al proyecto generado bajo `scripts/preflight.sh`. El script reproduce las validaciones aplicables al `platform_context` declarado, en CI o en maquinas de desarrolladores. Ver `[[calidad-delivery-gate-contract]]` para la convencion de entregables y `[[calidad-post-generation-protocol]]` para el archivado del resultado.
