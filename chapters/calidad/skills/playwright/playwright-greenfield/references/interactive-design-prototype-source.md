
# Prototipo interactivo de diseño como fuente UI de primera clase

## Qué es y por qué vale más que un Figma estático

Cada vez es más común que el diseño llegue como un **prototipo navegable**: un export HTML/JS de Figma Make, "design capture", Framer, Storybook o un demo del design system. No es una imagen: es una app de mentira **con textos, datos, estados y navegación reales**, y se puede *ejecutar*.

Un Figma estático da jerarquía y aspecto. Un prototipo interactivo da además:

| Qué extraer | Para qué sirve |
|---|---|
| **Catálogo de textos exactos** (todas las pantallas) | Contrato de textos: selectores por texto, aserciones de mensajes, i18n. Se copia carácter a carácter |
| **Modelo de datos** (saldos, montos, nombres, estados) | Datos del prototipo/mock que deben coincidir con la HU; detecta incoherencias antes de codificar |
| **Formato de presentación** (moneda, fechas, separadores) | Evita la saga de normalización en aserciones (`"$180.000"` vs `"180.000 $"`) |
| **Grafo de navegación** (qué botón lleva a qué pantalla) | Orden de pantallas, transiciones y pasos intermedios que los tests deben ejecutar |
| **Estados por pantalla** (vacío, error, carga, éxito) | Escenarios negativos y de borde que la HU quizá no enumera |
| **Screenshots por pantalla** | Baseline de fidelidad para el gate de aceptación del prototipo |

En campo, un prototipo interactivo entregado como insumo contenía la respuesta a **cinco de los diecinueve problemas** que costaron una PoC completa (montos, formato de moneda, pantalla multiproducto y dos transiciones de navegación). Se abrió una vez, superficialmente, y no se volvió a mirar.

## Cómo se explota (no se "mira": se recorre)

1. **Servirlo y abrirlo headless** — es una página: `npx serve <carpeta>` y navegarlo con Playwright/browser MCP. Es la misma técnica de `[[calidad-playwright-from-live-app]]`, aplicada al prototipo en vez de a la app.
2. **Recorrer todas las pantallas y estados**, incluidos los selectores de escenario que el prototipo ofrezca (p. ej. "Todo al día" / "Con mora"): cada uno es un conjunto de datos distinto.
3. **Extraer y persistir** en `.evidence/design-extract.json`: textos por pantalla, datos, formatos, grafo de navegación y rutas. Screenshots a `.evidence/design-baseline/`.
4. **Si no se puede ejecutar** (sin navegador disponible), leer el fuente: el HTML/JS contiene los literales de texto y los objetos de datos. Es menos cómodo, pero sigue siendo la fuente de verdad — no una excusa para inferir.
5. **Volver a él durante el trabajo**: ante cualquier duda de texto, monto, formato o navegación, manda el prototipo, no la memoria ni la inferencia.

## Reglas

- Un prototipo interactivo entregado como insumo **se explota o se declara por qué no** (`[[calidad-mandatory-inputs-protocol]]`, tabla de extracción). Ignorarlo es blocker.
- **No sustituye al locator map**: el prototipo da textos y flujo; los identificadores de automatización siguen siendo el contrato con desarrollo (`[[calidad-ui-locator-map-contract]]`). Si el prototipo trae identificadores útiles, se proponen como semilla del mapa, no como sustituto.
- **No es el SUT**: es diseño ejecutable. No se automatiza contra él salvo que se haya adoptado explícitamente como prototipo de front (ver `front-prototype-recipe.md`).
- Cuando además se construye un prototipo propio (front o app), este extract es su **especificación y su baseline**: el gate de aceptación compara contra él.

## Cross-links

`ui-source-priority.md` (dónde encaja en el orden de fuentes), `front-prototype-recipe.md`, `[[calidad-playwright-from-live-app]]`, `[[calidad-ui-locator-map-contract]]`, `[[calidad-appium-screenplay-android]]` (consultar `references/flutter-apps-and-prototype.md` para el gate de aceptación del prototipo mobile).
