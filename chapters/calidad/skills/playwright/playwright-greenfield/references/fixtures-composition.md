
# Composición de fixtures

## Convención

- Un único `fixtures/base.fixture.ts` extiende `test` con todos los Page Objects.
- Cada Page Object se expone como fixture nombrado en lowercase (ej. `usersPage`).
- `mockApi` se declara como **fixture opt-in** (NO `auto`). Cada test que lo necesite lo inyecta explícitamente en su firma; los tests que no lo inyectan corren contra backend real. Esto evita el bug histórico de convertir toda suite E2E en una suite de contrato del mock.
- Se re-exporta `expect` desde el mismo módulo para que los tests importen `test` y `expect` desde un único punto.

## Anti-patrón corregido

```typescript
// INCORRECTO — convierte TODOS los tests en mocked, aunque no lo declaren
mockApi: [async ({ page }, use) => {
  await setupMocks(page);
  await use();
}, { auto: true }],
```

El flag `{ auto: true }` hacía que `setupMocks` corriera antes de cada test, incluso los que querían validar integración real. Eso oculta bugs de backend y de contrato.

## Snippet — `fixtures/base.fixture.ts`

```typescript
import { test as base } from '@playwright/test';
import { UsersPage } from '@pages/UsersPage';
import { OrdersPage } from '@pages/OrdersPage';
import { setupMocks } from '@mocks/api-handlers';

type Pages = {
  usersPage: UsersPage;
  ordersPage: OrdersPage;
  mockApi: void;
};

export const test = base.extend<Pages>({
  usersPage: async ({ page }, use) => {
    await use(new UsersPage(page));
  },
  ordersPage: async ({ page }, use) => {
    await use(new OrdersPage(page));
  },
  // Fixture opt-in: solo corre setupMocks cuando un test lo inyecta explícitamente.
  // NO lleva { auto: true } a propósito.
  mockApi: async ({ page }, use) => {
    await setupMocks(page);
    await use();
  },
});

export { expect } from '@playwright/test';
```

## Uso en tests — `usersPage` y `mockApi` son independientes

```typescript
import { test, expect } from '@fixtures/base.fixture';

// Test @live — usa usersPage SIN inyectar mockApi
test('@live crea un usuario contra backend real', async ({ page, usersPage }) => {
  await usersPage.navigate();
  await usersPage.createUser({ email: 'real@example.com', firstName: 'Alice' });
  await expect(page.getByText('User created')).toBeVisible();
});

// Test @mocked — inyecta mockApi explícitamente
test('@mocked muestra error cuando POST /users devuelve 500', async ({ page, usersPage, mockApi }) => {
  await usersPage.navigate();
  await usersPage.createUser({ email: 'mock@example.com', firstName: 'Bob' });
  await expect(page.getByText('Server error')).toBeVisible();
});
```

## Nota sobre el proyecto sin mocks

Si el usuario no declaró `mock_mode` ni `mock_endpoints`, **no** se genera la carpeta `mocks/` ni se declara el fixture `mockApi`. El archivo `fixtures/base.fixture.ts` solo compone Page Objects. Esto es el caso por defecto.
