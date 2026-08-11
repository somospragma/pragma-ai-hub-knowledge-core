# Execution Status & Blockers — Variante K6

Versión K6 del schema universal `[[calidad-environment-blocker-evidence]]`. Se emite cuando una corrida K6 termina sin poder validar performance porque el ambiente bloquea el tráfico (WAF, rate limit, IdP caído), no porque el SUT esté lento o roto.

## Schema K6-específico

Extiende el schema base con campos propios de K6 que dan contexto al bloqueo (`vu_count_at_block`, `scenario`, `workload`).

```json
{
  "exitCode": 99,
  "framework": "k6",
  "endpoint_or_url": "https://api.example.com/transactions",
  "timestamp": "2026-06-05T10:30:15Z",
  "reason": "environment_blocked_waf",
  "command": "k6 run tests/carga/main.js",
  "statusCode": 403,
  "responseHeaders": {
    "X-CDN": "Incapsula",
    "X-Iinfo": "..."
  },
  "stderr_tail": "WARN[0042] Request Failed error=...",
  "scenario": "carga",
  "workload": "ramping-vus 50→200 over 10min",
  "vu_count_at_block": 137,
  "failed_request_rate_at_block": 0.94,
  "checks_failed_at_block": 1240
}
```

## Categorías típicas K6

Subset de las categorías universales que se observa con más frecuencia en pruebas de performance:

- `environment_blocked_waf` — Incapsula/Cloudflare interpreta el ramp-up como ataque y bloquea con 403 sostenido. Síntoma: `failed_request_rate > 0.5` con `statusCode === 403` y `X-CDN` presente.
- `environment_rate_limit` — Gateway aplica 429 con `Retry-After` mayor a la ventana de la prueba. La carga planificada no se puede sostener.
- `environment_auth_fail` — IdP/OAuth provider caído. Los `setup` o `per-vu` auth no obtienen token. `failed_request_rate == 1.0` en endpoints autenticados desde el primer VU.
- `environment_dns_fail` — Hostname del SUT no resuelve. `k6` aborta con `lookup ENOTFOUND`.

## Detección dentro de `handleSummary`

K6 expone métricas agregadas en `data` (la entrada de `handleSummary(data)`). El criterio default: si el `http_req_failed.rate > 0.5` en cualquier escenario, se considera bloqueo de ambiente y se emite `execution-status.json`.

```javascript
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const today = timestamp.slice(0, 10);
  const scenario = __ENV.SCENARIO_NAME || 'unknown';
  const base = `results/${scenario}/${today}`;

  const out = {
    [`${base}/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };

  // Detección de bloqueo: failureRate > 0.5 en cualquier escenario
  const failedRate = data.metrics.http_req_failed?.values?.rate ?? 0;
  if (failedRate > 0.5) {
    const reason = inferBlockerReason(data);
    const status = {
      exitCode: 99,
      framework: 'k6',
      endpoint_or_url: __ENV.BASE_URL || 'unknown',
      timestamp: new Date().toISOString(),
      reason: reason,
      command: `k6 run tests/${scenario}/main.js`,
      statusCode: inferDominantStatus(data),
      responseHeaders: {},
      stderr_tail: '',
      scenario: scenario,
      workload: __ENV.WORKLOAD_DESCRIPTOR || 'unknown',
      vu_count_at_block: data.metrics.vus?.values?.value ?? 0,
      failed_request_rate_at_block: failedRate,
      checks_failed_at_block: data.metrics.checks?.values?.fails ?? 0,
    };
    out['.evidence/execution-status.json'] = JSON.stringify(status, null, 2);
  }

  return out;
}

function inferBlockerReason(data) {
  // 403 dominante → WAF; 429 dominante → rate limit; sin respuestas → DNS/network
  const reqs = data.metrics.http_reqs?.values?.count ?? 0;
  if (reqs === 0) return 'environment_dns_fail';
  // Para granularidad real por status code, instrumentar tags `status:XXX` en checks
  // y leer data.metrics['http_reqs{status:403}'] etc.
  if (data.metrics['http_reqs{status:403}']?.values?.count > reqs * 0.5) {
    return 'environment_blocked_waf';
  }
  if (data.metrics['http_reqs{status:429}']?.values?.count > reqs * 0.5) {
    return 'environment_rate_limit';
  }
  if (data.metrics['http_reqs{status:401}']?.values?.count > reqs * 0.5) {
    return 'environment_auth_fail';
  }
  return 'environment_blocked_network';
}

function inferDominantStatus(data) {
  for (const code of [403, 429, 401, 500, 502, 503]) {
    if (data.metrics[`http_reqs{status:${code}}`]?.values?.count > 0) return code;
  }
  return 0;
}
```

## Reglas K6 específicas

- El threshold semántico `failureRate > 0.5` aplica por escenario, no agregado global. Cada `tests/{scenario}/main.js` evalúa el suyo.
- Para que `inferBlockerReason` funcione, los checks deben usar tags `{ status: r.status }` o equivalentes. Ver `[tag-policy-and-metrics-isolation](./tag-policy-and-metrics-isolation.md)`.
- Si el bloqueo se detecta, el status del delivery_gate K6 es `partial` con `blocker: "environment_blocked_<type>"`. No se ejecutan los escenarios siguientes (`carga` no se corre si `linea-base` quedó bloqueado).
- NUNCA bajar thresholds para "pasar" cuando hay un WAF de por medio (anti-cheating). El bloqueo se escala a infra.

## Cross-links

`[[calidad-environment-blocker-evidence]]`, `[handle-summary-evidence](./handle-summary-evidence.md)`, `[tag-policy-and-metrics-isolation](./tag-policy-and-metrics-isolation.md)`, `[[calidad-delivery-gate-contract]]`, `[[calidad-post-generation-protocol]]`.
