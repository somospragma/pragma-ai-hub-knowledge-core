# Problemas específicos de mobile nativo

## Problema 1: getWindowHandle / getWindowHandles en NATIVE_APP

### Sintomas

- Error `unknown command` o HTTP `404` al ejecutar Questions con `PageElement` en mobile.
- Mensajes tipo: `Method has not yet been implemented`, `window`, `window/handles`.
- Falla aunque los selectores sean correctos.

### Causa raiz

`BrowseTheWebWithWebdriverIO` (Serenity/JS) asume modelo de navegación web basado en window handles. Internamente invoca:

- `browser.getWindowHandle()` → `GET /window`
- `browser.getWindowHandles()` → `GET /window/handles`

En contexto `NATIVE_APP` (Appium Android/iOS), estos endpoints no aplican porque el concepto de "ventana" es solo del DOM. El driver responde "unknown command" y rompe la resolución de Questions.

### Workaround (ya implementado en configs/wdio.shared.conf.ts)

```typescript
before: async function () {
  if (!browser?.isMobile) return;

  const isUnsupported = (error: any) => {
    const msg  = String(error?.message ?? '');
    const name = String(error?.name ?? '');
    return (
      name.includes('UnknownCommand') ||
      msg.includes('unknown command') ||
      msg.includes('window') ||
      msg.includes('window/handles') ||
      msg.includes('404')
    );
  };

  const b = browser as any;
  const FALLBACK_HANDLE = 'NATIVE-APP';   // sin "_" — debe matchear ^[\d.A-Za-z-]+$

  b.overwriteCommand('getWindowHandle', async function (orig: any, ...args: any[]) {
    try { return await orig(...args); }
    catch (e: any) {
      if (isUnsupported(e)) return FALLBACK_HANDLE;
      throw e;
    }
  });

  b.overwriteCommand('getWindowHandles', async function (orig: any, ...args: any[]) {
    try { return await orig(...args); }
    catch (e: any) {
      if (isUnsupported(e)) return [FALLBACK_HANDLE];
      throw e;
    }
  });
}
```

### Alcance

- Aplica solo si `browser.isMobile === true`.
- No replicar en Tasks, Interactions ni Steps.
- NO usar `_` (underscore) en el handle — el `CorrelationId` de Serenity/JS exige regex `^[\d.A-Za-z-]+$`.

---

## Problema 2: @serenity-js/web no funciona en mobile nativo

### Sintomas

- `Click.on(...)`, `Enter.theValue(...)`, `Text.of(...)` fallan en NATIVE_APP.
- Errores al evaluar `PageElement.located(By.xpath(...))` con selectores nativos.
- `Question.about` devuelve `undefined` o lanza error de DOM no encontrado.

### Causa raiz

`@serenity-js/web` está diseñado para el modelo DOM de un navegador. En contexto Appium NATIVE_APP no hay DOM, sino árbol de elementos nativos.

### Alternativa correcta

No degradar a usar `browser.$` directo en Tasks. En su lugar:

1. Crear Interactions custom que extiendan `Interaction` y encapsulen `browser.$`.
2. Crear Questions custom con `Question.about<T>(...)`.
3. Selectores como `string`, no `PageElement`.

```typescript
// CORRECTO — Interaction encapsulada
import { Interaction, UsesAbilities, AnswersQuestions } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export class Tap extends Interaction {
  static on(selector: string) { return new Tap(selector); }

  constructor(private readonly selector: string) {
    super(`#actor taps on ${ selector }`);
  }

  async performAs(_actor: UsesAbilities & AnswersQuestions): Promise<void> {
    const el = await browser.$(this.selector);
    await el.waitForDisplayed({ timeout: 15_000 });
    await el.click();
  }
}

// INCORRECTO — browser.$ directo en Task
export const BadLogin = () => Task.where(`#actor login`,
  Interaction.where('clicks', async () => {
    await (await browser.$('~login')).click();  // NO HACER ESTO
  }),
);
```

---

## Problema 3: Selectores con By.xpath lentos o fragiles en mobile

### Sintomas

- Tests inestables (flakiness).
- Tiempos de espera que crecen con el tamaño de la app.
- iOS especialmente lento con XPath complejos.

### Alternativa por plataforma

| Estrategia | Android | iOS | Performance |
|---|---|---|---|
| Accessibility ID (`~id`) | ideal | ideal | rápido |
| `android=...` (UiAutomator2) | sí | no | buena |
| `-ios predicate string:...` | no | sí | buena |
| `-ios class chain:...` | no | sí | buena |
| XPath | frágil | lento | frágil |

Pedir al equipo de desarrollo que añada `accessibilityIdentifier` (iOS) y `contentDescription` (Android) a los elementos clave.

---

## Problema 4: Contextos NATIVE_APP / WEBVIEW (apps híbridas)

### Sintomas

- Selectores web no encuentran elementos cuando se está en NATIVE_APP.
- Selectores nativos no encuentran elementos cuando se está en WEBVIEW.
- Cambios de contexto pierden el estado de Serenity/JS.

### Patrón recomendado

```typescript
// features/mobile/shared/Interactions/SwitchContext.ts
import { Interaction } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export const SwitchToWebView = () =>
  Interaction.where(`#actor switches to WEBVIEW context`, async () => {
    const contexts = await (browser as any).getContexts();
    const webview = contexts.find((c: string) => c.includes('WEBVIEW'));
    if (!webview) throw new Error('No WEBVIEW context available');
    await (browser as any).switchContext(webview);
  });

export const SwitchToNative = () =>
  Interaction.where(`#actor switches to NATIVE_APP context`, async () => {
    await (browser as any).switchContext('NATIVE_APP');
  });
```

### Reglas para híbrido

- Validar contexto activo antes de cada acción crítica.
- Encapsular cambios de contexto en Interactions.
- Documentar en cada Task híbrida qué contexto requiere.
- NUNCA mezclar selectores web y nativos sin cambio explícito de contexto.
