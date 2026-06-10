# Tags nativos Playwright v1.42+

Desde Playwright 1.42 los tags se declaran nativamente como segundo argumento de `test()` y `test.describe()`. Esto sustituye el patrón legacy de incrustar `@smoke` en el título del describe, y habilita filtrado por `--tag` en CLI con trazabilidad HU→test automática.

## Migración

### Antes (legacy, NO usar en código nuevo)

```typescript
test.describe('@smoke @HU-01 Catalog page', () => {
  test('user can search by name', async ({ page }) => {
    // ...
  });
});
```

Filtrado: `npx playwright test --grep "@smoke"`. Aún funciona, pero los tags están enterrados en el string del título.

### Después (obligatorio en código nuevo)

```typescript
test('user can search by name',
  { tag: ['@smoke', '@HU-01'] },
  async ({ page }) => {
    // ...
  }
);

test.describe('Catalog page', () => {
  test('user can search by SKU',
    { tag: ['@regression', '@HU-01'] },
    async ({ page }) => {
      // ...
    }
  );
});
```

Filtrado: `npx playwright test --tag @smoke` (flag dedicado, no grep) o `--grep @smoke` (sigue funcionando).

## Reglas por test

Cada test debe declarar exactamente dos categorías de tags:

1. **Tag de suite** — uno y solo uno de: `@smoke`, `@regression`, `@security`, `@a11y`, `@visual`, `@perf`.
2. **Tag de HU** — uno y solo uno con la convención `@HU-<id>`, donde `<id>` corresponde a la HU declarada en `.evidence/coverage-declared.json` (ver `[[playwright-greenfield/references/coverage-formula.md]]`).

Tags opcionales (no excluyentes con los anteriores):

- `@live` / `@mocked` / `@hybrid` — modo de ejecución; ver `[[playwright-greenfield/references/execution-modes-live-mocked-hybrid.md]]`.
- `@critical` / `@high` / `@medium` / `@low` — espejo del `risk_factor`.

## Filtrado en CLI

```bash
npx playwright test --tag @smoke               # solo smoke
npx playwright test --tag @HU-01               # solo HU-01
npx playwright test --tag "@smoke&@HU-01"      # ambos
npx playwright test --tag "@smoke|@regression" # cualquiera
npx playwright test --tag "!@security"         # excluir security
```

## Trazabilidad automática

Como cada test lleva su tag `@HU-XX`, la trazabilidad HU→test es greppable:

```bash
grep -r "tag:.*@HU-01" tests/ --include="*.ts" | wc -l
```

Este número debe coincidir con `effective_minimum` declarado para esa HU. Si no coincide → o falta cobertura, o sobra un test mal etiquetado.

## Cross-links

- Cobertura por HU: `[[playwright-greenfield/references/coverage-formula.md]]`.
- Modos `@live` / `@mocked` / `@hybrid`: `[[playwright-greenfield/references/execution-modes-live-mocked-hybrid.md]]`.
- Coherencia y data-driven (uso de `for...of` con tags por iteración): `[[playwright-greenfield/references/coherence-checks.md]]`.
- Documentación oficial: Playwright Release Notes 1.42, sección "Tagging tests".
