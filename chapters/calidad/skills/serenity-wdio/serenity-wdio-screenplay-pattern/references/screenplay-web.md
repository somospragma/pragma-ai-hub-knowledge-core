# Screenplay Pattern — Implementación Web

## Imports correctos (v3)

```typescript
import { Task, Duration, Answerable } from '@serenity-js/core';
import { Click, Enter, Clear, Wait, PageElement, By } from '@serenity-js/web';
import { isClickable, isVisible, not } from '@serenity-js/assertions';
```

## UI Mapping con PageElement

```typescript
// features/web/UI/<Modulo>/<Modulo>UI.ts
import { PageElement, By } from '@serenity-js/web';

export class LoginUI {
  static buttonLogin = () =>
    PageElement.located(By.xpath("//button[@id='btn-login']"))
               .describedAs('button for login');

  static userInput = () =>
    PageElement.located(By.css('input#username'))
               .describedAs('input for user');
}
```

Prioridad de selectores en Web:

1. `By.id('...')`
2. `By.css('[data-testid="..."]')`
3. Texto visible (`PageElements.located(...).where(Text, includes('...'))`)
4. `By.css('...')`
5. `By.xpath('...')` (último recurso)

## Task con Task.where

```typescript
// features/web/Tasks/<Modulo>/<Task>.ts
import { Task } from '@serenity-js/core';
import { ClickWhenReady } from '../../shared/Tasks/ClickWhenReady';
import { ClearAndEnter } from '../../shared/Tasks/ClearAndEnter';
import { LoginUI } from '../../UI/Login/LoginUI';

export class LoginTask {
  static signInWith = (user: string, password: string) =>
    Task.where(
      `#actor inicia sesión con el usuario ${ user }`,
      ClearAndEnter.theValue(user).into(LoginUI.userInput()),
      ClearAndEnter.theValue(password).into(LoginUI.passwordInput()),
      ClickWhenReady.on(LoginUI.buttonLogin()),
    );
}
```

## Shared Tasks reutilizables (web)

```typescript
// features/web/shared/Tasks/ClickWhenReady.ts
import { Task, Duration, Answerable } from '@serenity-js/core';
import { Click, Wait, PageElement } from '@serenity-js/web';
import { isClickable } from '@serenity-js/assertions';

export class ClickWhenReady {
  static on = (element: Answerable<PageElement>) =>
    Task.where(`#actor hace clic cuando el elemento está listo`,
      Wait.upTo(Duration.ofSeconds(10)).until(element, isClickable()),
      Click.on(element),
    );
}

// features/web/shared/Tasks/ClearAndEnter.ts
import { Clear, Enter } from '@serenity-js/web';

export class ClearAndEnter {
  static theValue = (value: string) => ({
    into: (element: Answerable<PageElement>) =>
      Task.where(`#actor limpia y escribe "${ value }"`,
        Clear.theValueOf(element),
        Enter.theValue(value).into(element),
      ),
  });
}

// features/web/shared/Tasks/WaitUntilGone.ts
import { Wait } from '@serenity-js/web';
import { isVisible, not } from '@serenity-js/assertions';

export const WaitUntilGone = {
  the: (element: Answerable<PageElement>) =>
    Task.where(`#actor espera que el elemento desaparezca`,
      Wait.upTo(Duration.ofSeconds(30)).until(element, not(isVisible())),
    ),
};
```

## Question (web) — usar APIs nativas

```typescript
import { Text } from '@serenity-js/web';
import { Ensure, equals } from '@serenity-js/assertions';

// Uso directo en Then:
await actor.attemptsTo(
  Ensure.that(Text.of(LoginUI.welcomeMessage()), equals('Bienvenido')),
);
```

## Obligatorio en Web

- `@serenity-js/web` para todo (Click, Enter, Clear, Wait, Text, PageElement, By).
- `Wait.until(element, isClickable())` o `isVisible()` antes de interactuar.
- `Task.where()` para componer Interactions.
- `describedAs(...)` en cada PageElement (mejora reportes).
- `'wdio:enforceWebDriverClassic': true` en TODA capability de navegador del config.

## Prohibido en Web

- `browser.$(...)` directo en Tasks o Steps.
- `Target` (API legacy de Serenity/JS v2).
- `resolveFor(actor)` (anti-patrón).
- `browser.pause()` o `setTimeout`.
- Callbacks en `Task.where` (siempre `async/await` en Interactions).

## Checklist de calidad

- [ ] El contexto está claro (Web)
- [ ] Los imports usan `@serenity-js/web`
- [ ] Cada Task tiene una descripción `#actor ...` clara y de negocio
- [ ] Los selectores siguen la prioridad correcta (id → testid → texto → css → xpath)
- [ ] No hay hard waits
- [ ] Las Tasks reutilizan Tasks/Interactions existentes en `shared/`
- [ ] PageElements tienen `describedAs(...)`
