# Capabilities iOS (XCUITest)

iOS no es Android con otros selectores. La diferencia estructural es **WebDriverAgent**: Appium no habla con el dispositivo directamente, sino con una app auxiliar que compila, firma e instala en el dispositivo antes de cada sesión nueva. Casi todo lo que falla en iOS falla ahí, y el mensaje de error rara vez lo dice.

## Prerequisitos que no se pueden omitir

| Requisito | Simulador | Dispositivo físico |
|---|---|---|
| macOS con Xcode y command line tools | Sí | Sí |
| Driver XCUITest instalado en Appium | Sí | Sí |
| Cuenta de desarrollo Apple y equipo de firma | No | Sí |
| Dispositivo confiando en el certificado | No | Sí |
| Web Inspector habilitado (para webviews) | No | Sí, en ajustes de Safari |

```bash
xcode-select --install
appium driver install xcuitest
appium driver list --installed
xcrun simctl list devices          # simuladores disponibles
xcrun xctrace list devices         # dispositivos físicos y su UDID
```

Sin macOS, el perfil iOS se genera y se documenta, pero no se ejecuta: se reporta `partial`. Degradar a Android en silencio es peor que no entregar.

## Simulador

```typescript
{
  platformName: 'iOS',
  'appium:automationName': 'XCUITest',
  'appium:deviceName': env('IOS_SIMULATOR_DEVICE_NAME'),
  'appium:platformVersion': env('IOS_SIMULATOR_PLATFORM_VERSION'),
  'appium:udid': env('IOS_SIMULATOR_UDID'),
  'appium:bundleId': env('IOS_SIMULATOR_BUNDLE_ID'),
  'appium:noReset': true,
  'appium:fullReset': false,
  'appium:autoAcceptAlerts': true,
  'appium:autoDismissAlerts': false,
  'appium:webviewConnectTimeout': 90_000,
  'appium:includeSafariInWebviews': true,
  'appium:webkitResponseTimeout': 90_000,
  'appium:language': env('IOS_LANGUAGE', 'es'),
  'appium:locale': env('IOS_LOCALE', 'es_ES')
}
```

El simulador es rápido y no necesita firma, pero **no sirve para todo**: no tiene cámara real, biometría real, notificaciones push reales ni comportamiento de red idéntico. Los flujos de autenticación biométrica, escaneo y push se validan en dispositivo físico o no se validan.

## Dispositivo físico

```typescript
{
  platformName: 'iOS',
  'appium:automationName': 'XCUITest',
  'appium:deviceName': env('IOS_DEVICE_NAME'),
  'appium:platformVersion': env('IOS_PLATFORM_VERSION'),
  'appium:udid': env('IOS_UDID'),
  'appium:bundleId': env('IOS_BUNDLE_ID'),

  // --- Bloque WebDriverAgent: sin esto la primera sesión falla por timeout ---
  'appium:updatedWDABundleId': env('IOS_UPDATED_WDA_BUNDLE_ID'),
  'appium:xcodeOrgId': env('IOS_XCODE_ORG_ID'),
  'appium:xcodeSigningId': env('IOS_XCODE_SIGNING_ID', 'Apple Development'),
  'appium:usePrebuiltWDA': false,
  'appium:useNewWDA': false,
  'appium:wdaLaunchTimeout': 300_000,
  'appium:wdaConnectionTimeout': 900_000,
  'appium:wdaStartupRetries': 3,
  'appium:wdaStartupRetryInterval': 10_000,
  'appium:showXcodeLog': true,
  'appium:skipLogCapture': true,

  // --- Sesión ---
  'appium:noReset': true,
  'appium:fullReset': false,
  'appium:autoLaunch': false,
  'appium:autoAcceptAlerts': true,
  'appium:autoDismissAlerts': false,
  'appium:shouldTerminateApp': true,
  'appium:newCommandTimeout': 660,

  // --- Webviews ---
  'appium:webviewConnectTimeout': 120_000,
  'appium:includeSafariInWebviews': true,
  'appium:webkitResponseTimeout': 120_000,

  // --- Evidencia ---
  'appium:screenshotQuality': 3
}
```

## El bloque WebDriverAgent, capability por capability

| Capability | Qué hace | Qué pasa si falta |
|---|---|---|
| `updatedWDABundleId` | Identificador con el que se firma e instala WebDriverAgent | Se usa el identificador por defecto de Apple, que **no se puede firmar** con una cuenta de desarrollo gratuita ni con perfiles restringidos. La instalación falla. |
| `xcodeOrgId` | Equipo de desarrollo con el que se firma | No compila WebDriverAgent. Error de firma en Xcode que Appium reporta como fallo de sesión. |
| `xcodeSigningId` | Tipo de certificado (`Apple Development` en la mayoría de casos) | Toma el valor por defecto, que puede no existir en el llavero de esa máquina. |
| `wdaLaunchTimeout` | Espera a que WebDriverAgent compile, instale y arranque | Compilar WebDriverAgent la primera vez toma **minutos**. El valor por defecto expira antes y produce un timeout que parece un problema de red. |
| `wdaConnectionTimeout` | Espera a que el canal con WebDriverAgent quede estable | Sesiones que caen a mitad de escenario en dispositivos lentos o con la app pesada. |
| `wdaStartupRetries` y `wdaStartupRetryInterval` | Reintentos del arranque | El arranque de WebDriverAgent es intermitente por naturaleza en dispositivo físico. Sin reintentos, la tasa de falsos rojos sube de forma notable. |
| `usePrebuiltWDA: false` | Recompila en vez de asumir una compilación previa | Con `true` y sin compilación previa válida, falla. Se pone en `true` solo cuando el flujo de CI compila WebDriverAgent como paso aparte, y entonces ahorra minutos por corrida. |
| `useNewWDA: false` | Reutiliza la instancia si ya está corriendo | Con `true` desinstala y reinstala en cada sesión: mucho más lento, útil solo para diagnosticar estado corrupto. |
| `showXcodeLog: true` | Vuelca el log de Xcode | Sin él, un fallo de firma se reporta como "no se pudo iniciar la sesión" sin causa. Es la capability que convierte una hora de diagnóstico en dos minutos. |
| `skipLogCapture: true` | No captura el log del sistema | Sin ella, el log del dispositivo se acumula en cada sesión y degrada la corrida en suites largas. Se desactiva puntualmente cuando el diagnóstico lo necesita. |

Los tres timeouts se expresan deliberadamente en minutos. No son valores conservadores de más: compilar e instalar WebDriverAgent en un dispositivo físico es un proceso de esa escala, y ajustarlos a la baja por estética produce fallos que se atribuyen a la app.

## `autoLaunch: false` y control explícito del arranque

Con `autoLaunch: false`, la sesión se establece sin lanzar la app; el escenario decide cuándo abrirla. Es lo que permite escribir un `Given` que declare el estado inicial de forma explícita, en vez de que la app ya esté abierta por efecto del hook.

```typescript
await driver.activateApp(bundleId);      // abrir o traer a primer plano
await driver.terminateApp(bundleId);     // cerrar por completo
await driver.queryAppState(bundleId);    // 0 no instalada … 4 en primer plano
```

`shouldTerminateApp: true` cierra la app al terminar la sesión, que es lo que evita que el escenario siguiente empiece a mitad de un flujo.

## Alertas del sistema

`autoAcceptAlerts` y `autoDismissAlerts` son **excluyentes**: activar las dos hace que el driver ignore ambas.

| Configuración | Cuándo |
|---|---|
| `autoAcceptAlerts: true` | La app pide permisos y ninguno de ellos es objeto de prueba. Evita que un diálogo de notificaciones bloquee el escenario. |
| Ambas en `false` | El diálogo **es** parte del flujo bajo prueba: un enlace universal, un permiso que hay que denegar, una confirmación de pago. |

El caso híbrido es el que más confunde: una capability heredada de la configuración base con `autoAcceptAlerts: true` acepta el diálogo del sistema antes de que el escenario pueda verlo, y el `Then` falla diciendo que el diálogo no apareció. Detalle en `hybrid-web-native-context.md`.

## Selectores idiomáticos

| Estrategia | Cuándo | Ejemplo |
|---|---|---|
| `~identificador` (accessibility id) | Siempre que exista. Es el más rápido y el más estable. | `~botonIngresar` |
| Class chain | Jerarquías predecibles | `**/XCUIElementTypeButton[\`label == "Ingresar"\`]` |
| Predicate string | Filtros por atributo | `type == 'XCUIElementTypeSecureTextField' AND visible == 1` |
| XPath | Último recurso | `//XCUIElementTypeButton[@name="Ingresar"]` |

XPath en iOS es notablemente más lento que las otras estrategias: recorre el árbol completo de accesibilidad en cada búsqueda. En pantallas densas la diferencia entre XPath y class chain se nota en la duración total de la suite. Los selectores viven en el test-data, no en el código: ver `selectors-in-testdata-json.md`.

## Grabación de video en dispositivo físico

La grabación nativa del driver es poco fiable en iOS físico. La alternativa es el servidor MJPEG que expone WebDriverAgent, capturado con una herramienta externa:

```typescript
{
  'appium:mjpegServerPort': 9100,
  'appium:mjpegServerFramerate': 10
}
```

Ver `mobile-evidence-and-video.md`.

## Verificación previa

```bash
xcrun xctrace list devices | grep -v Simulator     # el dispositivo aparece y su UDID coincide
appium driver list --installed | grep xcuitest
security find-identity -v -p codesigning           # el certificado de firma existe
```

Un fallo aquí es blocker de entorno, con su comando de remediación, no un fallo de la suite.
