# Metadata Emitter — Playwright

Playwright expone una interfaz `Reporter` que permite escribir reporters personalizados invocados durante la corrida. El metadata emitter es un reporter TS que en `onEnd` produce el `{ISO}-metadata.json` universal definido en `[execution-metadata-schema](../../../_all/execution-metadata-schema.md)`.

## Mecanismo

1. Crear `metadata-reporter.ts` en la raíz del proyecto.
2. Implementar `Reporter` con `onTestEnd` (acumular totales) y `onEnd` (escribir el JSON).
3. Wire-up en `playwright.config.ts` como reporter adicional al `html`/`json` existentes.

## `metadata-reporter.ts`

```typescript
import type { Reporter, TestCase, TestResult, FullResult } from '@playwright/test/reporter';
import * as fs from 'fs';
import * as path from 'path';

export default class MetadataReporter implements Reporter {
  private started_at = new Date().toISOString();
  private totals = { total: 0, passed: 0, failed: 0, skipped: 0 };

  onTestEnd(_test: TestCase, result: TestResult): void {
    this.totals.total += 1;
    if (result.status === 'passed') this.totals.passed += 1;
    else if (result.status === 'failed' || result.status === 'timedOut') this.totals.failed += 1;
    else if (result.status === 'skipped') this.totals.skipped += 1;
  }

  onEnd(result: FullResult): void {
    const finished_at = new Date().toISOString();
    const ts = finished_at.replace(/[:.]/g, '-');
    const date = ts.split('T')[0];
    const base = `results/playwright/${date}`;
    fs.mkdirSync(base, { recursive: true });

    const metadata = {
      scenario_or_feature: process.env.SCENARIO_NAME || 'all',
      framework: 'playwright',
      version: 'v1',
      environment: process.env.ENV || 'staging',
      workload_or_scope: `${this.totals.total} tests`,
      sut_endpoint_or_url: process.env.BASE_URL || process.env.BACKEND_URL || '',
      auth_strategy: process.env.AUTH_STRATEGY || 'storageState',
      exit_code: result.status === 'passed' ? 0 : 1,
      started_at: this.started_at,
      finished_at,
      totals: this.totals,
      thresholds_or_coverage_met: result.status === 'passed',
      blockers: [] as string[],
    };

    fs.writeFileSync(
      path.join(base, `${ts}-metadata.json`),
      JSON.stringify(metadata, null, 2),
    );
  }
}
```

## Wire-up en `playwright.config.ts`

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  reporter: [
    ['html', { open: 'never' }],
    ['json', { outputFile: 'results/playwright/results.json' }],
    ['./metadata-reporter.ts'],
  ],
  // ... resto de la config
});
```

## Mapeo de campos

| Campo metadata | Origen Playwright |
|---|---|
| `scenario_or_feature` | `process.env.SCENARIO_NAME` o `--grep` value. |
| `framework` | Constante `playwright`. |
| `workload_or_scope` | `"<N> tests"` donde N = `totals.total`. |
| `sut_endpoint_or_url` | `process.env.BASE_URL` (frontend) o `BACKEND_URL`. |
| `auth_strategy` | `storageState` cuando `auth.setup.ts` está habilitado; `none` en caso contrario. |
| `totals` | Acumulado desde `onTestEnd` por `result.status`. |
| `thresholds_or_coverage_met` | `result.status === 'passed'` (Playwright no tiene thresholds, usa cobertura declarada). |
| `blockers` | Vacío si todo OK; llenado desde `execution-status.json` cuando aplica. |

## Reglas

- Path final: `results/playwright/{YYYY-MM-DD}/{ISO}-metadata.json` (alineado con `[results-structure-universal](../../../_all/results-structure-universal.md)`).
- El reporter NO interfiere con `html` ni `json` builtin; corre en paralelo.
- `auth_strategy` se setea desde `process.env.AUTH_STRATEGY` si el proyecto usa modos múltiples. Default `storageState` para greenfield con auth.
- NO omitir claves: si no aplica, usar enum `"none"` o valor por defecto del schema.
- Si una corrida termina con bloqueo de ambiente (timeouts masivos, browser missing), `onEnd` se ejecuta igualmente y el `metadata.json` se emite con `blockers` poblado por el detector de bloqueos.

## Cross-links

`[execution-metadata-schema](../../../_all/execution-metadata-schema.md)`, `[results-structure-universal](../../../_all/results-structure-universal.md)`, `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`, `[[calidad-delivery-gate-contract]]`, `[[playwright-greenfield]]`.
