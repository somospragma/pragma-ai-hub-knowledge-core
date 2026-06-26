
# Regresión visual

> Política transversal (cuándo, baselines, dinamismo, anti-patrones): `[[calidad-visual-regression]]`. Esta referencia cubre la implementación **Playwright (web)**.

## Reglas

- Solo Chromium. En `tests/visual.spec.ts` se hace skip explícito para los proyectos `firefox` y `webkit` para evitar baselines duplicados (las diferencias de render entre engines no se persiguen aquí).
- Los baselines se versionan en `tests/__screenshots__/{test-file}/{test-name}/{browser-name}/...`.
- En la primera corrida (o al introducir una nueva captura) se ejecuta `npx playwright test tests/visual.spec.ts --update-snapshots` y se commitean los PNG resultantes.
- Una captura por página priorizada (`CRITICAL`, `HIGH`).

## Snippet — `tests/visual.spec.ts`

```typescript
import { test, expect } from '@fixtures/base.fixture';

test.describe('Visual regression', () => {
  test.beforeEach(({}, testInfo) => {
    if (testInfo.project.name !== 'chromium') {
      test.skip();
    }
  });

  test('users list', async ({ page, usersPage, mockApi }) => {
    await usersPage.navigate();
    await expect(page).toHaveScreenshot('users-list.png');
  });

  test('users detail', async ({ page, usersPage, mockApi }) => {
    await usersPage.navigate('/users/1');
    await expect(page).toHaveScreenshot('users-detail.png');
  });
});
```

## Comandos

```bash
# Primera corrida (genera baselines)
npx playwright test tests/visual.spec.ts --update-snapshots

# Corrida normal (compara contra baselines)
npx playwright test tests/visual.spec.ts
```
