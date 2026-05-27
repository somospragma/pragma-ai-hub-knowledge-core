---
id: playwright-generate-mock-handlers-prompt
version: 2.0.0
scope: stack
type: prompt
chapter: calidad
stack: [automation]
description: Prompt opt-in que genera setupMocks(page) agrupando methods por path. Solo se invoca cuando el usuario declara mock_mode o mock_endpoints; NUNCA se ejecuta por defecto.
tags: [playwright, prompt, mocks, page-route, network-interception, opt-in]
---

# Prompt — Generar mock handlers (opt-in)

## Cuándo invocar este prompt

**Por defecto NO se invoca.** Las suites Playwright corren contra backend real (`@live`). Este prompt se activa solo cuando el usuario declara explícitamente uno de:

- `mock_mode: full` — toda la red interceptada (tests con tag `@mocked`).
- `mock_endpoints: ["/api/v1/users", ...]` — mock dirigido para suite híbrida (tests con tag `@hybrid`).

Si el workflow `[[generate-playwright-greenfield]]` no recibió esos campos en sus inputs, **omite este prompt** y no generes la carpeta `mocks/`.

## Variables

- `{{endpoints}}` — Lista de endpoints `{ path, method, status, requestSchema?, responseSchema? }` que el usuario quiere mockear (subset de un OpenAPI, o lista manual).
- `{{response_schemas}}` — Mapa de schemas para construir bodies sintéticos válidos.
- `{{mock_mode}}` — `full | partial`. Cuando es `partial`, los paths no listados deben caer a `route.continue()` (no romper integración real).

## Instrucción para el LLM

Genera UN solo archivo `mocks/api-handlers.ts` siguiendo estrictamente `[ver mocks](../../skills/automation/playwright/playwright-greenfield/references/mocks-page-route.md)`:

- Exporta `async function setupMocks(page: Page): Promise<void>`.
- Declara `let nextId = 1000;` al inicio.
- Agrupa los endpoints por path: una sola llamada a `page.route()` por path, con `switch` sobre `route.request().method()` adentro.
- Convierte `{id}` (estilo OpenAPI) a `*` en el patrón Playwright: `/api/v1/users/{id}` → `**/api/v1/users/*`.
- Para POST: genera body de respuesta con `const id = nextId++;` y mergea el `postDataJSON()` cuando aplique.
- Para DELETE: responde `{ status: 204 }` sin body.
- Cualquier method no manejado en el path: `await route.continue();`.
- Bodies sintéticos derivados de `{{response_schemas}}`. NO inventes campos fuera de los schemas.
- Si `{{mock_mode}}` es `partial`, cualquier path no presente en `{{endpoints}}` debe quedar implícito (no registrar handler), de modo que las llamadas no listadas alcancen el backend real.

## Recordatorio sobre el riesgo de mockear

Los tests `@mocked` validan que el frontend habla con el contrato del mock, no con el backend real. Pueden pasar verde aunque la API esté caída. La estrategia recomendada es: smoke suite siempre `@live`; mocks solo para aislamiento UI puntual, contract regression del mock o desarrollo offline. Ver `[execution-modes-live-mocked-hybrid](../../skills/automation/playwright/playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`.

## Snippet de salida esperado

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
        body: JSON.stringify([{ id: 1, email: 'test@example.com', firstName: 'Test' }]),
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
