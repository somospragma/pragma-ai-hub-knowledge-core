---
id: playwright-generate-page-object-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [playwright]
description: Prompt que genera una clase Page Object TypeScript a partir de la especificación de página, form fields y navegación.
tags: [playwright, prompt, page-object-model, typescript]
---

# Prompt — Generar Page Object

## Variables

- `{{page_spec}}` — Spec de la página: `{ name, page_type, priority, route }`.
- `{{form_fields}}` — Lista de form fields con `{ name, type, format, required, enum, min, max }`.
- `{{navigation}}` — Lista de navegaciones salientes con `{ label, target }`.

## Instrucción para el LLM

Genera UNA clase TypeScript siguiendo estrictamente `[[playwright-page-object-model]]` y `[[playwright-selector-priority]]`:

- Archivo `pages/{{page_spec.name}}.ts`.
- Constructor `(private page: Page)`.
- Una propiedad `readonly` por cada form field y por cada navegación, usando primero `getByRole`, luego `getByLabel`, luego `getByPlaceholder`, luego `getByText`. Solo usar `getByTestId` si el caller lo indica explícitamente. Nunca XPath.
- Métodos `async` que expresen intención del usuario: `navigate`, `fill{Field}`, `submit`, `goTo{Target}`. Sin aserciones.
- Tipar parámetros y retornos. No usar `any`.
- No incluir imports innecesarios.

NO inventes campos, navegaciones ni acciones que no estén en `{{form_fields}}` o `{{navigation}}`.

## Snippet de salida esperado

```typescript
import { Page, Locator } from '@playwright/test';

export class UserFormPage {
  constructor(private page: Page) {}

  readonly emailInput: Locator = this.page.getByLabel('Email');
  readonly firstNameInput: Locator = this.page.getByLabel('First Name');
  readonly roleSelect: Locator = this.page.getByLabel('Role');
  readonly submitButton: Locator = this.page.getByRole('button', { name: 'Submit' });
  readonly backLink: Locator = this.page.getByRole('link', { name: 'Back to list' });

  async navigate(path: string = '/users/new'): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  async fillEmail(email: string): Promise<void> {
    await this.emailInput.fill(email);
  }

  async fillFirstName(firstName: string): Promise<void> {
    await this.firstNameInput.fill(firstName);
  }

  async selectRole(role: 'admin' | 'user'): Promise<void> {
    await this.roleSelect.selectOption(role);
  }

  async submit(): Promise<void> {
    await this.submitButton.click();
  }

  async goToUsersList(): Promise<void> {
    await this.backLink.click();
  }
}
```
