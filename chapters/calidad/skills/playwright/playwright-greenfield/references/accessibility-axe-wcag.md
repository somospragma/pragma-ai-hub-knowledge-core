
# Accesibilidad — WCAG 2.1 AA

## Stack

- Dependencia: `@axe-core/playwright` `^4.9.0` (peer de `axe-playwright`).
- Cobertura por defecto: WCAG 2.1 Level AA.
- Tipos de hallazgo que detecta axe en este flujo: missing alt text en imágenes, ARIA roles inválidos o mal aplicados, contraste de color insuficiente, label sin input asociado, jerarquía de headings rota.

## Snippet — `tests/accessibility.spec.ts`

```typescript
import { test, expect } from '@fixtures/base.fixture';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility — WCAG 2.1 AA', () => {
  test('users list', async ({ page, usersPage, mockApi }) => {
    await usersPage.navigate();
    await injectAxe(page);
    await checkA11y(page, undefined, {
      detailedReport: true,
      detailedReportOptions: { html: true },
      axeOptions: {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      },
    });
  });

  test('users detail', async ({ page, usersPage, mockApi }) => {
    await usersPage.navigate('/users/1');
    await injectAxe(page);
    await checkA11y(page);
  });
});
```

## Notas

- Una suite por página priorizada (`CRITICAL` y `HIGH`).
- Las violaciones se reportan inline en consola; el test falla si hay al menos una violación de severidad `serious` o `critical`.
- Para excluir un nodo conocido y aceptado, usa `checkA11y(page, undefined, { exclude: ['#legacy-widget'] })`.
