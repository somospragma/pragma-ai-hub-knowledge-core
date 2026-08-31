# Orquestador, Appium y cómo agregar un nuevo modo

## Flujo de selección del orquestador

```
node scripts/run.mjs --mode=<m> [--platform=<p>]
   │
   ├── mode=web         → .env.web         → wdio.web.conf.ts
   ├── mode=web_movil   → .env.web_movil   → wdio.web_mobile.conf.ts
   ├── mode=api         → .env.api         → wdio.api.conf.ts
   ├── mode=movil + platform=android → .env.movil.android → wdio.android.conf.ts
   ├── mode=movil + platform=ios     → .env.movil.ios     → wdio.ios.conf.ts
   ├── mode=desktop     → .env             → wdio.desktop.conf.ts
   └── mode=all         → secuencial: web, web_movil, movil(android), desktop, api
```

Tras ejecutar wdio, siempre corre `serenity-bdd run --features ./features` para generar el reporte.

## Appium (mobile)

El `wdio.android.conf.ts` y `wdio.ios.conf.ts` usan `@wdio/appium-service` que arranca Appium como child process automáticamente:

```typescript
services: [
  ['appium', {
    logPath: './logs/appium',
    args: {
      address: process.env.APPIUM_HOST ?? '127.0.0.1',
      port: Number(process.env.APPIUM_PORT ?? 4723),
      basePath: process.env.APPIUM_BASE_PATH ?? '/',   // Appium 3 usa '/' (no '/wd/hub')
    },
  }],
],
```

Pre-requisitos antes de correr mobile:

1. Emulador/dispositivo levantado (Android emulator running o iPhone conectado).
2. Drivers instalados: `appium driver list` — `appium-uiautomator2-driver` (Android) y `appium-xcuitest-driver` (iOS).
3. App compilada en `ANDROID_APP_PATH` o `IOS_APP_PATH`.
4. Para iOS real: WDA firmado con `IOS_XCODE_ORG_ID` y `IOS_WDA_BUNDLE_ID`.

## Cómo agregar un nuevo modo (sincronía atómica)

1. Crear `.env.<nuevo_modo>` con las variables específicas.
2. Crear `configs/wdio.<nuevo_modo>.conf.ts` que herede de `sharedConfig`:

```typescript
import { sharedConfig as shared } from './wdio.shared.conf';
const merge = (base, extra) => ({ ...base, ...extra, serenity: { ...base.serenity, ...extra.serenity } });
export const config = merge(shared, {
  specs: ['../features/<modulo>/Features/*.feature'],
  // capabilities, cucumberOpts, reporters, etc.
});
```

3. Agregar el mapping en `scripts/run.mjs`:

```javascript
const modeToConfig = {
  // existentes...
  <nuevo_modo>: './configs/wdio.<nuevo_modo>.conf.ts',
};

if (mode === '<nuevo_modo>') envFile = '.env.<nuevo_modo>';
```

4. Agregar el script npm en `package.json`:

```json
"test:<nuevo_modo>": "node ./scripts/run.mjs --mode=<nuevo_modo>"
```

5. Actualizar `README.md` con el nuevo modo y sus pre-requisitos.

Todos los 4 cambios deben ir en el mismo commit/PR (sincronía atómica).

## Salidas y artefactos

| Ruta | Generado por | Contiene |
|---|---|---|
| `target/site/serenity/index.html` | `serenity-bdd run` | Reporte HTML final |
| `target/site/serenity/*.json` | `ArtifactArchiver` | Resultados crudos por escenario |
| `allure-results/` | `@wdio/allure-reporter` (web) | Datos Allure |
| `reports/cucumber-report.json` | `cucumberOpts.format` | Cucumber JSON |
| `logs/appium/` | `@wdio/appium-service` | Logs de Appium |

## Comandos utilitarios del proyecto

```bash
# Reportes
npm run serenity:update    # descarga el JAR de Serenity BDD si falta
npm run serenity:report    # regenera el reporte sin re-correr tests
npm run serenity:clean     # limpia ./target

# Diagnóstico mobile
npx appium driver list
npx appium driver install uiautomator2
npx appium driver install xcuitest
adb devices
xcrun xctrace list devices

# Diagnóstico WDIO
npx wdio --version
```
