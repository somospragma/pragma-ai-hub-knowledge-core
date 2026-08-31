# Metadata Emitter — serenity-wdio (WebdriverIO + Serenity/JS)

WebdriverIO expone el hook de ciclo de vida `onComplete` en cada `configs/wdio.<modo>.conf.ts`. Este reference define cómo derivar el `{ISO}-metadata.json` universal definido en `[execution-metadata-schema](../../../_all/execution-metadata-schema.md)` a partir del reporte Cucumber JSON generado por `wdio-cucumberjs-json-reporter`.

## Mecanismo

`wdio.shared.conf.ts` declara una función `emitMetadata` reutilizada por todos los configs por modo mediante el hook `onComplete`:

1. Lee el reporte Cucumber JSON generado en `.tmp/json/` (o el path configurado en `wdio-cucumberjs-json-reporter`) al finalizar la corrida.
2. Construye el objeto metadata respetando el schema universal.
3. Escribe `results/serenity-wdio/{YYYY-MM-DD}/{ISO}-metadata.json`.
4. Se ejecuta siempre, incluso si la suite terminó con escenarios fallidos (`onComplete` recibe `exitCode` como primer argumento).

## Snippet `wdio.shared.conf.ts`

```typescript
// wdio.shared.conf.ts — emitMetadata reutilizado por todos los modos
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

interface CucumberJsonFeature {
  elements?: Array<{ steps?: Array<{ result?: { status?: string } }> }>;
}

export async function emitMetadata(
  exitCode: number,
  mode: string,
  platform?: string,
): Promise<void> {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').replace('Z', 'Z');
  const date = ts.slice(0, 10);
  const base = join('results', 'serenity-wdio', date);
  mkdirSync(base, { recursive: true });

  const jsonPath = join('.tmp', 'json', `${mode}.cucumber.json`);
  const features: CucumberJsonFeature[] = existsSync(jsonPath)
    ? JSON.parse(readFileSync(jsonPath, 'utf8'))
    : [];

  let total = 0, passed = 0, failed = 0, skipped = 0;
  for (const feature of features) {
    for (const scenario of feature.elements ?? []) {
      total += 1;
      const statuses = (scenario.steps ?? []).map((s) => s.result?.status);
      if (statuses.includes('failed')) failed += 1;
      else if (statuses.includes('skipped')) skipped += 1;
      else passed += 1;
    }
  }

  const metadata = {
    scenario_or_feature: process.env.TAGS ?? 'all',
    framework: 'serenity-wdio',
    version: 'v1',
    environment: process.env.ENVIRONMENT ?? 'staging',
    workload_or_scope: `${total} escenarios (mode=${mode}${platform ? `, platform=${platform}` : ''})`,
    sut_endpoint_or_url: process.env.BASE_URL ?? process.env.API_BASE_URL ?? '',
    auth_strategy: 'actor',
    exit_code: exitCode,
    started_at: ts,
    finished_at: ts,
    totals: { total, passed, failed, skipped },
    thresholds_or_coverage_met: failed === 0,
    blockers: [] as string[],
  };

  writeFileSync(join(base, `${ts}-metadata.json`), JSON.stringify(metadata, null, 2));
}
```

## Cableado por modo

Cada `configs/wdio.<modo>.conf.ts` invoca la función compartida en su propio hook `onComplete`, pasando el `mode` y (en móvil) el `platform`:

```typescript
// configs/wdio.android.conf.ts
import { emitMetadata } from '../wdio.shared.conf';

export const config: WebdriverIO.Config = {
  // ...resto de la config
  onComplete: async (exitCode) => {
    await emitMetadata(exitCode, 'movil', 'android');
  },
};
```

## Mapeo de campos

| Campo metadata | Origen serenity-wdio |
|---|---|
| `scenario_or_feature` | `process.env.TAGS` (expresión de tags pasada a `scripts/run.mjs --tags=...`) o `'all'`. |
| `framework` | Constante `serenity-wdio`. |
| `workload_or_scope` | `"<N> escenarios (mode=<modo>[, platform=<platform>])"`. |
| `sut_endpoint_or_url` | `BASE_URL` (web/web_movil) o `API_BASE_URL` (api); vacío en móvil/desktop nativo. |
| `auth_strategy` | `actor` — Screenplay usa Actors que portan credenciales. `none` si el flujo no requiere auth. |
| `totals` | Derivado del reporte Cucumber JSON: escenarios con algún step `failed` cuentan como `failed`; con algún `skipped` (sin `failed`) cuentan como `skipped`; el resto como `passed`. |
| `thresholds_or_coverage_met` | `failed === 0`. |
| `blockers` | Vacío si OK; llenado desde `execution-status.json` cuando el preflight degrada una plataforma a `scaffold-only` (device/simulador/navegador no disponible). |

## Reglas

- Path final: `results/serenity-wdio/{YYYY-MM-DD}/{ISO}-metadata.json` (alineado con `[results-structure-universal](../../../_all/results-structure-universal.md)`).
- `onComplete` se ejecuta siempre, incluso si la suite terminó con `exitCode !== 0` — clave para evidencia de corridas rojas.
- La función `emitMetadata` vive únicamente en `wdio.shared.conf.ts` y se importa desde cada config por modo; no se duplica su lógica en cada `configs/wdio.<modo>.conf.ts`.
- NO omitir claves: si el modo no aplica una semántica (ej. `desktop` sin `sut_endpoint_or_url`), usar cadena vacía o el enum neutro del schema, nunca eliminar la clave.
- Si el pre-flight (`preflight-serenity-wdio.sh`) degrada una plataforma a `scaffold-only`, el `blockers` de esa corrida recibe el `reason` desde `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`.

## Cross-links

`[execution-metadata-schema](../../../_all/execution-metadata-schema.md)`, `[results-structure-universal](../../../_all/results-structure-universal.md)`, `[environment-blocker-evidence](../../../_all/environment-blocker-evidence.md)`, `[[calidad-delivery-gate-contract]]`, `[[serenity-wdio-greenfield]]`.
