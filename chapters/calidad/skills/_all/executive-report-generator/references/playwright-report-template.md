# Plantilla específica de Playwright para el reporte ejecutivo

Esta plantilla guía las secciones del reporte ejecutivo cuando `framework = playwright`. Complementa `report-structure.md`. Se invoca desde el Paso 6 del `SKILL.md`.

## Fuentes primarias

- `playwright-report/results.json` (o el path equivalente bajo `results/playwright/<timestamp>/`).
- `test-results/` con traces, screenshots, videos por test fallido.
- Resultados de `tests/visual.spec.ts` (snapshots diff) y `tests/accessibility.spec.ts` (axe findings).
- `metadata.json` de la corrida.

## Sección 2 — Cumplimiento de SLAs (vista Playwright)

Mapear desde `STRATEGY.md`:

- Cumplimiento por HU: pasados / totales por `@user-story:HUT-XXX`.
- Cobertura mínima por página (`effective_minimum = happy + 2_boundary + 2_negative + 1_edge` mínimo 8).
- A11y: WCAG 2.1 AA sin findings `critical` ni `serious` (regla por defecto).
- Performance browser si fue declarado: page load < N ms, TTI < N ms.

## Sección 3 — Resultados por HU y por página

Tabla principal por HU:

| HU | Páginas asociadas | Total tests | Pasados | Fallidos | % éxito | Visual diffs | A11y findings |
|---|---|---|---|---|---|---|---|
| HUT-001 | LoginPage, DashboardPage | 12 | 12 | 0 | 100% | 0 | 0 |
| HUT-002 | CheckoutPage | 8 | 6 | 2 | 75% | 1 | 2 (serious) |

### Sub-tabla: visual diffs significativos

Solo listar diffs superiores al threshold configurado en `playwright.config.ts` (default `maxDiffPixelRatio`):

| Test | Página | Snapshot esperado | Snapshot actual | Delta px ratio | Justificación |
|---|---|---|---|---|---|
| visual.spec.ts > checkout layout | CheckoutPage | checkout.png | checkout-actual.png | 4.2% | a determinar |

### Sub-tabla: a11y findings por severidad

| Severidad | Cantidad | Páginas afectadas |
|---|---|---|
| critical | 0 | (ninguna) |
| serious | 2 | CheckoutPage |
| moderate | 5 | DashboardPage, ProfilePage |
| minor | 11 | varias |

Los `critical` y `serious` son bloqueadores. Los `moderate` y `minor` se reportan como observaciones.

### Sub-tabla: performance browser (si fue medido)

| Página | Page load p95 | TTI p95 | Cumple SLA |
|---|---|---|---|
| LoginPage | 1.2 s | 1.8 s | OK |
| CheckoutPage | 3.4 s | 4.1 s | FAIL |

## Sección 4 — Comparación entre corridas (vista Playwright)

| HU | Corrida anterior | Corrida actual | Delta | Visual diffs nuevos | Tests recuperados | Tests regresionados |
|---|---|---|---|---|---|---|
| HUT-001 | 10/12 | 12/12 | +2 | 0 | login_with_2fa, login_with_remember_me | (ninguno) |
| HUT-002 | 7/8 | 6/8 | -1 | 1 | (ninguno) | checkout_express_path |

## Sección 7 — Anexos específicos Playwright

- Comando exacto (`npx playwright test --project=live-chromium`, etc.) y `mock_mode` aplicado.
- Path al reporte HTML nativo: `playwright-report/index.html`.
- Listado de traces relevantes (solo fallidos): `test-results/*/trace.zip`.
- Versión de `@playwright/test`, navegadores instalados.
- Browsers ejecutados (chromium / firefox / webkit) y projects activos.
