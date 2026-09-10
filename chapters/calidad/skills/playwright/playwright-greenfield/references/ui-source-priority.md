
# Fuentes válidas de información para Playwright

> El contrato general de las fuentes de interfaz —qué es cada una, qué se espera de
> ella, qué **no** puede dar, y la procedencia y confianza de lo que se extrae— vive en
> `[[calidad-ui-source-contract]]`, que aplica igual a web y a móvil. Aquí queda lo
> específico de Playwright: el árbol de decisión, la profundidad de extracción por
> fuente y el enganche con el mapa de locators.

Playwright valida la capa de presentación. El insumo debe describir UI real. Esta referencia documenta las 4 fuentes aceptadas, cuándo usar cada una y qué profundidad de extracción esperar.

## Las fuentes (en orden de preferencia)

1. **URL de aplicación viva** — la app está accesible (dev/staging/prod) y autenticable.
2. **Prototipo interactivo de diseño** (export navegable de Figma Make / design capture / Framer, demo del design system) — **se recorre como una app**: da textos exactos, datos, formatos, estados y grafo de navegación. Muy superior al Figma estático; ver `[interactive-design-prototype-source](interactive-design-prototype-source.md)`.
3. **Figma / wireframes / mockups UI** — diseños con jerarquía de páginas y componentes.
4. **User stories con flujos UI explícitos** — historias que enumeran páginas, acciones y transiciones.
5. **Storybook / sistema de diseño existente** — componentes catalogados con sus rutas demo.

## Dos preguntas distintas, dos jerarquías

La lista de arriba responde bien a **"¿qué pantallas hay y cómo se navega?"**. Responde mal a la otra pregunta, que es de la que dependen los selectores: **"¿qué árbol publica este elemento?"**. Mezclarlas es lo que produce selectores inventados que pasan en el prototipo y se rompen el día del despliegue.

| Pregunta | Jerarquía de fuentes |
|---|---|
| **Flujo y navegación** — qué pantallas hay, cómo se llega | app viva > prototipo interactivo > Figma > historia de usuario > Storybook |
| **Estructura de un elemento** — qué árbol publica, qué rol, qué anidamiento | app viva > **design system / Storybook** > **repositorio de front** > Figma |

Para la segunda, **el Figma es de las peores fuentes**: muestra píxeles y no dice nada del árbol. Y el design system pasa de último a primero, porque lo que el driver ve lo decide la implementación del componente, no el diseño visual.

Verificado en campo, tres costes que salieron de confundir las dos jerarquías, y los tres eran detalle de componente: cada casilla de un grid de código de un solo uso tenía **dos campos anidados** y había que escribir en el interno; una opción de menú era texto estático y no botón; y un ícono de alternancia era un gráfico sin etiqueta accesible, localizable sólo por geometría. Ninguno se ve en un diseño; los tres estaban en el componente.

### Design system y repositorio de front

Dos fuentes que no estaban en la lista de arriba y que son de primer nivel para la estructura:

- **Design system** — si el prototipo se construye con el mismo paquete que usa la app, publica la misma semántica por construcción. El prototipo **fija la misma versión** que publica la app; si derivan, vuelve la deriva por otra puerta. Se toma **como dependencia del proyecto generador**, nunca leyendo su código con el modelo.
- **Repositorio de front** — para lo ya construido: identificadores declarados, componente de cada uno, grafo de rutas y puntos de llamada a servicios. Con dos límites que no se difuminan: se extrae **estructura, nunca comportamiento esperado** —derivar las aserciones del código es probar la implementación contra sí misma, y es anti-cheating—, y se extrae **con herramienta, por diferencias**, nunca leyendo el repositorio con el modelo. Ver `[[calidad-pre-development-artifacts-continuity]]`.

## Árbol de decisión

```
¿La app está corriendo en algún ambiente?
├── Sí → URL viva. Usa Playwright Codegen o MCP browser tools (preferido).
└── No → ¿Hay un prototipo interactivo navegable del diseño?
        ├── Sí → RECÓRRELO headless y extrae textos/datos/formato/navegación
        │        (interactive-design-prototype-source.md) + LOCATOR MAP obligatorio.
        └── No → ¿Existe Figma / mockup con rutas?
        ├── Sí → Figma + LOCATOR MAP obligatorio (ver abajo).
        └── No → ¿Hay user story con flujos UI explícitos?
                ├── Sí → User story + LOCATOR MAP obligatorio. Mismo caveat de Figma.
                └── No → ¿Hay Storybook publicado?
                        ├── Sí → Storybook. Cobertura limitada a componentes catalogados.
                        └── No → DETENTE. Solicita al usuario una fuente UI real.
```

## Pre-desarrollo: fuente inferida exige locator map

Cuando la fuente es Figma o user story porque la app **aún no existe** (`execution_target: mock` en `[[calidad-sut-readiness-gate]]`), inferir selectores no basta: la suite fallaría el día que llegue el desarrollo por drift de identificadores. En ese modo es **obligatorio** el contrato de mapeo `[[calidad-ui-locator-map-contract]]`: un `locator-map.json` acordado con el equipo de desarrollo del que salen TODOS los selectores (`getByTestId`), con validación de drift contra el DOM real antes de la primera corrida live. Sin locator map + Figma, la construcción pre-desarrollo se detiene (STOP del gate).

## Profundidad de extracción esperada por fuente

| Fuente            | Rutas frontend | Selectores reales | Form fields | Navegación | Esfuerzo / fricción |
|-------------------|----------------|-------------------|-------------|------------|---------------------|
| URL viva          | Exactas        | Sí (codegen/MCP)  | Sí          | Sí         | Bajo                |
| Figma             | Anotadas       | Inferidos         | Sí (visual) | Sí         | Medio               |
| User story        | Texto          | Inferidos         | Parcial     | Texto      | Medio-alto          |
| Storybook         | Por componente | Sí (story DOM)    | Parcial     | Limitada   | Medio               |

## Herramientas recomendadas por fuente

- **URL viva** → `npx playwright codegen URL`, MCP browser tools (`browser_navigate`, `browser_snapshot`), o crawlers headless. Skill: `[[calidad-playwright-from-live-app]]`.
- **Figma** → conexión vía MCP (server oficial remoto o Framelink con PAT) según `[[calidad-figma-mcp-integration]]`. **Un link "público" de Figma NO es consumible sin esa conexión autenticada** — si el usuario entrega solo el link, guiar el setup del MCP (el skill incluye el flujo y los snippets por IDE) y luego continuar. Export estático (imágenes/PDF) solo como último recurso.
- **User story** → leer en voz alta el flujo y mapearlo a páginas; pedir al PO los flujos faltantes.
- **Storybook** → `npm run storybook` y crawlear `iframe.html?id=...` con Playwright.

## Comparativa rápida — accuracy vs effort

| Fuente            | Accuracy de selectores | Effort de extracción | Cuándo elegirla                                       |
|-------------------|------------------------|----------------------|-------------------------------------------------------|
| URL viva          | Alta                   | Bajo                 | Por defecto si está disponible                        |
| Storybook         | Alta (acotada)         | Bajo-medio           | Hay design system maduro y la app está poco accesible |
| Figma             | Media (inferidos)      | Medio                | App no existe aún (pre-dev) pero hay diseño aprobado  |
| User story        | Baja (texto)           | Alto                 | Solo si no hay nada mejor; pedir validación luego     |

## Especificaciones backend

Specs como OpenAPI/Swagger/WSDL describen contrato backend, no UI: no aplican aquí. Si el usuario solo trae un spec backend y su intención es validar el contrato, deriva a `[[calidad-karate-greenfield]]` (funcional) o `[[calidad-k6-greenfield]]` (performance). Para mocks dentro de un proyecto Playwright (modo `@mocked` o `@hybrid`), las fuentes de `mock_endpoints` se documentan en `[mocks-page-route](mocks-page-route.md)`.
