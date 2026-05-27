
# Fuentes válidas de información para Playwright

Playwright valida la capa de presentación. Por eso el insumo principal debe describir UI real, no contrato backend. Esta referencia documenta las 5 fuentes aceptadas, cuándo usar cada una y qué profundidad de extracción esperar.

## Las 5 fuentes (en orden de preferencia)

1. **URL de aplicación viva** — la app está accesible (dev/staging/prod) y autenticable.
2. **Figma / wireframes / mockups UI** — diseños con jerarquía de páginas y componentes.
3. **User stories con flujos UI explícitos** — historias que enumeran páginas, acciones y transiciones.
4. **Storybook / sistema de diseño existente** — componentes catalogados con sus rutas demo.
5. **OpenAPI / Swagger** — SOLO como insumo opcional para generar mocks aislados (`@mocked`). **NUNCA** como fuente de páginas.

## Árbol de decisión

```
¿La app está corriendo en algún ambiente?
├── Sí → URL viva. Usa Playwright Codegen o MCP browser tools (preferido).
└── No → ¿Existe Figma / mockup con rutas?
        ├── Sí → Figma. Selectores serán inferidos y deberán validarse contra DOM real luego.
        └── No → ¿Hay user story con flujos UI explícitos (no solo reglas backend)?
                ├── Sí → User story. Mismo caveat de Figma para selectores.
                └── No → ¿Hay Storybook publicado?
                        ├── Sí → Storybook. Cobertura limitada a componentes catalogados.
                        └── No → DETENTE. Solicita al usuario una fuente UI real.
                                  OpenAPI solo no alcanza para generar Playwright.
```

## Profundidad de extracción esperada por fuente

| Fuente            | Rutas frontend | Selectores reales | Form fields | Navegación | Esfuerzo / fricción |
|-------------------|----------------|-------------------|-------------|------------|---------------------|
| URL viva          | Exactas        | Sí (codegen/MCP)  | Sí          | Sí         | Bajo                |
| Figma             | Anotadas       | Inferidos         | Sí (visual) | Sí         | Medio               |
| User story        | Texto          | Inferidos         | Parcial     | Texto      | Medio-alto          |
| Storybook         | Por componente | Sí (story DOM)    | Parcial     | Limitada   | Medio               |
| OpenAPI (mocks)   | NO aplica      | NO aplica         | NO aplica   | NO aplica  | N/A — no es UI      |

## Herramientas recomendadas por fuente

- **URL viva** → `npx playwright codegen URL`, MCP browser tools (`browser_navigate`, `browser_snapshot`), o crawlers headless. Skill: `[[playwright-from-live-app]]`.
- **Figma** → plugin oficial de Figma para exportar specs; OCR sobre screenshots si solo hay imagen.
- **User story** → leer en voz alta el flujo y mapearlo a páginas; pedir al PO los flujos faltantes.
- **Storybook** → `npm run storybook` y crawlear `iframe.html?id=...` con Playwright.
- **OpenAPI** → opcional para `[[playwright-generate-mock-handlers-prompt]]`; nunca para inferir páginas.

## Comparativa rápida — accuracy vs effort

| Fuente            | Accuracy de selectores | Effort de extracción | Cuándo elegirla                                       |
|-------------------|------------------------|----------------------|-------------------------------------------------------|
| URL viva          | Alta                   | Bajo                 | Por defecto si está disponible                        |
| Storybook         | Alta (acotada)         | Bajo-medio           | Hay design system maduro y la app está poco accesible |
| Figma             | Media (inferidos)      | Medio                | App no existe aún (pre-dev) pero hay diseño aprobado  |
| User story        | Baja (texto)           | Alto                 | Solo si no hay nada mejor; pedir validación luego     |
| OpenAPI           | N/A                    | N/A                  | Nunca como fuente UI                                  |

## Regla operacional

Si llegas a este skill y el único insumo es OpenAPI/Swagger, **detente** y aplica `[[calidad-mandatory-inputs-protocol]]` para solicitar una fuente UI válida. No procedas a inferir páginas desde paths backend; ese fue precisamente el bug histórico que esta refactorización corrige.
