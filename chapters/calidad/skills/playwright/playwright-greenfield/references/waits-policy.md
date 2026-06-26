# Política de waits en Playwright

Los tests E2E son tan flaky como su peor wait. Esta política es de cumplimiento obligatorio en greenfield y brownfield.

## Prohibido

### 1. `page.waitForTimeout(ms)` — siempre

Razones:
- Los timeouts fijos son arbitrarios: o son demasiado cortos (flake) o demasiado largos (CI lento).
- Ocultan el evento real que se está esperando, lo que rompe la trazabilidad cuando un test falla.

El proyecto incluye una regla ESLint que falla el lint si encuentra `.waitForTimeout(` en cualquier archivo. La regla ya está inyectada en `templates/package.json.tpl` bajo `eslintConfig.rules.no-restricted-syntax`.

### 2. `page.waitForLoadState('networkidle')` en SPAs con WebSockets o long-polling

Aplicaciones como Instaleap, Firebase Realtime Database, Pusher, Pub/Sub, Apollo subscriptions, o cualquier SPA con telemetría push **nunca llegan** a `networkidle`. El test colgará 30 s y romperá por timeout sin razón aparente.

`networkidle` solo es aceptable en sitios estáticos sin sockets abiertos. En caso de duda, asumir que **no** es aceptable.

## Alternativas obligatorias

### Esperar una respuesta de API específica

```typescript
const responsePromise = page.waitForResponse(
  (resp) => resp.url().includes('/api/orders') && resp.status() === 200
);
await page.getByRole('button', { name: 'Create order' }).click();
const response = await responsePromise;
const order = await response.json();
expect(order.id).toBeDefined();
```

### Esperar a que un elemento sea visible/oculto

```typescript
await page.getByRole('dialog', { name: 'Order created' })
  .waitFor({ state: 'visible', timeout: 10_000 });
```

### Esperar a que un valor de texto cambie

```typescript
const status = page.getByTestId('order-status');
const previous = await status.textContent();
await page.getByRole('button', { name: 'Submit' }).click();
await expect(status).not.toHaveText(previous ?? '');
```

### Esperar a que termine una transición CSS / debounce / animación

Usar el estado al que la animación lleva, no el reloj:

```typescript
await page.getByTestId('side-panel').waitFor({ state: 'visible' });
await expect(page.getByTestId('side-panel')).toHaveCSS('opacity', '1');
```

## Antes / después

### Antes (prohibido)

```typescript
await page.getByRole('button', { name: 'Search' }).click();
await page.waitForTimeout(3000);                           // arbitrary
await page.waitForLoadState('networkidle');                // bloquea en SPAs
const results = await page.locator('.result').count();
```

### Después (correcto)

```typescript
const responsePromise = page.waitForResponse('**/api/search**');
await page.getByRole('button', { name: 'Search' }).click();
await responsePromise;
await page.getByRole('list', { name: /results/i })
  .waitFor({ state: 'visible' });
const results = await page.getByRole('listitem').count();
```

## Cross-links

- `[[playwright-greenfield/references/templates/package.json.tpl]]` — la regla ESLint vive aquí.
- ``coherence-checks.md`` — auditoría de coherencia.
- `[[calidad-post-generation-protocol]]` — la corrida de lint forma parte del post-protocolo.
