
# Mocks con `page.route()` (módulo opt-in)

## Framing — esto NO es infraestructura por defecto

Mockear la red con `page.route()` convierte un test E2E en un **test de contrato del mock**: la suite puede pasar verde aunque el backend esté caído o haya cambiado el contrato. Por eso, en esta convención los mocks son un **módulo opt-in**, no parte del runtime por defecto.

- La suite de smoke / regresión por defecto corre contra backend real (tag `@live`).
- Los mocks se activan solo cuando el test lleva el tag `@mocked` (mock total) o `@hybrid` (mock dirigido).
- El fixture `mockApi` NO es `auto`: cada test lo inyecta explícitamente cuando quiere mocks (ver `[fixtures](fixtures-composition.md)`).

Detalle de modos y filtros en `[execution-modes-live-mocked-hybrid](execution-modes-live-mocked-hybrid.md)`.

## Patrón de tags

```typescript
import { test, expect } from '@fixtures/base.fixture';

test('@live crea un usuario contra backend real', async ({ page, usersPage }) => {
  await usersPage.navigate();
  await usersPage.createUser({ email: 'real@example.com', firstName: 'Alice' });
  await expect(page.getByText('User created')).toBeVisible();
});

test('@mocked maneja error 500 del backend', async ({ page, usersPage, mockApi }) => {
  // mockApi inyectado explícitamente → setupMocks(page) corre antes del test
  await usersPage.navigate();
  await usersPage.createUser({ email: 'mock@example.com', firstName: 'Bob' });
  await expect(page.getByText('Server error')).toBeVisible();
});
```

Filtros por CLI:

```bash
npx playwright test --grep @live      # ejecución por defecto en CI
npx playwright test --grep @mocked    # ejecución sin backend (dev offline)
npx playwright test --grep "@live|@hybrid"
```

## Fuentes válidas para `mock_endpoints` (orden de preferencia)

Cuando el QA activa mocks, hay que enumerar qué endpoints interceptar. Las fuentes válidas, de mayor a menor fidelidad respecto a lo que el frontend realmente llama:

1. **Captura del live app** (Playwright Codegen / MCP browser / HAR export del navegador) — refleja exactamente lo que el frontend invoca; cero drift.
2. **Postman collection** del equipo backend — curada por humanos, suele estar actualizada en proyectos con CI/CD maduro.
3. **OpenAPI / Swagger** del backend — útil como starting reference cuando no hay live app y no existe Postman; verificar contra una corrida `@live` antes de promover los mocks a regresión, porque el spec puede divergir de la implementación.
4. **Lista manual** del QA — fallback cuando ninguna de las anteriores está disponible.

El criterio es la fidelidad respecto al runtime: cualquier fuente sirve, pero las primeras dejan menos margen para que el mock no coincida con la realidad del backend.

## Reglas de agrupamiento (cuando los mocks SÍ aplican)

- Un único `setupMocks(page)` exportado desde `mocks/api-handlers.ts`.
- Una llamada a `page.route()` por path, no por método. Dentro del handler, se hace `switch` sobre `route.request().method()` para responder GET/POST/PUT/DELETE.
- Convertir cualquier placeholder de id en el path (`{id}`, `:id`, `[id]` según la convención de la fuente desde la que se capturaron los endpoints) a `*` en el patrón Playwright: `/api/v1/users/{id}` → `**/api/v1/users/*`.
- ID dinámico para POST con `let nextId = 1000; const id = nextId++;`.
- DELETE responde `204` sin body.
- Cualquier method no manejado cae a `route.continue()` para no romper otras llamadas.
- En modo `@hybrid`, los paths no listados **no se registran**, de forma que el backend real siga atendiéndolos.

## Snippet — `mocks/api-handlers.ts`

```typescript
import { Page } from '@playwright/test';

export async function setupMocks(page: Page): Promise<void> {
  let nextId = 1000;

  await page.route('**/api/v1/users', async (route) => {
    const method = route.request().method();
    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, email: 'test@example.com', firstName: 'Test' },
        ]),
      });
    } else if (method === 'POST') {
      const id = nextId++;
      const body = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({ id, ...body }),
      });
    } else {
      await route.continue();
    }
  });

  await page.route('**/api/v1/users/*', async (route) => {
    const method = route.request().method();
    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, email: 'test@example.com', firstName: 'Test' }),
      });
    } else if (method === 'PUT') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ id: 1, email: 'updated@example.com', firstName: 'Updated' }),
      });
    } else if (method === 'DELETE') {
      await route.fulfill({ status: 204 });
    } else {
      await route.continue();
    }
  });
}
```

## Cuándo NO mockear

- Smoke pipeline: siempre `@live`, sin excepciones.
- Validar contratos reales backend-frontend (para esto se usa `[[karate-greenfield]]`, no Playwright).
- Pruebas de regresión que el negocio cuenta como evidencia de integración funcionando.

## Cuándo SÍ mockear

- Aislar la UI para reproducir error states (500, 429, timeouts) difíciles de provocar en backend real.
- Desarrollo offline cuando el backend no está disponible localmente.
- Regression del propio mock cuando otros equipos lo consumen como contrato.
