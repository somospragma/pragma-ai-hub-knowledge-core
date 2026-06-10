# Arquitectura modular K6 (scenarios + workloads + tests + shared)

Documento de referencia para la generación de proyectos K6 greenfield bajo la arquitectura modular idiomática. Sustituye al enfoque monolítico de un script por escenario (smoke/load/stress/spike/soak) heredado en `references/templates/*-test.js.tpl`.

Cross-links: `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-delivery-gate-contract]]`, `[[k6-greenfield]]`, `[[k6-options-scenarios-executors]]`.

## Por qué separar scenarios / workloads / tests

- **Reusabilidad**: un mismo flow HTTP (scenario) se ejecuta con múltiples workloads sin duplicar lógica. Un único `retrieve-transactions.js` corre como línea base, carga y estrés.
- **Mantenibilidad**: cambiar la curva de carga (stages, executor, QPS) no obliga a tocar la lógica del flow. Cambiar el flow no obliga a re-validar curvas de carga.
- **Trazabilidad**: cada `tests/{escenario}/main.js` declara explícitamente qué scenario + qué workload está combinando. La intención del test queda autodocumentada.
- **Anti-duplicación**: con cinco scripts monolíticos se duplican 5x el bloque HTTP, los checks, los tags y el `handleSummary`. Cualquier cambio se replica cinco veces y es fuente de drift.
- **Escalabilidad**: agregar un nuevo flow (`auth`, `update-profile`, `checkout`) o un nuevo perfil de carga (`spike`, `soak`) es lineal: se agrega un archivo por carpeta, no se reescribe todo.

## Reglas por carpeta

### `scenarios/{flow}.js`

- Exporta una función `default` con la secuencia HTTP del flujo (auth, main, cleanup).
- **No** define `options`. La carga la decide el workload.
- Usa `group()` para envolver pasos y `check()` con `tags` consistentes (`endpoint`, `step`).
- Reutiliza `shared/config.js` (URL, env vars) y `shared/utils.js` (`getAuthHeaders`, `uuidv4`).
- Si requiere autenticación, importa el helper de `scenarios/auth.js` — no inlinea login.

### `workloads/{escenario}.js`

- Exporta `options` con `scenarios:` (executors, vus/rate, stages, duration, tags).
- Importa `thresholds` desde `shared/thresholds.js` (`thresholdsBaseline`, `thresholdsCarga`, `thresholdsEstres`).
- Asigna `tags: { scenario: 'linea-base'|'carga'|'estres' }` en cada bloque para correlacionar métricas por workload.
- Decide el **executor** según el objetivo (ver `[[k6-options-scenarios-executors]]`).

### `tests/{escenario}/main.js`

- Es el archivo **ejecutable** por `k6 run`.
- Re-exporta `options` desde su workload.
- Re-exporta `default` desde su scenario.
- Re-exporta `handleSummary` desde `shared/handle-summary.js`.
- No contiene lógica propia: es un orquestador puro de tres líneas.

### `shared/`

- `config.js`: URLs (BASE_URL, AUTH_URL), enums, headers constantes, fallback con `__ENV`.
- `utils.js`: helpers cross-cutting (`uuidv4`, `getAuthHeaders`, `randomIntBetween` re-export, `buildXxxBody`).
- `thresholds.js`: thresholds por tier (Conservative / Moderate / Relaxed) y por escenario (`thresholdsBaseline`, `thresholdsCarga`, `thresholdsEstres`).
- `handle-summary.js`: función `handleSummary` compartida — un único punto de truth para el JSON de resultados y el `textSummary` en stdout.

## Snippet end-to-end

### `scenarios/retrieve-transactions.js`

```javascript
import http from 'k6/http';
import { group, check, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from '../shared/config.js';
import { getAuthHeaders } from '../shared/utils.js';

export default function () {
  group('retrieve-transactions', () => {
    const res = http.get(`${config.baseUrl}/transactions`, {
      headers: getAuthHeaders(),
      tags: { endpoint: 'retrieveTransactions', step: 'main' },
    });
    check(res, {
      'status 200': (r) => r.status === 200,
      'has data array': (r) => Array.isArray(r.json('data')),
    }, { endpoint: 'retrieveTransactions', step: 'main' });
    sleep(randomIntBetween(1, 3));
  });
}
```

### `workloads/linea-base.js`

```javascript
import { thresholdsBaseline } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    linea_base: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 5 },
        { duration: '3m', target: 5 },
        { duration: '1m', target: 0 },
      ],
      tags: { scenario: 'linea-base' },
    },
  },
  thresholds: thresholdsBaseline,
};
```

### `tests/linea-base/main.js`

```javascript
export { options } from '../../workloads/linea-base.js';
export { default } from '../../scenarios/retrieve-transactions.js';
export { handleSummary } from '../../shared/handle-summary.js';
```

## Mapa scenario × workload

Combinatoria recomendada para una suite mínima sobre un único flow `{main-flow}`:

| Test ejecutable | Scenario | Workload | Executor |
|---|---|---|---|
| `tests/linea-base/main.js` | `scenarios/{main-flow}.js` | `workloads/linea-base.js` | `ramping-vus` (baseline 20-30% del peak) |
| `tests/carga/main.js` | `scenarios/{main-flow}.js` | `workloads/carga.js` | `ramping-vus` (100% del peak) |
| `tests/estres/main.js` | `scenarios/{main-flow}.js` | `workloads/estres.js` | `ramping-arrival-rate` (200-300% progresivo) |

Si el flow requiere autenticación previa, se compone delegando a `scenarios/auth.js` desde el flow principal (no se mezcla login + main en el mismo archivo).

## Convivencia con templates monolíticos

Los templates `smoke-test.js.tpl`, `load-test.js.tpl`, `stress-test.js.tpl`, `spike-test.js.tpl` y `soak-test.js.tpl` quedan marcados como **DEPRECATED** al inicio del archivo y se conservan únicamente para proyectos brownfield que ya nacieron con estructura monolítica (`[[k6-brownfield]]`). Todo proyecto greenfield nuevo debe generarse con la estructura modular descrita en este documento.
