---
id: calidad-figma-mcp-integration
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Cómo consumir archivos de Figma como fuente UI: conexión vía MCP (server oficial remoto/desktop o Framelink con PAT), solicitud segura del token, setup guiado por IDE y fallback REST API. Un link público de Figma NO es consumible sin esto."
tags: [figma, mcp, ui-source, pat, setup, playwright, appium, locator-map, design]
---

# Figma MCP Integration — Consumir Diseños de Figma como Fuente UI

## Problema que resuelve

Un enlace "público" de Figma **no es consumible por un agente con un fetch plano**: figma.com sirve una SPA que exige JavaScript y sesión; el HTML no contiene el diseño. Cuando el usuario entrega un link de Figma como `ui_source` (Playwright, locator map, revisión de accesibilidad desde diseño), la vía correcta es **MCP** o la **REST API** con autenticación. Este skill define cómo el agente establece esa conexión y, si no está configurada, cómo guía al usuario para configurarla y luego continúa con el flujo original.

## Cuándo aplicar

Cada vez que un flujo del chapter reciba Figma como insumo: fuente UI de [[calidad-playwright-greenfield]] (`references/ui-source-priority.md`), construcción del `[[calidad-ui-locator-map-contract]]`, revisión de diseño de `[[calidad-accessibility-testing]]` (`references/design-review.md`), o pantallas de referencia para Appium.

## Vías de conexión (elegir en este orden)

| Vía | Cuándo | Auth | Notas |
|---|---|---|---|
| 1. **MCP oficial remoto** (`https://mcp.figma.com/mcp`) | Default si el cliente MCP soporta servers HTTP remotos | OAuth gestionado por el cliente MCP | Disponible en todos los seats y planes; gratis durante beta (Figma anunció que será feature paga por uso). No requiere app desktop. |
| 2. **MCP oficial desktop** | Organizaciones que lo exijan / trabajo con selección en vivo | Sesión de la app desktop | Requiere app de Figma corriendo y seat Dev o Full en plan pago. |
| 3. **Framelink** (`figma-developer-mcp`, community) | Entornos headless/CI o clientes sin soporte de MCP remoto | **PAT** vía env var `FIGMA_API_KEY` | Solo lectura sobre la REST API; expone `get_figma_data` (estructura del archivo/nodo) y descarga de imágenes. |
| 4. **REST API directa** (fallback sin MCP) | Nada de lo anterior es viable | Header `X-Figma-Token: <PAT>` | `GET https://api.figma.com/v1/files/{file_key}`. Último recurso: el JSON crudo es verboso; preferir MCP. |

El `file_key` se extrae de la URL: `figma.com/design/{file_key}/{titulo}` (formato legacy: `figma.com/file/{file_key}/...`).

## PAT de Figma (vías 3 y 4)

- **Generación** (lo hace el usuario, nunca el agente): figma.com → menú de cuenta → Settings → pestaña **Security** → **Personal access tokens** → Generate new token.
- **Scopes mínimos de lectura**: `File content` (read) y `Dev resources` (read).
- **Manejo seguro**: el token se solicita al usuario, se inyecta por variable de entorno o config local del IDE y **JAMÁS se escribe en el repo, en un asset, en el STRATEGY.md ni en `.evidence/`**. Recomendar expiración corta al crearlo.

## Flujo del agente

```
1. ¿El cliente MCP ya tiene un server Figma configurado y responde?
   ├── Sí → probar con una tool de lectura (get_metadata / get_figma_data sobre el file_key). Si responde → consumir y continuar el flujo original.
   └── No → informar al usuario: "el link de Figma no es consumible sin conexión autenticada"
            y ofrecer el setup guiado (paso 2). NUNCA reportar "no puedo acceder" sin ofrecer la solución.
2. Setup guiado según IDE (snippets abajo): elegir vía (remoto OAuth si el cliente lo soporta;
   Framelink + PAT si no), pedir al usuario el PAT cuando aplique, escribir la config MCP local.
3. Reiniciar/recargar los MCP servers del IDE y volver al paso 1.
4. Si el usuario no puede/quiere configurar MCP → fallback REST API con PAT (vía 4).
5. Si tampoco hay PAT → pedir export estático del diseño (imágenes/PDF con jerarquía de pantallas)
   y continuar con las limitaciones documentadas en ui-source-priority (accuracy menor, selectores inferidos).
```

## Config por IDE (verificada contra doc oficial)

**Kiro** — `.kiro/settings/mcp.json` (workspace) o `~/.kiro/settings/mcp.json` (usuario):

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": { "FIGMA_API_KEY": "${FIGMA_API_KEY}" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Para el server oficial remoto, Kiro soporta `"url": "https://mcp.figma.com/mcp"` con OAuth (`oauth`/`oauthScopes`).

**Claude Code**:

```bash
# Server oficial remoto (OAuth por el cliente)
claude mcp add --transport http figma https://mcp.figma.com/mcp
# o Framelink con PAT
claude mcp add figma -e FIGMA_API_KEY=<PAT> -- npx -y figma-developer-mcp --stdio
```

**Cursor** — `.cursor/mcp.json`, misma estructura `mcpServers` que Kiro (sin `disabled`/`autoApprove`).

**VS Code / GitHub Copilot** — `.vscode/mcp.json`: la clave raíz es **`servers`** (no `mcpServers`), con `"type": "stdio" | "http"`; usar el bloque `inputs` para solicitar el token sin hardcodearlo.

El comando canónico de Framelink es `npx -y figma-developer-mcp --figma-api-key=<PAT> --stdio` (el flag y la env var son equivalentes; preferir la env var para no dejar el token en la línea de comandos).

## Qué extraer una vez conectado

- **Jerarquía de páginas/frames** y navegación → páginas candidatas para el plan de tests (`detect-pages-from-ui-source`).
- **Nombres de capas y componentes** → insumo para proponer los identificadores del `[[calidad-ui-locator-map-contract]]` (el nombre de capa NO es un selector: es la semilla del acuerdo con desarrollo).
- **Variables/estilos y screenshots** (server oficial: `get_variable_defs`, `get_screenshot`; ver la lista completa de tools en la doc oficial) → soporte para revisión de accesibilidad desde diseño y para baselines visuales tempranas.

## Restricciones

- **NUNCA** persistir el PAT en ningún archivo versionable ni en la evidencia; si el usuario lo pega en el chat, usarlo solo para la config local y recordarle rotarlo si quedó expuesto.
- **NUNCA** dar por leído un Figma sin haberlo consumido realmente (por MCP o REST): inferir pantallas "por el nombre del link" es inventar insumos.
- Si la conexión falla por permisos del archivo (no compartido con el usuario del token), reportar la causa exacta y pedir al usuario acceso al archivo — no degradar silenciosamente a user-story.
- Los detalles volátiles (URL del server remoto, precios post-beta, set de tools) pueden cambiar: ante discrepancia, la doc oficial (`developers.figma.com/docs/figma-mcp-server/`) manda sobre este asset.

## Cross-links

`[[calidad-playwright-greenfield]]` (reference `ui-source-priority.md`), `[[calidad-ui-locator-map-contract]]`, `[[calidad-accessibility-testing]]` (reference `design-review.md`), `[[calidad-sut-readiness-gate]]`, `[[calidad-generate-playwright-greenfield]]`.
