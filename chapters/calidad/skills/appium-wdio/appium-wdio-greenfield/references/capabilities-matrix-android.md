# Capabilities Android (UiAutomator2)

## Base común

```typescript
const base = {
  platformName: 'Android',
  'appium:automationName': 'UiAutomator2',
  'appium:autoGrantPermissions': true,
  'appium:noReset': true,
  'appium:newCommandTimeout': 660,
  'appium:language': env('ANDROID_LANGUAGE', 'es'),
  'appium:locale': env('ANDROID_LOCALE', 'ES'),
  'appium:settings[imageQuality]': 30
};
```

| Capability | Por qué está |
|---|---|
| `automationName: UiAutomator2` | Único driver soportado para Android nativo. No es negociable. |
| `autoGrantPermissions: true` | Concede los permisos del manifiesto al instalar. Sin esto, el primer escenario se cuelga en un diálogo del sistema que ningún selector de la app resuelve. |
| `noReset: true` | No borra datos de la app entre sesiones. Ver la tabla de decisión abajo: es la capability que más fallos de arranque causa cuando se elige mal. |
| `newCommandTimeout: 660` | Segundos que Appium espera un comando antes de matar la sesión. El valor por defecto (60) mata sesiones durante pausas legítimas: un OTP manual, un breakpoint. |
| `settings[imageQuality]` | Calidad de los screenshots que toma el driver. Bajarla reduce el peso del reporte en un orden de magnitud sin perder diagnóstico. |

## Anti-idle: obligatorio en ejecución local

UiAutomator2 espera a que la interfaz quede quieta antes de resolver cada comando, hasta agotar `waitForIdleTimeout` (default **10 000 ms**). En un dispositivo de escritorio, con las animaciones del sistema activas, ese estado quieto puede no llegar nunca y **cada `find` paga la espera completa**. Los dispositivos de granja no lo reproducen porque vienen con las escalas de animación en `0`.

```typescript
if (!isCloudMode()) {
  Object.assign(base, {
    'appium:disableWindowAnimation': true,
    'appium:settings[waitForIdleTimeout]': envNumber('ANDROID_WAIT_FOR_IDLE_TIMEOUT', 100),
    'appium:settings[actionAcknowledgmentTimeout]': envNumber('ANDROID_ACTION_ACK_TIMEOUT', 300)
  });
}
```

| Variable | Default | Efecto |
|---|---|---|
| `ANDROID_WAIT_FOR_IDLE_TIMEOUT` | `100` | Milisegundos que el driver espera a que la UI quede quieta antes de cada comando. El default del driver es `10000`. |
| `ANDROID_ACTION_ACK_TIMEOUT` | `300` | Milisegundos de espera de confirmación tras una acción. El default del driver es `3000`. |

Se verifica en el log del servidor al crear la sesión, que imprime los valores realmente aplicados. Medición tras aplicarlo: los comandos más lentos de la corrida bajaron de ~1.7 s a ~0.7 s. Diagnóstico completo en `local-run-stalls-and-host-timers.md`, que además cubre el otro cuelgue local —el del proceso cliente— con el que este se confunde.

## `noReset` y `fullReset`: la tabla de decisión

| Escenario | `noReset` | `fullReset` | Consecuencia |
|---|---|---|---|
| App ya instalada, sesión persistente deseada | `true` | `false` | Arranque rápido. Estado de la corrida anterior sobrevive: los escenarios deben ser idempotentes. |
| Cada escenario desde cero, app instalada | `false` | `false` | Limpia datos de la app entre sesiones. Cuesta segundos por escenario. |
| Instalar desde binario en cada corrida | `false` | `true` | Desinstala y reinstala. El más lento y el más determinista. |

La elección se declara explícitamente en el perfil y se documenta. Heredarla por descuido es lo que produce el fallo clásico de "el primer escenario pasa y el segundo no": el estado del primero sobrevivió.

## App nativa contra navegador móvil

El mismo dispositivo sirve para los dos, y las capabilities son mutuamente excluyentes:

```typescript
if (appPackage && appActivity) {
  Object.assign(base, {
    'appium:appPackage': appPackage,
    'appium:appActivity': appActivity
  });
} else if (appPath) {
  Object.assign(base, { 'appium:app': appPath });   // instala el binario
} else {
  Object.assign(base, { browserName: 'Chrome' });    // navegador móvil
}
```

Declarar `browserName` junto a `appPackage` produce una sesión que abre el navegador e ignora la app, con un error confuso varios steps más adelante. Los perfiles web del arquetipo eliminan explícitamente las capabilities de app (`deleteCapabilityKeys`).

Para obtener `appPackage` y `appActivity` de un binario:

```bash
aapt dump badging app.apk | grep -E "package:|launchable-activity:"
# o, con la app instalada y en primer plano:
adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'
```

## Resolución del dispositivo

El UDID no se hardcodea nunca: cambia por máquina y por sesión de emulador.

```typescript
function resolveAndroidUdid(): string {
  const envUdid = process.env.ANDROID_UDID;
  if (envUdid) {
    // `adb connect` SOLO aplica a dispositivos por red (host:puerto). Con el
    // serial de un dispositivo USB, adb intenta resolverlo como nombre de host
    // y bloquea ~5s sincrónicos —bloqueando el event loop— antes de fallar,
    // en cada arranque de sesión.
    if (/^[^\s]+:\d+$/.test(envUdid)) {
      spawnSync(adb, ['connect', envUdid], { stdio: 'ignore', shell: false });
    }
    return envUdid;
  }
  // Autodetección: primer dispositivo en estado 'device'
  const salida = spawnSync(adb, ['devices'], { encoding: 'utf8', shell: false }).stdout ?? '';
  for (const linea of salida.split('\n').slice(1)) {
    const [id, estado] = linea.trim().split(/\s+/);
    if (estado === 'device') return id;
  }
  return '';
}
```

Detalles que importan:

- **`adb connect` solo para UDID de red.** Verificado en campo: `adb connect <serial-usb>` tarda 5 segundos exactos en fallar con `failed to resolve host`, y esos 5 segundos son sincrónicos. Se paga en cada arranque y no deja rastro en el log del servidor Appium, así que aparece como un cuelgue sin causa.
- **Se salta la primera línea** de `adb devices`: es el encabezado.
- **Se filtra por estado `device`**: un dispositivo en `unauthorized` u `offline` aparece listado y produce una sesión que falla con un error que no menciona la autorización.
- **`shell: false`** en todo `spawn`: el UDID viene de configuración externa y no debe interpretarse por un shell.

## Emulador contra dispositivo físico

```typescript
if (deviceType === 'emulator') {
  Object.assign(base, {
    'appium:deviceName': env('ANDROID_EMULATOR_NAME'),
    'appium:avd': env('ANDROID_EMULATOR_NAME'),          // arranca el AVD si no corre
    'appium:platformVersion': env('ANDROID_EMULATOR_PLATFORM_VERSION')
  });
} else {
  Object.assign(base, {
    'appium:deviceName': env('ANDROID_DEVICE_NAME', 'Android Device'),
    'appium:platformVersion': env('ANDROID_PLATFORM_VERSION'),
    'appium:udid': resolveAndroidUdid()
  });
}
```

`avd` deja que Appium arranque el emulador, pero sin control sobre el tiempo de espera. Arrancarlo desde el gestor del framework da un timeout explícito y un mensaje de error útil. Ver `appium-server-lifecycle.md`.

## Chromedriver: la versión se fija, no se descubre

Para navegador móvil o para webviews dentro de la app nativa, Appium necesita un Chromedriver **compatible con la versión de Chrome o del WebView System del dispositivo**. Es la incompatibilidad silenciosa más común del stack: la sesión arranca, el primer `$()` sobre el webview falla y el mensaje habla de versiones sin decir cuál se esperaba.

```typescript
'appium:chromedriverExecutable': env('CHROMEDRIVER_PATH')
```

Procedimiento:

```bash
# 1. Versión de Chrome o del WebView en el dispositivo
adb shell dumpsys package com.android.chrome | grep versionName
adb shell dumpsys package com.google.android.webview | grep versionName

# 2. Descargar el Chromedriver de esa major y apuntar CHROMEDRIVER_PATH al binario
```

Alternativa gestionada, que evita mantener binarios a mano a cambio de requerir red en la máquina de ejecución:

```typescript
'appium:chromedriverAutodownload': true
```

En CI se prefiere el binario fijado: el autodownload introduce una dependencia de red en el arranque de cada sesión, y la versión que descarga puede cambiar entre corridas.

## Grabación de video

Android graba con las capacidades nativas del driver. Se activa por variable de entorno para no pagar el costo en cada corrida:

```typescript
if (process.env.RECORD_VIDEO === 'true') {
  Object.assign(base, {
    'appium:videoType': 'mp4',
    'appium:videoFps': 30,
    'appium:videoSize': '1280x720'
  });
}
```

Ver `mobile-evidence-and-video.md` para el ciclo completo de arranque, detención y adjunto al reporte.

## Prerequisitos verificables

El health-check del arquetipo comprueba esto antes de la primera corrida, en este orden:

```bash
adb version                                  # Android SDK platform-tools en el PATH
adb devices                                  # al menos un dispositivo en estado 'device'
appium driver list --installed | grep uiautomator2
adb shell pm list packages | grep <paquete>  # la app está instalada
```

Un fallo aquí se reporta como blocker de entorno con el comando de remediación, no como fallo de la suite. Ver `[[calidad-environment-blocker-evidence]]`.
