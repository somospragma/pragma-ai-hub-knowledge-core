# Convenciones Screenplay (Serenity WDIO Greenfield)

Screenplay Pattern puro con Serenity/JS v3 como orquestador. Componentes y responsabilidades:

| Componente | Responsabilidad | Ejemplo |
|---|---|---|
| Actors | Quien ejecuta | `actorCalled('Ana')` |
| Tasks | Que hace (negocio) | `LoginTask.signInWith(user, pass)` |
| Interactions | Como lo hace (tecnico) | `Tap.on(selector)`, `Click.on(element)` |
| Questions | Que observa | `TextOf(selector)`, `Text.of(element)` |
| UI Mapping | Donde esta | `LoginUI.buttonLogin()` |

## Web (obligatorio `@serenity-js/web`)

```typescript
// UI mapping con PageElement + By
export class LoginUI {
  static buttonLogin = () =>
    PageElement.located(By.xpath("//button[@id='btn-login']"))
               .describedAs('button for login');
}

// Task que compone Interactions con Task.where
export class ClickWhenReady {
  static on = (element: Answerable<PageElement>) =>
    Task.where(`#actor hace clic cuando el elemento esta listo`,
      Wait.upTo(Duration.ofSeconds(10)).until(element, isClickable()),
      Click.on(element),
    );
}
```

## Mobile nativo (selectores como string, sin `@serenity-js/web`)

WebdriverIO (`browser.$`) permitido SOLO encapsulado dentro de una Interaction, nunca expuesto en Tasks ni Steps.

```typescript
// Interaction que encapsula browser.$
export class Tap extends Interaction {
  static on(selector: string): Tap { return new Tap(selector); }
  constructor(private readonly selector: string) {
    super(`#actor taps on ${selector}`);
  }
  async performAs(_actor: UsesAbilities & AnswersQuestions): Promise<void> {
    const el = await browser.$(this.selector);
    await el.waitForExist({ timeout: 15_000 });
    await el.waitForDisplayed({ timeout: 15_000 });
    await el.click();
  }
}

// UI mapping con selectores string (Accessibility ID prioritario)
export const LoginUI = {
  button_login: '~login-button',
  input_user: '~username-input',
  input_password: '~password-input',
};
```

## Prohibiciones

- `Target` (API v2 legacy).
- `resolveFor(actor)` (anti-patron).
- `browser.$` directo en Tasks o Steps (solo dentro de Interactions en mobile).
- Hard waits (`browser.pause()`, `setTimeout`).
- Callbacks en `Task.where` (usar `async/await`).
- Questions con efectos secundarios.
- `@serenity-js/web` y `PageElement` en mobile.

## Estandares de codigo

- TypeScript `strict: true`, `async/await` siempre, DRY y SOLID.
- Prioridad de selectores: Accessibility ID (`~id`), TestID, texto visible, CSS (web), XPath (ultimo recurso).
- `setDefaultTimeout` explicito en cada archivo de steps.
