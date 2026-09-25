# Screenplay Pattern — Implementación Mobile nativo (Appium)

## Restricción critica

`@serenity-js/web` **NO funciona** en mobile nativo. Ver skill `serenity-wdio-troubleshooting` para detalles del problema y el workaround de window handles.

## Imports correctos para mobile

```typescript
import { Interaction, Task, Question, Duration } from '@serenity-js/core';
import type { AnswersQuestions, UsesAbilities } from '@serenity-js/core';
import { browser } from '@wdio/globals';
```

## UI Mapping con strings (no PageElement)

```typescript
// features/mobile/shared/UI/LoginSelectors.ts — interfaz
export interface LoginSelectors {
  buttonLogin: string;
  inputUser: string;
  inputPassword: string;
  buttonSubmit: string;
}

// features/mobile/android/UI/LoginUI.android.ts
import { LoginSelectors } from '../../shared/UI/LoginSelectors';

export const AndroidLoginUI: LoginSelectors = {
  buttonLogin:    '~login-button',         // accessibility id (preferido)
  inputUser:      '~username-input',
  inputPassword:  '~password-input',
  buttonSubmit:   '~submit-button',
};

// features/mobile/ios/UI/LoginUI.ios.ts
export const IOSLoginUI: LoginSelectors = {
  buttonLogin:    '~login-button',
  inputUser:      '~username-input',
  inputPassword:  '~password-input',
  buttonSubmit:   '~submit-button',
};
```

Prioridad de selectores en Mobile:

1. Accessibility ID (`~id`) — preferido siempre
2. iOS Predicate (`-ios predicate string:...`)
3. UiAutomator2 (`android=...`)
4. XPath (último recurso, frágil en mobile)

## PlatformUI Resolver (Android/iOS)

```typescript
// features/mobile/shared/Resolvers/PlatformUI.ts
import { AndroidLoginUI } from '../../android/UI/LoginUI.android';
import { IOSLoginUI }     from '../../ios/UI/LoginUI.ios';
import { LoginSelectors } from '../UI/LoginSelectors';

export class PlatformUI {
  static login(): LoginSelectors {
    return (process.env.MOBILE_PLATFORM || '').toLowerCase() === 'ios'
      ? IOSLoginUI
      : AndroidLoginUI;
  }
}
```

## Interaction (encapsula browser.$)

```typescript
// features/mobile/shared/Interactions/Tap.ts
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

## Task que compone Interactions

```typescript
// features/mobile/shared/Tasks/TapWhenVisible.ts
import { Duration, Task } from '@serenity-js/core';
import { WaitForDisplayed } from '../Interactions/WaitFor';
import { Tap } from '../Interactions/Tap';

export const TapWhenVisible = {
  on: (selector: string) =>
    Task.where(
      `#actor toca ${ selector } cuando está visible`,
      WaitForDisplayed.of(selector, Duration.ofSeconds(15)),
      Tap.on(selector),
    ),
};
```

## Question (mobile)

```typescript
// features/mobile/shared/Questions/TextOf.ts
import { Question } from '@serenity-js/core';
import { browser } from '@wdio/globals';

export const TextOf = (selector: string) =>
  Question.about<string>(`texto de ${ selector }`, async () => {
    const el = await browser.$(selector);
    await el.waitForExist({ timeout: 15_000 });
    return el.getText();
  });
```

## Obligatorio en Mobile

- Selectores como `string` (NO `PageElement`).
- `browser.$()` solo dentro de Interactions o Questions (encapsulado).
- `waitForExist` + `waitForDisplayed` antes de cada acción.
- Resolver `PlatformUI` para diferenciar Android/iOS.
- Tasks describen negocio, Interactions tocan WebdriverIO.

## Prohibido en Mobile

- `@serenity-js/web` (no funciona en NATIVE_APP).
- `PageElement`, `By`, `Click`, `Enter`, `Text` de Serenity/JS web.
- `browser.$` directo en Tasks o Steps.
- Hard waits (`browser.pause`, `setTimeout`).

## Checklist de calidad

- [ ] El contexto está claro (Mobile nativo)
- [ ] Los imports NO usan `@serenity-js/web`
- [ ] Selectores son `string`, no `PageElement`
- [ ] `browser.$` solo dentro de Interactions o Questions
- [ ] `waitForExist` + `waitForDisplayed` antes de cada acción
- [ ] `PlatformUI` se usa cuando aplica multiplataforma
