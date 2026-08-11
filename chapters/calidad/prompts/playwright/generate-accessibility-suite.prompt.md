---
id: calidad-playwright-generate-a11y-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [playwright]
description: Prompt que genera tests/accessibility.spec.ts con un test WCAG 2.1 AA por cada página priorizada (CRITICAL/HIGH).
tags: [playwright, prompt, accessibility, a11y, wcag, axe]
---

# Prompt — Generar suite de accesibilidad

## Variables

- `{{pages_critical_high}}` — Lista de páginas con `priority` `CRITICAL` o `HIGH`: `{ name, route, fixture }`.

## Instrucción para el LLM

Genera UN solo archivo `tests/accessibility.spec.ts` siguiendo estrictamente [[calidad-playwright-greenfield]] (consultar `references/accessibility-axe-wcag.md` en su subfolder):

- Importa `test` y `expect` desde `@fixtures/base.fixture`.
- Importa `injectAxe` y `checkA11y` desde `axe-playwright`.
- Un `test.describe('Accessibility — WCAG 2.1 AA', ...)` que agrupa todos los tests.
- Un `test(...)` por cada página en `{{pages_critical_high}}`.
- Cada test: navega a la página (vía su fixture: `usersPage`, `ordersPage`, etc.), inyecta axe y ejecuta `checkA11y` con tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`.
- Incluye siempre el fixture `mockApi` en la firma para activar los mocks.

NO incluyas páginas con prioridad `MEDIUM` o `LOW`.

## Snippet de salida esperado

```typescript
import { test, expect } from '@fixtures/base.fixture';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility — WCAG 2.1 AA', () => {
  test('login page', async ({ page, loginPage, mockApi }) => {
    await loginPage.navigate();
    await injectAxe(page);
    await checkA11y(page, undefined, {
      detailedReport: true,
      detailedReportOptions: { html: true },
      axeOptions: {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      },
    });
  });

  test('users list', async ({ page, usersPage, mockApi }) => {
    await usersPage.navigate();
    await injectAxe(page);
    await checkA11y(page, undefined, {
      axeOptions: {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      },
    });
  });

  test('product detail', async ({ page, productsPage, mockApi }) => {
    await productsPage.navigate('/products/1');
    await injectAxe(page);
    await checkA11y(page, undefined, {
      axeOptions: {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      },
    });
  });
});
```
