# WebdriverIO encapsulado en Screenplay

## Cuándo escribir una Interaction custom

- El proyecto está en mobile y `@serenity-js/web` no aplica.
- Se necesita un gesto custom (swipe con coordenadas calculadas, longPress, etc.).
- La acción se reutilizará en múltiples Tasks.
- Hay lógica de plataforma (Android vs iOS).

## Plantilla de Interaction encapsulando WDIO

```typescript
// features/mobile/shared/Interactions/<Nombre>.ts
import { AnswersQuestions, Interaction, UsesAbilities } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export class Tap extends Interaction {

  static on(selector: string): Tap {
    return new Tap(selector);
  }

  constructor(private readonly selector: string) {
    super(`#actor taps on ${ selector }`);
  }

  async performAs(_actor: UsesAbilities & AnswersQuestions): Promise<void> {
    const el = await browser.$(this.selector);
    await el.waitForExist({ timeout: 15_000 });
    await el.waitForDisplayed({ timeout: 15_000 });
    await el.click();
  }
}
```

## Plantilla de Interaction funcional (con Interaction.where)

Útil cuando la acción no necesita constructor con params complejos:

```typescript
// features/mobile/shared/Interactions/<Nombre>.ts
import { Interaction } from '@serenity-js/core';
import { browser } from '@wdio/globals';

type Options = {
  maxSwipes?: number;
  pressMs?: number;
};

export const ScrollUp = (options: Options = {}) => {
  const cfg = {
    maxSwipes: options.maxSwipes ?? 10,
    pressMs: options.pressMs ?? 120,
  };

  const perform = async () => {
    const rect = await browser.getWindowRect();
    const x = Math.floor(rect.width * 0.5);
    const startY = Math.floor(rect.height * 0.7);
    const endY = Math.floor(rect.height * 0.3);

    for (let i = 0; i < cfg.maxSwipes; i++) {
      await browser
        .action('pointer', { parameters: { pointerType: 'touch' } })
        .move({ x, y: startY })
        .down()
        .pause(cfg.pressMs)
        .move({ x, y: endY })
        .up()
        .perform();
    }
  };

  return Interaction.where(`#actor scrolls up`, perform);
};
```

## Plantilla de Question encapsulando WDIO

```typescript
// features/mobile/shared/Questions/IsVisible.ts
import { Question } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export const IsVisible = (selector: string) =>
  Question.about<boolean>(`si ${ selector } está visible`, async () => {
    const el = await browser.$(selector);
    return el.isDisplayed().catch(() => false);
  });
```

```typescript
// features/mobile/shared/Questions/AttributeOf.ts
import { Question } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export const AttributeOf = (selector: string, attribute: string) =>
  Question.about<string | null>(`${ attribute } de ${ selector }`, async () => {
    const el = await browser.$(selector);
    await el.waitForExist({ timeout: 15_000 });
    return el.getAttribute(attribute);
  });
```

## Acción que difiere por plataforma

```typescript
// features/mobile/shared/Interactions/HideKeyboard.ts
import { Interaction } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export const HideKeyboard = () => Interaction.where(
  `#actor oculta el teclado`,
  async () => {
    const platform = String(browser.capabilities.platformName ?? '').toLowerCase();

    if (platform === 'android') {
      try { await (browser as any).hideKeyboard(); return; }
      catch { /* fallback */ }
    }

    if (platform === 'ios') {
      try { await browser.execute('mobile: hideKeyboard'); return; }
      catch { /* ignore */ }
    }
  },
);
```

## Reglas de encapsulación

### NUNCA hacer (en Tasks o Steps)

```typescript
// MAL: WDIO directo en step
When('Pepito hace login', async () => {
  await (await $('~user')).setValue('pepito');   // MAL
  await (await $('~submit')).click();             // MAL
});

// MAL: WDIO directo en Task
export const BadLogin = () => Task.where(
  `#actor login`,
  Interaction.where('clicks submit', async () => {
    await (await browser.$('~submit')).click();   // MAL inline en Task
  }),
);
```

### SIEMPRE hacer

```typescript
// BIEN: encapsulado en Interaction reutilizable
export class Tap extends Interaction {
  // ... implementación con browser.$ ...
}

// BIEN: Task compuesta con Interactions
export const Login = {
  withCredentials: (ui: LoginSelectors, user: string, password: string) =>
    Task.where(`#actor inicia sesión con credenciales`,
      TapWhenVisible.on(ui.inputUser),
      ClearAndEnter.value(user).into(ui.inputUser),
      TapWhenVisible.on(ui.buttonSubmit),
    ),
};

// BIEN: Step delega a Task
When('{pronoun} logs in with username {string} and password {string}',
  async (actor: Actor, user: string, password: string) => {
    await actor.attemptsTo(
      Login.withCredentials(PlatformUI.login(), user, password),
    );
  },
);
```

## Anti-patrones comunes

| Anti-patrón | Por qué está mal | Alternativa |
|---|---|---|
| `browser.pause(3000)` | Espera ciega, lenta y frágil | `waitForDisplayed` / `Wait.until` |
| `await $('btn').click()` (sin await en `$()`) | TypeError en runtime | `await (await $('btn')).click()` o guardar ref |
| `browser.$` en Tasks/Steps | Rompe Screenplay | Encapsular en Interaction |
| Repetir `$()` para mismo elemento | Múltiples queries al DOM | Guardar referencia |
| `setTimeout` para esperar UI | No bloquea el flujo correctamente | `browser.waitUntil` |
| `try/catch` que swallow errors silenciosamente | Tests verde-en-falso | Loggear o re-lanzar |
| `addCommand` dentro de un step | Ejecuta en cada test | Definir en hook `before` del config |
| `mobile: scroll` sin parámetros válidos por plataforma | `mobile: scrollGesture` (Android) != `mobile: scroll` (iOS) | Usar `el.scrollIntoView()` cuando se pueda |

## Checklist de calidad

- [ ] No hay `browser.$` ni `$()` directo en Tasks ni Steps
- [ ] WDIO directo solo en configs, Interactions, Questions o scripts standalone
- [ ] Cada elemento usado más de una vez está guardado en variable
- [ ] No hay `browser.pause()` ni `setTimeout`
- [ ] Esperas usan `waitFor*` o `waitUntil` con timeout explícito
- [ ] `addCommand`/`overwriteCommand` solo en hooks de config, con comentario explicativo
- [ ] Comandos mobile usan API enriquecida v9 (`longPress`, `swipe`, `scrollIntoView`) cuando aplica
- [ ] Acciones que difieren por plataforma chequean `browser.capabilities.platformName`
- [ ] Cambios de contexto (NATIVE_APP/WEBVIEW) son explícitos y documentados
