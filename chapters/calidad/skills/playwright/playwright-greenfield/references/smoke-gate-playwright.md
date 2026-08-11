# Smoke Gate (Playwright) — `npx playwright test --grep @smoke`

Implementación Playwright de la política universal `[[calidad-smoke-gate-policy]]`. Antes de declarar `status: success`, el agente DEBE correr al menos un test taggeado `@smoke` en el project `chromium-live` y validar exit code 0.

## Comando canónico

```bash
npx playwright test \
  --grep @smoke \
  --project=chromium-live \
  --workers=1 \
  --max-failures=1 \
  --reporter=json,list
```

Notas:

- `--grep @smoke` filtra tests cuyo título (describe/test) contiene la subcadena `@smoke` (convención native tags v1.42+; ver `[playwright-native-tags-v142](./playwright-native-tags-v142.md)`).
- `--project=chromium-live` fuerza navegador único + project `live` con `storageState` real. Smoke nunca corre en `mocked` (un mocked verde no prueba el scaffold end-to-end).
- `--workers=1` evita race conditions iniciales del smoke contra ambientes con rate-limit bajo.
- `--max-failures=1` aborta tras el primer fallo (no malgastes minutos de CI re-corriendo si el scaffold está roto).
- `--reporter=json,list` produce JSON parseable + output amigable en stdout.

> Si el `project` canónico tiene otro nombre (ej. `live-chromium` en `playwright.config.ts`), usar ese identificador. El requisito es que sea el project `live` con `chromium`.

## Asegurar al menos un test `@smoke`

El agente DEBE garantizar al menos un `test('... @smoke', ...)` en la suite que represente un happy path end-to-end (login básico, navegación a home, render de una vista crítica). Convención:

```typescript
test('navega a home y muestra título @smoke @live', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle(/MyApp/);
});
```

El tag `@smoke` va en el título del test (no en el archivo) para que `--grep` lo encuentre. Si la suite no contiene ningún `@smoke`, reportar `smoke_gate_missing_scenario_playwright`.

## Parsing del JSON reporter

Configurar JSON reporter en `playwright.config.ts`:

```typescript
reporter: [
  ['html', { open: 'never', outputFolder: 'results/playwright/html' }],
  ['json', { outputFile: 'results/playwright/last-run.json' }],
  ['list'],
],
```

Tras correr el smoke:

```bash
EXIT=$?
if [ $EXIT -ne 0 ]; then
  echo "smoke_gate_failed_playwright exit=$EXIT" >&2
  exit $EXIT
fi

UNEXPECTED=$(jq '.stats.unexpected // 0' results/playwright/last-run.json)
if [ "$UNEXPECTED" != "0" ]; then
  echo "smoke_gate_failed_playwright unexpected=$UNEXPECTED" >&2
  exit 1
fi
```

Si `stats.expected` es 0 (no matcheó nada), reportar `smoke_gate_missing_scenario_playwright`.

## Wiring con delivery_gate

```yaml
smoke_gate:
  framework: playwright
  command: "npx playwright test --grep @smoke --project=chromium-live --workers=1 --max-failures=1"
  executed: true
  exit_code: 0
  duration_seconds: 8
```

## Cross-links

`[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-smoke-gate-policy]]`, `[playwright-native-tags-v142](./playwright-native-tags-v142.md)`.
