---
id: playwright-detect-pages-from-ui-source-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [automation]
description: Prompt que detecta páginas frontend, form fields, navegación y selectores a partir de una fuente UI real (URL viva, Figma, user story, Storybook). La prioridad se recibe como input externo, nunca se infiere por keyword.
tags: [playwright, prompt, ui-first, page-detection, live-app, figma, storybook]
---

# Prompt — Detectar páginas desde fuente UI

## Variables

- `{{ui_source_type}}` — Tipo de fuente UI. Valores válidos: `live-url | figma | user-story | storybook | hybrid`.
- `{{ui_source_content}}` — Contenido concreto de la fuente:
  - Si `live-url`: URL de la app + (opcional) JSON con el resultado de Playwright Codegen / MCP browser crawl (rutas, selectores, headings).
  - Si `figma`: link a Figma + lista de screenshots y descripción de páginas/componentes/rutas tentativas.
  - Si `user-story`: texto de la historia con flujos UI explícitos (páginas visitadas, acciones por página, transiciones).
  - Si `storybook`: URL del Storybook + listado de stories/componentes y sus rutas de demo.
  - Si `hybrid`: combinación de varios; cada bloque debe declarar su `type`.
- `{{user_story}}` — (opcional) Contexto funcional adicional.
- `{{priority_assignments}}` — Mapa `pageName -> priority` (`CRITICAL | HIGH | MEDIUM | LOW`) provisto por el usuario o Product Owner. La prioridad **NO se infiere**: viene de aquí o el resultado debe marcarla como `UNKNOWN` y solicitarla.

## Reglas críticas

1. **El insumo debe describir UI**. Si el único input disponible es un OpenAPI/Swagger y no hay descripción UI real, **detente** y responde con un error explícito:

   ```json
   { "error": "OpenAPI no es una fuente válida de UI. Solicita una de: URL viva, Figma, user story con flujos UI, Storybook." }
   ```

   No infieras páginas a partir de endpoints, paths, tags ni del bloque `security`.

2. **`route` es la ruta frontend** (la que aparece en el navegador / router del SPA), nunca el path backend. Si la fuente UI no la provee, márcala como `route: "?"` y pide al usuario que la complete.

3. **`page_type` y `priority` provienen de `{{priority_assignments}}`** (o quedan `UNKNOWN`). No los infieras desde el nombre (`login` no es automáticamente `CRITICAL`, `profile` no es automáticamente `MEDIUM`).

4. **`form_fields`, `navigation`, `selectors_hint`** provienen exclusivamente de la fuente UI:
   - Codegen / MCP devuelve selectores reales → úsalos con prioridad `getByTestId > getByRole > getByLabel > getByText`.
   - Figma / user story → describe lo observable (label, placeholder, button text); marca `selectors_hint` como `inferred` para que el desarrollador los valide después contra el DOM real.

5. **No inventes páginas** que no aparezcan en la fuente UI provista. Una API REST con 20 endpoints puede corresponder a una sola página SPA o a un wizard de 5 pasos: la fuente UI manda.

## Formato de salida (JSON)

```json
{
  "ui_source_type": "live-url",
  "pages": [
    {
      "name": "UsersPage",
      "route": "/users",
      "page_type": "list",
      "priority": "MEDIUM",
      "priority_source": "priority_assignments",
      "form_fields": [],
      "navigation": [
        { "label": "Add User", "target": "UserFormPage" },
        { "label": "View detail", "target": "UserDetailPage" }
      ],
      "selectors_hint": {
        "addButton": { "strategy": "getByRole", "args": "{ name: 'Add User' }", "source": "codegen" }
      }
    },
    {
      "name": "UserDetailPage",
      "route": "/users/:id",
      "page_type": "detail",
      "priority": "UNKNOWN",
      "priority_source": "missing",
      "form_fields": [
        { "name": "email", "type": "email", "required": true, "source": "codegen" },
        { "name": "firstName", "type": "text", "required": true, "source": "codegen" }
      ],
      "navigation": [
        { "label": "Back to list", "target": "UsersPage" }
      ],
      "selectors_hint": {
        "emailInput": { "strategy": "getByLabel", "args": "'Email'", "source": "codegen" }
      }
    }
  ],
  "warnings": [
    "UserDetailPage no tiene priority asignada en priority_assignments — solicita al PO."
  ]
}
```

## Notas

- `priority_source` registra de dónde salió la prioridad: `priority_assignments`, `user_story`, `missing`. Nunca `inferred-from-name`.
- Si `{{ui_source_type}}` es `figma` o `user-story`, marca todos los `selectors_hint` con `"source": "inferred"`: el desarrollador deberá validarlos contra el DOM real antes de mergear.
- `route` admite el formato del router del frontend (`/users/:id`, `/users/[id]`). NO uses el patrón OpenAPI `{id}` salvo que la fuente UI lo use literalmente.
