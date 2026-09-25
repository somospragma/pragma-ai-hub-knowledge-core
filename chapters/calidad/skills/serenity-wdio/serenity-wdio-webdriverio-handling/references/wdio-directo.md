# WebdriverIO directo (sin Screenplay)

## Selectores básicos

```typescript
// CSS (web)
const button = await $('button#submit');
const inputs = await $$('input.form-control');

// XPath
const link = await $('//a[text()="Continuar"]');

// Accessibility ID (mobile, preferido)
const loginBtn = await $('~login-button');

// Android UiAutomator2
const androidEl = await $('android=new UiSelector().text("Aceptar")');

// iOS predicate / class chain
const iosEl = await $('-ios predicate string:label == "Submit"');
const iosChain = await $('-ios class chain:**/XCUIElementTypeButton[`label == "OK"`]');
```

## Acciones básicas

```typescript
// Click + setValue + clearValue
await (await $('~username')).click();
await (await $('~username')).setValue('pepito');
await (await $('~username')).clearValue();

// Verificaciones
const text = await (await $('h1')).getText();
const visible = await (await $('~spinner')).isDisplayed();
const enabled = await (await $('button')).isEnabled();
const value = await (await $('input')).getValue();

// Esperas (recomendado en lugar de browser.pause)
await (await $('~loader')).waitForExist({ timeout: 15_000 });
await (await $('~loader')).waitForDisplayed({ timeout: 15_000, reverse: true });
await (await $('button')).waitForClickable({ timeout: 10_000 });
```

## Patrón "guardar referencia" (performance)

`$()` consulta el DOM cada vez. Si se usa el elemento varias veces, guardarlo:

```typescript
// MAL — 3 queries al DOM
await (await $('~submit')).waitForDisplayed();
await (await $('~submit')).waitForClickable();
await (await $('~submit')).click();

// BIEN — 1 query
const submit = await $('~submit');
await submit.waitForDisplayed();
await submit.waitForClickable();
await submit.click();
```

## Mobile commands enriquecidos (WDIO v9)

WebdriverIO v9 añade comandos mobile que abstraen Appium. Preferir estos sobre comandos `mobile: ...` crudos cuando estén disponibles:

```typescript
// Long press
await (await $('~Contacts')).longPress();

// Swipe en dirección (cross-platform)
await browser.swipe({ direction: 'up', percent: 0.6 });

// Scroll hasta elemento (cross-platform)
await (await $('~Settings')).scrollIntoView({ direction: 'down', maxScrolls: 10 });

// Comando Appium crudo (cuando WDIO no lo abstrae)
await driver.execute('mobile: swipeGesture', {
  direction: 'down',
  percent: 0.8,
});
```

## Action API (gestos personalizados)

Cuando los comandos enriquecidos no son suficientes:

```typescript
const rect = await browser.getWindowRect();
const x = Math.floor(rect.width * 0.5);
const startY = Math.floor(rect.height * 0.7);
const endY = Math.floor(rect.height * 0.3);

await browser
  .action('pointer', { parameters: { pointerType: 'touch' } })
  .move({ x, y: startY })
  .down()
  .pause(120)
  .move({ x, y: endY })
  .up()
  .perform();
```

## Manejo de contextos (apps híbridas)

```typescript
const contexts = await (browser as any).getContexts();
// devuelve algo como: ['NATIVE_APP', 'WEBVIEW_com.example.app']

const webview = contexts.find((c: string) => typeof c === 'string' && c.includes('WEBVIEW'));
if (!webview) throw new Error('No WEBVIEW context available');

await (browser as any).switchContext(webview);
// ... interactuar con el DOM ...
await (browser as any).switchContext('NATIVE_APP');
```

## Capabilities y session info

```typescript
const platform = String(browser.capabilities.platformName ?? '').toLowerCase();
const isAndroid = platform === 'android';
const isIOS = platform === 'ios';
const isMobile = browser.isMobile;
const isW3C = browser.isW3C;
```

## Custom commands (addCommand / overwriteCommand)

Solo en configs/hooks, nunca en Tasks:

```typescript
// configs/wdio.shared.conf.ts (hook before)
before: async function () {
  if (!browser?.isMobile) return;

  // Añadir nuevo comando
  (browser as any).addCommand('clickWithRetry',
    async function (this: WebdriverIO.Element, retries = 3) {
      for (let i = 0; i < retries; i++) {
        try { return await this.click(); }
        catch (e) { if (i === retries - 1) throw e; }
      }
    },
    true, // attachToElement
  );

  // Sobrescribir uno existente (caso real del proyecto)
  (browser as any).overwriteCommand('getWindowHandle',
    async function (orig: any, ...args: any[]) {
      try { return await orig(...args); }
      catch { return 'NATIVE-APP'; }
    },
  );
}
```

## Script standalone (debug / exploración)

```typescript
// scripts/debug-mobile.ts
import { remote } from 'webdriverio';

(async () => {
  const browser = await remote({
    hostname: '127.0.0.1',
    port: 4723,
    path: '/',
    capabilities: {
      platformName: 'Android',
      'appium:automationName': 'UiAutomator2',
      'appium:app': './apps/android/app.apk',
    },
  });

  await browser.$('~login-button').click();
  console.log('clicked');
  await browser.deleteSession();
})();
```

Ejecutar con `tsx`: `npx tsx scripts/debug-mobile.ts`
