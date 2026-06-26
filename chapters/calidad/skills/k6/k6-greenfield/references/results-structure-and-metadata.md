# Estructura de `results/` y schema de `metadata.json`

Toda corrida de k6 debe dejar evidencia persistente bajo `results/` con una estructura jerárquica por escenario y fecha. Cada corrida produce dos artefactos: el `summary.json` nativo de k6 y un `metadata.json` con el contexto de ejecución (entorno, workload, exit code, disponibilidad observada, blockers).

## Estructura obligatoria

```
results/
├── linea-base/
│   └── 2026-06-04/
│       ├── 2026-06-04T10-30-15-summary.json
│       └── 2026-06-04T10-30-15-metadata.json
├── carga/
│   └── 2026-06-04/
│       ├── 2026-06-04T11-15-22-summary.json
│       └── 2026-06-04T11-15-22-metadata.json
└── estres/
    └── 2026-06-04/
        └── ...
```

Reglas:

- Primer nivel: `results/{scenario}/` con el vocabulario decidido en ``vocabulary-and-scenario-mapping.md`` (`linea-base|carga|estres|spike|soak` o `smoke|load|stress|spike|soak`).
- Segundo nivel: `results/{scenario}/{YYYY-MM-DD}/`.
- Por corrida: `{ISO-timestamp-safe}-summary.json` + `{ISO-timestamp-safe}-metadata.json`.
- Timestamp safe: `new Date().toISOString().replace(/[:.]/g, '-')`. Reemplazar `:` y `.` por `-` evita problemas en filesystems Windows y en URLs.
- La carpeta `results/` está en `.gitignore`. La evidencia se sube como artefacto del pipeline, no se commitea.

## Schema de `metadata.json`

```json
{
  "scenario":              "linea-base",
  "framework":             "k6",
  "version":               "v1",
  "environment":           "staging",
  "workload":              "ramping-vus 5-5-0 over 5min",
  "sut_endpoint":          "https://api.example.com/v1/transactions",
  "auth_strategy":         "setup",
  "exit_code":             0,
  "started_at":            "2026-06-04T10:30:15Z",
  "finished_at":           "2026-06-04T10:35:18Z",
  "duration_seconds":      303,
  "vu_max":                5,
  "iterations_total":      1543,
  "thresholds_met":        true,
  "availability_target":   99.5,
  "availability_observed": 99.7,
  "blockers":              []
}
```

### Campos

- `scenario`: nombre del escenario en el vocabulario elegido.
- `framework`: `"k6"` (constante, alinea con `[[calidad-delivery-gate-contract]]`).
- `version`: versión del schema de `metadata.json`; iniciar en `"v1"`.
- `environment`: `__ENV.ENVIRONMENT` (`staging|qa|preprod|prod-canary|...`).
- `workload`: descripción legible de los stages (auto-generable desde `options.stages`).
- `sut_endpoint`: URL principal del SUT (no la URL de auth).
- `auth_strategy`: `setup|refresh|per-vu` según ``auth-strategy-setup-vs-per-vu.md``.
- `exit_code`: `0` si la corrida fue normal y todos los thresholds pasaron, distinto de 0 si falló alguno.
- `started_at`, `finished_at`: ISO-8601 UTC.
- `duration_seconds`: `data.state.testRunDurationMs / 1000` redondeado.
- `vu_max`: `data.metrics.vus_max.values.max`.
- `iterations_total`: `data.metrics.iterations.values.count`.
- `thresholds_met`: `Object.values(data.metrics).every(m => !m.thresholds || Object.values(m.thresholds).every(t => t.ok))`.
- `availability_target`, `availability_observed`: ver ``availability-metric-from-rnf.md``. `null` si el RNF no declara objetivo.
- `blockers`: array; vacío en corridas limpias. Esquema de entrada en ``execution-status-and-blockers.md``.

## `handleSummary()` corregido

Paths relativos desde el project root. NO usar `../results/...` porque cuando `k6 run tests/linea-base/main.js` se ejecuta desde la raíz del proyecto, `..` apunta fuera del proyecto.

```javascript
import { textSummary } from './vendor/k6-summary.js';

export function handleSummary(data) {
  const ts       = new Date().toISOString().replace(/[:.]/g, '-');
  const scenario = __ENV.SCENARIO_NAME || 'unknown';
  const date     = ts.split('T')[0];
  const base     = `results/${scenario}/${date}`;

  return {
    [`${base}/${ts}-summary.json`]:  JSON.stringify(data, null, 2),
    [`${base}/${ts}-metadata.json`]: JSON.stringify(buildMetadata(data, scenario), null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function buildMetadata(data, scenario) {
  const failureRate     = data.metrics.http_req_failed?.values?.rate ?? 0;
  const availability    = Number(((1 - failureRate) * 100).toFixed(4));
  const target          = Number(__ENV.AVAILABILITY_TARGET) || null;
  const thresholdsMet   = Object.values(data.metrics).every(
    (m) => !m.thresholds || Object.values(m.thresholds).every((t) => t.ok),
  );
  const durationSeconds = Math.round((data.state?.testRunDurationMs ?? 0) / 1000);
  const startedAt       = new Date(Date.now() - durationSeconds * 1000).toISOString();
  const finishedAt      = new Date().toISOString();

  return {
    scenario,
    framework:             'k6',
    version:               'v1',
    environment:           __ENV.ENVIRONMENT || 'unknown',
    workload:              __ENV.WORKLOAD || 'see options.stages',
    sut_endpoint:          __ENV.SUT_ENDPOINT || __ENV.BASE_URL || 'unknown',
    auth_strategy:         __ENV.AUTH_STRATEGY || 'setup',
    exit_code:             thresholdsMet ? 0 : 1,
    started_at:            startedAt,
    finished_at:           finishedAt,
    duration_seconds:      durationSeconds,
    vu_max:                data.metrics.vus_max?.values?.max ?? null,
    iterations_total:      data.metrics.iterations?.values?.count ?? 0,
    thresholds_met:        thresholdsMet,
    availability_target:   target,
    availability_observed: target !== null ? availability : null,
    blockers:              [],
  };
}
```

## Anti-pattern (Hallazgo #4)

```javascript
// MAL: cuando se ejecuta `k6 run tests/linea-base/main.js` desde la raíz del proyecto,
// `../results/` apunta fuera del proyecto. La evidencia se pierde o queda en lugar
// inesperado del filesystem.
return {
  [`../results/${ts}-summary.json`]: JSON.stringify(data, null, 2),
};
```

Reglas para evitarlo:

- Paths relativos al CWD donde se invoca `k6 run`. Convención: invocar siempre desde la raíz del proyecto (documentar en README y en `run-all.sh`).
- Usar siempre `results/{scenario}/{date}/...` (sin `..`).
- Crear el directorio antes de la corrida si el k6 runner no lo crea automáticamente. Algunas versiones de k6 fallan si el path no existe; agregar `mkdir -p results/{scenario}/{date}` en `run-all.sh`.

## Inputs por variables de entorno

El `handleSummary` lee de `__ENV` para evitar acoplar el script a un entorno concreto:

- `SCENARIO_NAME`: requerido. Pasarlo en `run-all.sh`: `SCENARIO_NAME=linea-base k6 run tests/linea-base/main.js`.
- `ENVIRONMENT`: opcional, default `unknown`.
- `SUT_ENDPOINT` o `BASE_URL`: opcional, default `unknown`.
- `AUTH_STRATEGY`: opcional, default `setup`.
- `AVAILABILITY_TARGET`: opcional, default `null`.
- `WORKLOAD`: opcional, default `'see options.stages'`.

## Cross-links

- `[[calidad-k6-greenfield]]`
- ``handle-summary-evidence.md``
- ``vocabulary-and-scenario-mapping.md``
- ``availability-metric-from-rnf.md``
- ``execution-status-and-blockers.md``
- `[[calidad-delivery-gate-contract]]`
- `[[calidad-post-generation-protocol]]`
