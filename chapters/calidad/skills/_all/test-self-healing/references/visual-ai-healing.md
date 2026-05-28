# Visual AI Healing

Estrategias de healing basadas en comparación visual de la UI: en lugar de depender del selector exacto, se compara el render contra un baseline y se decide si el cambio es regresión funcional o reflow tolerable.

## Herramientas

| Tool | Tipo | Modelo de comparación | Cuándo aplicar | Cuándo NO aplicar |
|---|---|---|---|---|
| Applitools Eyes | Comercial | Layout / Content / Strict (match levels) | UI con frecuentes reflows, suites visuales de regresión | Tests funcionales (lentitud + costo) |
| Percy (BrowserStack) | Comercial | DOM diff + visual diff | Sitios estáticos / marketing con muchos cambios cosméticos | Apps con animaciones intensas (genera ruido) |
| Resemble.js | OSS | Pixel diff configurable con threshold | Validar widgets aislados, fragmentos de UI | E2E completos (no escala bien) |

## Match levels de Applitools

- **Layout**: tolera cambios de texto, color, font; solo compara estructura. Ideal para suites multi-locale donde el copy cambia.
- **Content**: tolera reflow pero no cambios de texto. Para validar copy crítico.
- **Strict** (default): pixel-perfect con tolerancia mínima. Para regresión visual estricta de design system.

Elegir el match level es decisión arquitectónica: empieza con **Layout** para healing y reserva **Strict** para suites de regresión visual dedicadas (no healing).

## Cuándo aplicar visual AI

- Páginas con **re-renders frecuentes** donde los selectors estructurales son inestables (dashboards con widgets dinámicos, listas que se reordenan).
- **Apps móviles con cambios de OS** donde elementos del sistema (status bar, navigation gestures) cambian.
- **Design systems en evolución** donde el equipo de diseño hace ajustes cosméticos semanales.

## Cuándo NO aplicar

- **Tests funcionales puros** — la verificación funcional debe hacerse por assertion de estado, no por screenshot. Visual AI es complemento, no reemplazo.
- **Suites de alto volumen** (>500 casos) — el costo por screenshot se vuelve prohibitivo en comercial; en OSS la latencia degrada el tiempo de CI.
- **Tests de contract o security** — bloqueados por `over-healing-guardrails.md`.

## Snippet integración Applitools con Playwright

```typescript
import { test } from '@playwright/test';
import { Eyes, Target, Configuration, MatchLevel } from '@applitools/eyes-playwright';

test('login page visual healing', async ({ page }) => {
  const eyes = new Eyes();
  const cfg = new Configuration();
  cfg.setMatchLevel(MatchLevel.Layout); // healing-friendly
  eyes.setConfiguration(cfg);

  try {
    await eyes.open(page, 'Pragma App', 'login page baseline');
    await page.goto('https://app.example.com/login');
    await eyes.check('login form', Target.window().fully());
    await eyes.close();
  } catch (err) {
    console.log(JSON.stringify({
      event: 'healing',
      framework: 'playwright+applitools',
      type: 'visual_diff',
      test_id: 'login.visual',
      error: String(err),
    }));
    throw err;
  } finally {
    await eyes.abortIfNotClosed();
  }
});
```

## Reglas

- Visual AI **no reemplaza** la cadena de multi-locator; la complementa.
- Cualquier diff visual reportado por Applitools/Percy/Resemble debe pasar por revisión humana antes de marcarse como tolerable.
- El baseline visual versiona como cualquier otro artefacto del suite (`[[calidad-test-evidence-and-traceability]]`).
