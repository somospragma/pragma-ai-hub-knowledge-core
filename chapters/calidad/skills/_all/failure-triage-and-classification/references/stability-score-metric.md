# Stability Score Metric

Métrica canónica del chapter para decidir cuándo un test pasa a quarantine. Sin esta métrica, las decisiones de quarantine son subjetivas.

## Definición

```
stability_score = (runs_pass / runs_total) * 100
```

Calculada sobre las **últimas 20 corridas del test en el pipeline CI** (default; ajustable según volumen). Solo cuentan runs reales del pipeline; **los runs locales del agente o desarrollador NO cuentan** — no son representativos del entorno de ejecución oficial.

## Thresholds y acciones

| Stability score | Estado | Acción |
|---|---|---|
| `>= 95%` | Estable | Ninguna; el test es confiable. |
| `80% – 94%` | Vigilancia | Alertar al owner; abrir ticket de investigación (no quarantine aún). |
| `< 80%` | Inestable | **Mover automáticamente a `@quarantine`** con ticket SLA 14 días (ver `quarantine-pattern.md`). |

## Implementación

Requiere history-tracking del test runner. Opciones soportadas por el chapter:

- **Allure Report** con `history/` (default para Playwright/Karate).
- **ReportPortal** (multi-framework; recomendado para multi-suite y multi-proyecto).
- **GitHub Actions artifacts** + script propio (fallback minimalista).

Ver `[[calidad-cicd-integration]]` para la configuración detallada por framework y CI.

## Snippet: cálculo desde Allure `history.json`

`allure-results/history/history.json` (después de varios runs) contiene array de runs por test. Cálculo en Node:

```ts
import fs from 'node:fs';

type HistoryEntry = { status: 'passed' | 'failed' | 'broken' | 'skipped' };
type History = Record<string, { items: HistoryEntry[] }>;

const history: History = JSON.parse(
  fs.readFileSync('allure-results/history/history.json', 'utf8'),
);

const WINDOW = 20;
const QUARANTINE_THRESHOLD = 80;

for (const [testId, data] of Object.entries(history)) {
  const recent = data.items.slice(-WINDOW);
  const passed = recent.filter((r) => r.status === 'passed').length;
  const total = recent.length;
  const score = (passed / total) * 100;

  if (score < QUARANTINE_THRESHOLD) {
    console.log(`QUARANTINE  ${score.toFixed(1)}%  ${testId}`);
  } else if (score < 95) {
    console.log(`WATCH       ${score.toFixed(1)}%  ${testId}`);
  }
}
```

## Reglas operativas

- El cálculo debe correrse al final de cada job de CI; el resultado se publica en el dashboard del chapter.
- Si un test tiene menos de 5 runs históricos, **no calcular score** (muestra insuficiente); marcar como "insufficient history".
- Si el SUT estuvo caído durante alguno de los últimos 20 runs, **excluir esos runs** del cálculo (no son representativos). Requiere marcar el run como "env-failure" al momento de ocurrir.
- El stability score se reporta junto con la evidencia del test en cada entregable (ver `[[calidad-test-evidence-and-traceability]]`).

## Anti-patrones

- **Calcular score solo con runs locales**: invalida la métrica.
- **Aumentar el `WINDOW` para diluir un test malo**: trampa. El window se ajusta solo por volumen real (tests con cientos de runs/día pueden usar 50; tests con pocos runs/día mantienen 20).
- **Ocultar runs `failed` del histórico**: viola el contrato anti-cheating.
