# Result Schema Common

Esquema unificado al que se normaliza el output de cualquier framework (Karate, Playwright, K6, Appium). Este esquema es el **input contractual** de `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-correction-loop]]` y `[[calidad-test-self-healing]]`.

## Modelo JSON

```json
{
  "framework": "playwright|karate|k6|appium",
  "run_id": "uuid",
  "started_at": "ISO8601",
  "duration_ms": 12345,
  "exit_code": 0,
  "status": "passed|failed|errored|partial",
  "totals": {
    "total": 50,
    "passed": 47,
    "failed": 2,
    "skipped": 1
  },
  "tests": [
    {
      "id": "users.spec.ts::create user successfully",
      "status": "passed|failed_deterministic|failed_flaky|errored|skipped",
      "duration_ms": 234,
      "tags": ["@smoke", "@regression"],
      "error": {
        "type": "AssertionError|TimeoutError|NetworkError|...",
        "message": "...",
        "stack": "..."
      },
      "evidence": [
        "path/to/screenshot.png",
        "path/to/trace.zip"
      ]
    }
  ],
  "thresholds": {
    "passed": true,
    "details": {}
  }
}
```

## Campos a nivel de run

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `framework` | enum | sí | `playwright` \| `karate` \| `k6` \| `appium`. |
| `run_id` | string (uuid) | sí | Identificador único del run; usado en el path de evidencia. |
| `started_at` | string (ISO8601) | sí | Timestamp de inicio en UTC. |
| `duration_ms` | int | sí | Duración total del run en milisegundos. |
| `exit_code` | int | sí | Exit code del proceso del runner. |
| `status` | enum | sí | `passed` (todos pasaron) \| `failed` (≥1 fallo determinístico) \| `errored` (error de runtime / SUT caído) \| `partial` (ejecución degradada). |
| `totals` | object | sí | Conteos agregados. |
| `tests` | array | sí | Detalle por test (puede estar vacío en runs de carga). |
| `thresholds` | object | no | Aplicable principalmente a K6; opcional para otros frameworks. |

## Campos a nivel de test

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | string | sí | Identificador estable: `<archivo>::<nombre>` o `<feature>::<scenario>`. |
| `status` | enum | sí | `passed` \| `failed_deterministic` \| `failed_flaky` \| `errored` \| `skipped`. |
| `duration_ms` | int | sí | Duración del test individual. |
| `tags` | array<string> | no | Tags del test (`@smoke`, `@regression`, etc.). |
| `error` | object | no | Solo si `status` ∈ {`failed_*`, `errored`}. |
| `error.type` | string | no | Categoría: `AssertionError`, `TimeoutError`, `NetworkError`, `ElementNotFound`, `SetupError`, etc. |
| `error.message` | string | no | Mensaje resumido (1-2 líneas). |
| `error.stack` | string | no | Stack trace completo. |
| `evidence` | array<string> | no | Paths relativos a screenshots, traces, videos, logs. |

## Distinción `failed_deterministic` vs `failed_flaky`

- `failed_deterministic`: el test falló de forma repetible en la primera y todas las re-ejecuciones (si las hubo).
- `failed_flaky`: el test falló en al menos una corrida pero pasó en otra dentro del mismo run (retry habilitado).
- Esta distinción la pobla el parser cuando el framework expone retries (Playwright: `retry` count > 0 con resultado final `passed`; Karate: re-runs configurados; K6: no aplica; Appium con Serenity: similar a Playwright).

## Distinción `failed` vs `errored` a nivel de run

- `failed`: el runner ejecutó y produjo resultados, pero al menos un test falló su assertion.
- `errored`: el runner no pudo completar la ejecución (compile error, dependency missing, SUT inalcanzable, timeout global).
- `partial`: ejecución parcial intencional (modo `scaffold-only` degradado, suite cortada por timeout configurado, sharding sin completar todos los shards).

## Convenciones de naming para `id` de test

| Framework | Patrón | Ejemplo |
|---|---|---|
| Playwright | `<spec-file>::<test-title>` | `users.spec.ts::create user successfully` |
| Karate | `<feature>::<scenario>` | `users.feature::create new user` |
| K6 | `<script>::<scenario>` o `<script>::<check>` | `smoke-test.js::api availability` |
| Appium / Serenity | `<story>::<scenario>` | `LoginStory::user logs in successfully` |

## Uso downstream

- `[[calidad-failure-triage-and-classification]]` consume `tests[].error.type` y `tests[].error.message` para clasificar cada fallo (bug del test / bug del SUT / problema de entorno / dato).
- `[[calidad-test-self-correction-loop]]` consume `tests[].status` + `error.stack` + `evidence` para proponer fixes acotados al test.
- `[[calidad-test-evidence-and-traceability]]` consume `tests[].evidence` y `run_id` para armar el bundle de evidencia archivable.
- `[[calidad-cicd-integration]]` consume `status` + `thresholds.passed` para decidir si abrir o cerrar un gate de calidad.
