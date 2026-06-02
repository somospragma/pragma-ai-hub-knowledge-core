---
id: playwright-generate-mock-handlers-prompt
version: 2.0.0
scope: stack
type: prompt
chapter: calidad
stack: [playwright]
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

- `{{endpoints}}` — Lista declarativa de endpoints `{ path, method, status, sample_response? }` que el usuario quiere mockear. Fuentes válidas, en orden de preferencia: **(a)** captura del live app vía Playwright Codegen / MCP browser / HAR export del navegador (refleja lo que el frontend realmente llama); **(b)** Postman collection entregada por el equipo backend; **(c)** lista manual del QA. **No se acepta OpenAPI/Swagger** como fuente: el contrato declarado en spec puede divergir de lo que el frontend invoca en runtime y mezclar fuentes induce mocks irreales.
- `{{sample_payloads}}` — Mapa opcional de payloads de muestra capturados desde el live app o construidos manualmente. NO se autogenera desde un schema OpenAPI.
- `{{mock_mode}}` — `full | partial`. Cuando es `partial`, los paths no listados deben caer a `route.continue()` (no romper integración real).

## Instrucción para el LLM

Genera UN solo archivo `mocks/api-handlers.ts` siguiendo estrictamente `[ver mocks](../../skills/playwright/playwright-greenfield/references/mocks-page-route.md)`:

- Exporta `async function setupMocks(page: Page): Promise<void>`.
- Declara `let nextId = 1000;` al inicio.
- Agrupa los endpoints por path: una sola llamada a `page.route()` por path, con `switch` sobre `route.request().method()` adentro.
- Convierte cualquier placeholder de ID en el path (`{id}`, `:id`, `[id]` según el router del frontend o la convención de la fuente capturada) a `*` en el patrón Playwright: `/api/v1/users/{id}` → `**/api/v1/users/*`.
- Para POST: genera body de respuesta con `const id = nextId++;` y mergea el `postDataJSON()` cuando aplique.
- Para DELETE: responde `{ status: 204 }` sin body.
- Cualquier method no manejado en el path: `await route.continue();`.
- Bodies sintéticos derivados de `{{sample_payloads}}` (capturados de la app viva o provistos manualmente). NO inventes campos no observados; si falta información, deja un `// TODO: capturar payload real desde la app viva` y avísalo en el reporte de salida.
- Si `{{mock_mode}}` es `partial`, cualquier path no presente en `{{endpoints}}` debe quedar implícito (no registrar handler), de modo que las llamadas no listadas alcancen el backend real.

## Recordatorio sobre el riesgo de mockear

Los tests `@mocked` validan que el frontend habla con el contrato del mock, no con el backend real. Pueden pasar verde aunque la API esté caída. La estrategia recomendada es: smoke suite siempre `@live`; mocks solo para aislamiento UI puntual, contract regression del mock o desarrollo offline. Ver `[execution-modes-live-mocked-hybrid](../../skills/playwright/playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`.

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
