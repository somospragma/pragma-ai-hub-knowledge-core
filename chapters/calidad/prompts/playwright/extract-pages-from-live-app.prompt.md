---
id: calidad-playwright-extract-pages-from-live-app-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [playwright]
description: Prompt para explorar una aplicación web viva (vía browser MCP o Playwright Codegen) y devolver páginas, selectores reales con prioridad getByTestId > getByRole, navegación y form fields.
tags: [playwright, prompt, live-app, codegen, mcp, exploration]
---

# Prompt — Extraer páginas desde aplicación viva

## Asunciones

Este prompt asume que el LLM ejecutor tiene acceso a herramientas de browser (MCP browser tools tipo `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_fill`) o puede ejecutar `npx playwright codegen` y leer su output. Si ninguna está disponible, **detente** y solicita al usuario que ejecute Playwright Codegen manualmente y comparta el snippet.

## Variables

- `{{base_url}}` — URL de la app viva (raíz). Ejemplo: `https://app.dev.example.com`.
- `{{auth_credentials}}` — (opcional) Credenciales para autenticar antes de explorar. Formato `{ "email": "...", "password": "..." }` o `{ "storageState": "..." }`.
- `{{flows_to_explore}}` — Lista de user stories / flujos UI a recorrer. Cada item incluye `name`, `steps[]` y opcionalmente `priority`.

## Instrucción para el LLM

1. **Autenticar (si aplica)** — Si `{{auth_credentials}}` está presente, navega a la página de login, completa el form y guarda el storageState.
2. **Recorrer flujos** — Para cada flow en `{{flows_to_explore}}`:
   - Navega los pasos enumerados.
   - Después de cada navegación, captura `window.location.pathname` como `route` frontend de la página actual.
   - Toma un snapshot del DOM (accessibility tree).
   - Identifica heading principal (`getByRole('heading', { level: 1 })`).
   - Enumera form fields visibles (inputs, selects, textareas) con su `label`, `placeholder`, `type`, `required`.
   - Enumera botones, links y otros controles de navegación.
3. **Extraer selectores con prioridad**:
   - `getByTestId` si el elemento tiene `data-testid` (preferido).
   - `getByRole` con `name` accesible si no hay testid.
   - `getByLabel` para inputs con `<label>` asociado.
   - `getByPlaceholder` o `getByText` como fallback.
   - **Nunca** XPath ni selectores CSS frágiles (clases generadas, índices).
4. **Marcar páginas sin testids** — Si una página no expone ningún `data-testid` en sus controles principales, márcala con `"needs_testid": true` y deja una recomendación.
5. **NO inventes** páginas ni flujos no declarados en `{{flows_to_explore}}`. Si la exploración detecta páginas adicionales (modales, redirecciones inesperadas), repórtalas en `discovered_pages` para revisión humana.
6. **Capturar errores** — Si un step falla (404, timeout, selector no encontrado), regístralo en `exploration_errors` con el flow y step exactos.

## Formato de salida (JSON)

```json
{
  "base_url": "https://app.dev.example.com",
  "pages": [
    {
      "name": "UsersPage",
      "route": "/users",
      "page_type": "list",
      "priority": "UNKNOWN",
      "heading": "Users",
      "form_fields": [],
      "controls": [
        {
          "name": "addUserButton",
          "strategy": "getByTestId",
          "args": "'add-user-btn'",
          "source": "dom-snapshot"
        }
      ],
      "navigation": [
        { "label": "Add User", "target": "UserFormPage", "route": "/users/new" },
        { "label": "Row detail", "target": "UserDetailPage", "route": "/users/:id" }
      ],
      "needs_testid": false
    },
    {
      "name": "UserDetailPage",
      "route": "/users/:id",
      "page_type": "detail",
      "priority": "UNKNOWN",
      "heading": "User detail",
      "form_fields": [
        {
          "name": "email",
          "type": "email",
          "required": true,
          "selector": { "strategy": "getByLabel", "args": "'Email'" }
        },
        {
          "name": "firstName",
          "type": "text",
          "required": true,
          "selector": { "strategy": "getByLabel", "args": "'First Name'" }
        }
      ],
      "controls": [
        {
          "name": "saveButton",
          "strategy": "getByRole",
          "args": "'button', { name: 'Save' }",
          "source": "dom-snapshot"
        }
      ],
      "navigation": [
        { "label": "Back", "target": "UsersPage", "route": "/users" }
      ],
      "needs_testid": true,
      "recommendation": "Solicitar al equipo frontend agregar data-testid a botones de acción."
    }
  ],
  "discovered_pages": [
    {
      "route": "/notifications",
      "reason": "Click en bell icon redirigió a esta ruta no declarada en flows_to_explore."
    }
  ],
  "exploration_errors": []
}
```

## Notas

- `priority` siempre sale como `UNKNOWN` desde este prompt. El workflow caller debe completarla con `priority_assignments` del usuario/PO antes de generar tests. Nunca la infieras desde el nombre de la página.
- `route` usa el formato del router del frontend (`/users/:id`, `/users/[id]`). NO lo traduzcas a estilo OpenAPI (`{id}`).
- Si la app es un SPA con hash routing, registra la ruta con el `#` (`/#/users`).
- Los `selector` y `controls` deben ser ejecutables tal cual en Playwright: el QA debe poder copiar/pegar el snippet en un POM sin transformación.
