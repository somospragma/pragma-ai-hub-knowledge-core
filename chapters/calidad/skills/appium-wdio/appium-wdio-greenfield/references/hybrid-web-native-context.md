# Contextos nativo y webview, deep links y diálogos del sistema

Este es el flanco donde más suites se atascan, porque el síntoma —"el elemento no existe"— apunta al lado equivocado del problema.

## Contextos

Una sesión de Appium tiene varios contextos: el nativo y uno por cada webview presente.

```typescript
const contextos = await driver.getContexts();
// ['NATIVE_APP', 'WEBVIEW_com.ejemplo.app', 'WEBVIEW_12345.1']
const actual = await driver.getContext();
```

**Los selectores solo resuelven dentro del contexto activo.** Un selector CSS no encuentra nada en contexto nativo; un XPath sobre `XCUIElementTypeButton` no encuentra nada dentro de un webview. En ambos casos el error es "elemento no encontrado", sin mencionar el contexto: es lo que manda el diagnóstico a revisar el selector cuando el selector está bien.

## La regla

**Antes de tocar un elemento del sistema operativo, declarar el contexto nativo.**

```typescript
await driver.switchContext('NATIVE_APP');
await (await driver.$(selectorNativo)).click();
await driver.switchContext(contextoWebviewPrevio);   // volver si el flujo sigue en la web
```

Casos que exigen el cambio, aunque el escenario sea de navegador móvil:

- Diálogos de permisos del sistema.
- El diálogo de "abrir en la app" de un enlace universal o un enlace de aplicación.
- Selectores de archivo, cámara, compartir.
- La barra del navegador: pestañas, dirección, recarga.
- Notificaciones del sistema.

## Volver al webview correcto

En una sesión con varios webviews, `switchContext('WEBVIEW_1')` es una apuesta. Se resuelve por nombre exacto, obtenido antes del cambio:

```typescript
const previo = await driver.getContext();
await driver.switchContext('NATIVE_APP');
// … interacción nativa …
await driver.switchContext(previo);
```

Cuando el diálogo nativo abre una pestaña nueva, el webview anterior puede haber desaparecido: se vuelve a listar contextos y se elige por el patrón esperado, con espera activa, porque el webview tarda en registrarse.

```typescript
await driver.waitUntil(
  async () => (await driver.getContexts()).some(c => String(c).startsWith('WEBVIEW')),
  { timeout: 30_000, timeoutMsg: 'No apareció ningún webview' }
);
```

## Capabilities que habilitan el webview

| Capability | Plataforma | Para qué |
|---|---|---|
| `webviewConnectTimeout` | Ambas | Cuánto espera Appium a que el webview quede accesible. El valor por defecto se queda corto en apps que cargan mucho. |
| `includeSafariInWebviews` | iOS | Sin esto, las pestañas de Safari no aparecen en la lista de contextos. Imprescindible cuando el flujo sale de la app al navegador. |
| `webkitResponseTimeout` | iOS | Tiempo del canal con el motor web. Bajo, produce cortes a mitad de interacción. |
| `chromedriverExecutable` | Android | El webview de Android necesita un Chromedriver compatible. Ver `capabilities-matrix-android.md`. |
| `enforceWebDriverClassic` | Ambas | Algunas combinaciones de versiones fallan con el protocolo nuevo. Es el interruptor a probar primero cuando el webview conecta pero no responde. |

En iOS físico, además, **Web Inspector debe estar habilitado en el dispositivo** (ajustes de Safari, opciones avanzadas). Sin eso, el túnel de inspección no levanta y no hay contexto de webview, con un error que habla del túnel y no del ajuste.

## Deep links y enlaces universales

Abrir la app por su esquema o por una URL es más rápido y determinista que navegar por la interfaz:

```typescript
// iOS
await driver.execute('mobile: deepLink', { url: destino, bundleId: 'com.apple.mobilesafari' });

// Android
await driver.execute('mobile: deepLink', { url: destino, package: 'com.ejemplo.app' });
```

Cuando lo que se prueba es el enlace universal en sí —el usuario abre una URL en el navegador y el sistema ofrece abrir la app—, hay tres condiciones que deben cumplirse a la vez, y omitir cualquiera hace que el diálogo no aparezca:

1. **La URL inicial del navegador debe ser una URL real**, no una página en blanco. Una página en blanco no dispara la resolución del enlace universal.
2. **El arranque automático del navegador debe estar activo**, para que la sesión empiece con la página cargada.
3. **La aceptación automática de alertas debe estar desactivada.** Con ella activa, el driver acepta el diálogo del sistema antes de que el escenario lo vea, y el `Then` falla diciendo que el diálogo no apareció — cuando en realidad apareció y lo aceptó el propio driver.

```typescript
{
  'appium:autoLaunch': true,
  'appium:safariInitialUrl': env('BASE_URL'),
  'appium:autoAcceptAlerts': false,
  'appium:autoDismissAlerts': false,
  'appium:webviewConnectTimeout': 90_000
}
```

El punto 3 es el que más tiempo cuesta diagnosticar, porque la capability suele venir heredada de la configuración base compartida con los perfiles de app nativa, donde `autoAcceptAlerts: true` es lo correcto. El perfil híbrido debe sobrescribirla explícitamente.

## Escenarios con la app desinstalada

Para probar el camino en que el usuario no tiene la app instalada, el escenario lo declara con un tag y el perfil lo aplica al conectar:

```typescript
afterLocalConnect: async world => {
  if (world.pickle?.tags.some(t => t.name === '@sin-app')) {
    const bundleId = env('IOS_BUNDLE_ID');
    if (await world.driver!.isAppInstalled(bundleId)) {
      await world.driver!.removeApp(bundleId);
    }
  }
}
```

Va en el perfil, no en un step: es una condición del entorno previa a la sesión, no una acción del usuario. Y exige que el escenario siguiente reinstale, o quede documentado que ese perfil deja el dispositivo sin la app.

## Diagnóstico

| Síntoma | Comprobar | Causa habitual |
|---|---|---|
| Elemento nativo no encontrado en escenario web | `getContext()` | La sesión está en el webview |
| Selector CSS no encuentra nada | `getContext()` | La sesión está en contexto nativo |
| `getContexts()` devuelve solo `NATIVE_APP` en iOS | Web Inspector en el dispositivo | El ajuste está desactivado |
| El diálogo de enlace universal no aparece | URL inicial y aceptación de alertas | Página en blanco, o el driver ya lo aceptó |
| El webview conecta pero no responde | Versión de Chromedriver, protocolo clásico | Incompatibilidad de versiones |
| Funciona en simulador, falla en dispositivo físico | Web Inspector, túnel, tiempos | Los tiempos del dispositivo real son mayores |
