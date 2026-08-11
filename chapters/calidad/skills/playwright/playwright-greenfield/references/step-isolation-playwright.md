# Step Isolation — Playwright

Implementación del patrón universal `[[calidad-step-isolation-pattern]]` en Playwright. El mecanismo nativo es `test.beforeEach`/`test.afterEach` para aislar setup/cleanup + tags por step para filtrar reportes.

## Mecanismo

- **Setup**: `test.beforeEach` ejecuta antes de cada test del describe. Aquí va la navegación inicial, restore de `storageState`, sembrado de datos. NO contiene aserciones del contrato.
- **Auth**: cuando aplica, se delega a `auth.setup.ts` + `storageState` (no a un step inline). El proyecto Playwright trata auth como dependencia, no como step a medir.
- **Main**: el cuerpo del `test('...')` contiene aserciones del contrato funcional. Tag `@main-step`.
- **Cleanup**: `test.afterEach` para teardown (limpiar datos sembrados, cerrar sesiones). Tag `@cleanup-step` si se modela como test separado.

## Snippet

```typescript
import { test, expect } from '@playwright/test';

test.describe('Transactions list', { tag: ['@HU-101'] }, () => {

  test.beforeEach(async ({ page }) => {
    // setup compartido — NO valida contrato
    await page.goto('/transactions');
    await expect(page.getByRole('heading', { name: 'Transacciones' })).toBeVisible();
  });

  test('list shows expected page size and money format',
    { tag: ['@happy-path', '@main-step'] },
    async ({ page }) => {
      // main — codifica el contrato funcional
      const rows = page.getByRole('row');
      await expect(rows).toHaveCount(20);
      await expect(rows.first().getByText(/^\$[\d,]+\.\d{2}$/)).toBeVisible();
      await expect(page.getByText(/Página \d+ de \d+/)).toBeVisible();
    },
  );

  test('pagination navigates and updates rows',
    { tag: ['@navigation', '@main-step'] },
    async ({ page }) => {
      await page.getByRole('button', { name: 'Siguiente' }).click();
      await expect(page.getByText(/Página 2 de \d+/)).toBeVisible();
    },
  );

  test.afterEach(async ({ page }, testInfo) => {
    // cleanup — opcional para el veredicto; warning si falla
    if (testInfo.status === 'failed') {
      await page.screenshot({ path: `screenshots/${testInfo.title}.png` });
    }
  });
});
```

## Reglas Playwright-específicas

- `auth.setup.ts` + `storageState` NO es un step de test — es una dependencia previa que Playwright resuelve en el project `setup`. Las assertions de login viven ahí y NO contaminan las métricas del main.
- Cada `test()` declara tags nativos v1.42+ (ver `[playwright-native-tags-v142](./playwright-native-tags-v142.md)`). Convención obligatoria: `@main-step` para los que codifican contrato; cualquier otro (ej. `@cleanup-step`) NO cuenta para `effective_minimum`.
- Filtrado: `npx playwright test --grep @main-step` corre sólo el flujo principal. Útil para smoke gates donde no se quiere ejecutar cleanups largos.
- `test.beforeEach` falla → el test fallido se reporta como `failed`, pero el reporter custom debe separar "fallo en setup" de "fallo en main" en el `metadata.json` (ver `[metadata-emitter-playwright](./metadata-emitter-playwright.md)`).
- La fórmula de cobertura `[coverage-formula](./coverage-formula.md)` cuenta SOLO `@main-step`. Setups y cleanups NO inflan el `effective_minimum`.

## Cross-links

`[[calidad-step-isolation-pattern]]`, `[playwright-native-tags-v142](./playwright-native-tags-v142.md)`, `[coverage-formula](./coverage-formula.md)`, `[auth-storage-state](./auth-storage-state.md)`, `[metadata-emitter-playwright](./metadata-emitter-playwright.md)`, `[[calidad-playwright-greenfield]]`.
