# Workaround de window handles para NATIVE_APP — serenity-wdio brownfield

## Contexto

Serenity/JS no soporta completamente mobile nativo con WebdriverIO. En un contexto `NATIVE_APP`, los comandos `browser.getWindowHandle()` y `browser.getWindowHandles()` no están soportados por el backend (UiAutomator2 / XCUITest) y lanzan error. Serenity/JS los invoca internamente, por lo que la sesión puede fallar antes de ejecutar el escenario.

## Dónde vive el workaround

El parche ya está implementado y centralizado en `configs/wdio.shared.conf.ts`, dentro del hook `before`. Sobrescribe (`overwriteCommand`) los comandos `getWindowHandle` y `getWindowHandles` a nivel de Browser scope, devolviendo un identificador estable (`'NATIVE-APP'`) cuando el backend no soporta el comando.

```typescript
// configs/wdio.shared.conf.ts - ya implementado, NO replicar
before: async function () {
  if (!browser?.isMobile) return;              // solo aplica en mobile

  const isUnsupported = (error: any) => { /* ... */ };
  const b = browser as any;
  const FALLBACK_HANDLE = 'NATIVE-APP';

  b.overwriteCommand('getWindowHandle', async function (orig: any, ...args: any[]) {
    try { return await orig(...args); }
    catch (e) { if (isUnsupported(e)) return FALLBACK_HANDLE; throw e; }
  });

  b.overwriteCommand('getWindowHandles', async function (orig: any, ...args: any[]) {
    try { return await orig(...args); }
    catch (e) { if (isUnsupported(e)) return [FALLBACK_HANDLE]; throw e; }
  });
}
```

## Alcance

- **SOLO** aplica cuando `browser.isMobile === true`. La guarda `if (!browser?.isMobile) return;` garantiza que no afecta ejecuciones web.
- Es un parche de nivel de configuración, transversal a toda la suite mobile.

## Prohibición de replicación

- **PROHIBIDO** replicar este workaround en Tasks, Interactions o Steps. Ya está resuelto de forma centralizada en `wdio.shared.conf.ts`.
- Si un escenario mobile falla por window handles, verificar que el proyecto conserva este hook en `wdio.shared.conf.ts`; **no** agregar `overwriteCommand` ni manejo de `getWindowHandle` en la capa Screenplay.
- Al detectar en el análisis previo que este workaround existe, registrarlo como `documented_workarounds: ["native-app-window-handles"]` y preservarlo intacto.

## Relación con el brownfield

Durante la extensión de un proyecto mobile existente, este workaround forma parte de la infraestructura que **no se modifica ni se duplica**. El código nuevo (Interactions que encapsulan `browser.$`, Tasks que componen con `Task.where`, Questions sin side effects) opera por encima del parche sin necesidad de conocer sus detalles.
