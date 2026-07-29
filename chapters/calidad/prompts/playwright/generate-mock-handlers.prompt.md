---
id: calidad-playwright-generate-mock-handlers-prompt
version: 2.1.0
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

Si el workflow `[[calidad-generate-playwright-greenfield]]` no recibió esos campos en sus inputs, **omite este prompt** y no generes la carpeta `mocks/`.

## Variables

- `{{endpoints}}` — Lista declarativa de endpoints `{ path, method, status, sample_response? }` que el usuario quiere mockear. Fuentes válidas en orden de preferencia (ver [[calidad-playwright-greenfield]] (consultar `references/mocks-page-route.md`)): captura del live app (Codegen/MCP/HAR) → Postman collection → OpenAPI/Swagger del backend → lista manual.
- `{{sample_payloads}}` — Mapa opcional de payloads de muestra. Preferir capturas reales del live app; payloads inferidos desde un schema (OpenAPI o Postman example) son aceptables como punto de partida pero deben revisarse contra runtime.
- `{{mock_mode}}` — `full | partial`. Cuando es `partial`, los paths no listados deben caer a `route.continue()` (no romper integración real).

## Instrucción para el LLM

Genera UN solo archivo `mocks/api-handlers.ts` siguiendo estrictamente [[calidad-playwright-greenfield]] (consultar `references/mocks-page-route.md`):

- Exporta `async function setupMocks(page: Page): Promise<void>`.
- Declara `let nextId = 1000;` al inicio.
- Agrupa los endpoints por path: una sola llamada a `page.route()` por path, con `switch` sobre `route.request().method()` adentro.
- Convierte cualquier placeholder de ID en el path (`{id}`, `:id`, `[id]` según el router del frontend o la convención de la fuente capturada) a `*` en el patrón Playwright: `/api/v1/users/{id}` → `**/api/v1/users/*`.
- Para POST: genera body de respuesta con `const id = nextId++;` y mergea el `postDataJSON()` cuando aplique.
- Para DELETE: responde `{ status: 204 }` sin body.
- Cualquier method no manejado en el path: `await route.continue();`.
- Bodies sintéticos derivados de `{{sample_payloads}}` cuando estén disponibles. Si falta información, deja un `// TODO: validar payload contra runtime` y avísalo en el reporte de salida.
- Si `{{mock_mode}}` es `partial`, cualquier path no presente en `{{endpoints}}` debe quedar implícito (no registrar handler), de modo que las llamadas no listadas alcancen el backend real.

## Recordatorio sobre el riesgo de mockear

Los tests `@mocked` validan que el frontend habla con el contrato del mock, no con el backend real. Pueden pasar verde aunque la API esté caída. La estrategia recomendada es: smoke suite siempre `@live`; mocks solo para aislamiento UI puntual, contract regression del mock o desarrollo offline. Ver [[calidad-playwright-greenfield]] (consultar `references/execution-modes-live-mocked-hybrid.md`).

**Propósito de estos mocks**: habilitar la interacción y navegación del front que depende del backend — NO probar los servicios. Los tests que consuman estos handlers asertan UI (navegación, estados visibles, mensajes); NUNCA generes tests que validen status code, schema o campos del response mockeado como si fueran pruebas de contrato — eso pertenece a Karate.

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
