
# Estrategia de actualización de selectores

## Regla central

Cuando la UI cambia (nuevos labels, reorganización de inputs, traducción), se actualizan ÚNICAMENTE las asignaciones de Locator. Todo lo demás del archivo permanece literal:

- Imports
- Decoradores
- Modificadores (`readonly`, `private`, `public`)
- Types (`: Locator`)
- Métodos completos (signature, body, comments)
- Orden de propiedades
- Espaciado y comentarios

## Validación previa al cambio

Antes de aplicar el reemplazo, validar que el selector nuevo es **semántico**:

- Preferir `getByRole`, `getByLabel`, `getByPlaceholder`, `getByText`.
- Evitar introducir `locator(CSS)` salvo que el original ya lo usara y no haya alternativa semántica.
- Nunca introducir XPath donde no existía.
- Si el selector original era `getByTestId` y el HTML aún expone `data-testid`, mantenerlo.

## Snippet — antes / después

```typescript
// pages/LoginPage.ts — antes
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  readonly emailInput: Locator = this.page.getByLabel('Email');
  readonly passwordInput: Locator = this.page.getByLabel('Password');
  readonly submitButton: Locator = this.page.getByRole('button', { name: 'Sign in' });

  async navigate(): Promise<void> {
    await this.page.goto('/login');
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }

  async fillPassword(password: string): Promise<void> {
    await this.passwordInput.fill(password);
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }
}
```

```typescript
// pages/LoginPage.ts — después (UI traducida al español)
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  constructor(private page: Page) {}

  readonly emailInput: Locator = this.page.getByLabel('Correo electrónico');
  readonly passwordInput: Locator = this.page.getByLabel('Contraseña');
  readonly submitButton: Locator = this.page.getByRole('button', { name: 'Iniciar sesión' });

  async navigate(): Promise<void> {
    await this.page.goto('/login');
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }

  async fillPassword(password: string): Promise<void> {
    await this.passwordInput.fill(password);
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }
}
```

Único cambio: las cadenas dentro de `getByLabel` y `getByRole`. Métodos, imports, tipos y orden, intactos.
