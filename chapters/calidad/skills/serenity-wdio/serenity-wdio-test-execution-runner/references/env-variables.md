# Variables de entorno por archivo .env.*

## .env (base, siempre cargado si no hay otro)

```
APPIUM_HOST=127.0.0.1
APPIUM_PORT=4723
APPIUM_BASE_PATH=/
NO_RESET=true
```

## .env.api

```
API_BASE_URL=https://httpbin.org   # consumido por wdio.api.conf.ts -> baseUrl
```

## .env.web

```
BROWSER=chrome | firefox | edge
HEADLESS=true | false
APP_USER=<usuario>
APP_PASSWORD=<clave>
APP_URL=<url base de la app web>
```

## .env.movil.android

```
MOBILE_PLATFORM=android
ANDROID_UDID=emulator-5554
ANDROID_DEVICE_NAME=Android Device
ANDROID_APP_PATH=./apps/android/app.apk
ANDROID_APP_PACKAGE=<package>
ANDROID_APP_ACTIVITY=<activity>
ANDROID_PLATFORM_VERSION=14
```

## .env.movil.ios

```
MOBILE_PLATFORM=ios
IOS_UDID=<udid real>
IOS_DEVICE_NAME=iPhone
IOS_PLATFORM_VERSION=18.5
IOS_APP_PATH=./apps/ios/app.ipa
IOS_XCODE_ORG_ID=<team id>
IOS_WDA_BUNDLE_ID=<wda bundle id>
IOS_APP_BUNDLE_ID=<app bundle id>
```

## Reglas de variables

- No commitear credenciales reales — usar valores mock/enmascarados.
- `MOBILE_PLATFORM` lo usa `PlatformUI.login()` para escoger Android vs iOS.
- `process.env.PLATFORM` se evita como "modo" porque colisiona con `--mode`.
