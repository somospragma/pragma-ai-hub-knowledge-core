
# Page Object Model

## Convención

- Una clase por página, en `pages/{Name}Page.ts`. El nombre del archivo y la clase usan sufijo `Page` (ej. `UsersPage`, `OrderDetailPage`).
- Constructor recibe `Page` como `private` parameter shorthand: `constructor(private page: Page) {}`.
- Locators como propiedades `readonly` inicializadas inline desde `this.page`.
- Métodos de acción son `async`, expresan intención del usuario (ej. `createUser`, `search`, `deleteUser`) y no retornan Locators salvo casos puntuales.
- No se hacen aserciones dentro del Page Object: las aserciones viven en el `.spec.ts`.

## Snippet — `pages/UsersPage.ts`

```typescript
import { Page, Locator } from '@playwright/test';

export class UsersPage {
  constructor(private page: Page) {}

  readonly searchInput: Locator = this.page.getByPlaceholder('Search users');
  readonly addButton: Locator = this.page.getByRole('button', { name: 'Add User' });
  readonly emailInput: Locator = this.page.getByLabel('Email');
  readonly firstNameInput: Locator = this.page.getByLabel('First Name');
  readonly submitButton: Locator = this.page.getByRole('button', { name: 'Submit' });
  readonly rows: Locator = this.page.getByRole('row');

  async navigate(path: string = '/users'): Promise<void> {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async createUser(user: { email: string; firstName: string }): Promise<void> {
    await this.addButton.click();
    await this.emailInput.fill(user.email);
    await this.firstNameInput.fill(user.firstName);
    await this.submitButton.click();
  }

  async getRowCount(): Promise<number> {
    return await this.rows.count();
  }

  async deleteUser(email: string): Promise<void> {
    const row = this.page.getByRole('row', { name: new RegExp(email) });
    await row.getByRole('button', { name: 'Delete' }).click();
    await this.page.getByRole('button', { name: 'Confirm' }).click();
  }
}
```

## Anti-patrón: rutas inventadas

El método `navigate()` de cada Page Object **debe usar la ruta frontend real** obtenida desde la fuente UI (URL crawled, ruta documentada en Figma, configuración del router del SPA). Nunca debe derivarse del path backend de un OpenAPI.

### Por qué

- Backend y frontend viven en dominios distintos: `/api/v1/users` (backend) no es `/users` (frontend), aunque parezcan paralelos.
- Un endpoint REST puede no tener ninguna página dedicada (lo consume otra página vía AJAX), o puede repartirse en varias (wizard de 3 pasos para `POST /orders`).
- Los SPAs reescriben rutas en cliente (`/users/:id` con React Router, `/users/[id]` con Next.js, hash routing `#/users/1`); inferir desde el spec genera URLs que no existen.

### Incorrecto

```typescript
// MAL — la ruta `/api/v1/users` salió del path de un OpenAPI
async navigate(): Promise<void> {
  await this.page.goto('/api/v1/users'); // 404 en el frontend
}
```

### Correcto

```typescript
// BIEN — ruta obtenida de Playwright Codegen sobre la app viva,
// o del router del SPA, o de un screenshot de Figma con la URL anotada.
async navigate(path: string = '/users'): Promise<void> {
  await this.page.goto(path);
  await this.page.waitForLoadState('networkidle');
}
```

Si la ruta frontend no está disponible en la fuente UI, **detente y solicítala al usuario**; no la inventes.

