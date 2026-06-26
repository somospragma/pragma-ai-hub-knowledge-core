# Disponibilidad como métrica operacionalizada desde RNF

Cuando el `user_story` o las RNF declaran un objetivo de disponibilidad (`availability ≥ X%`, "uptime 99.9%", "SLA 99.5"), ese objetivo NO debe quedar como prosa en el README. Debe operacionalizarse como una métrica derivada y reportada en cada corrida.

## Fórmula

```
availability = (1 - http_req_failed.rate) × 100
```

`http_req_failed` es una métrica nativa de k6 que cuenta cada request HTTP como exitoso o fallido según `responseCallback` (default: status 2xx/3xx = exitoso, 4xx/5xx = fallido). La tasa `rate` es la fracción de fallos sobre el total de requests del intervalo.

Reportar la disponibilidad observada por escenario (Línea Base / Carga / Estrés) y compararla contra el target del RNF.

## Threshold opcional para enforce

Cuando el RNF lo justifica, declarar el threshold equivalente para que k6 falle la corrida si no se cumple:

```javascript
// para target 99% → fallos < 1%
'http_req_failed{step:main}': ['rate<0.01'],

// para target 99.5% → fallos < 0.5%
'http_req_failed{step:main}': ['rate<0.005'],

// para target 99.9% → fallos < 0.001
'http_req_failed{step:main}': ['rate<0.001'],
```

Filtrar por `{step:main}` para que la disponibilidad se evalúe sobre el endpoint objetivo, no contaminada por fallos de auth o cleanup (ver ``tag-policy-and-metrics-isolation.md``).

## Snippet `handleSummary()` con cálculo de disponibilidad

```javascript
import { textSummary } from './vendor/k6-summary.js';

const AVAILABILITY_TARGET = Number(__ENV.AVAILABILITY_TARGET || 99.5);

export function handleSummary(data) {
  const failureRate  = data.metrics.http_req_failed?.values?.rate ?? 0;
  const availability = (1 - failureRate) * 100;
  const met          = availability >= AVAILABILITY_TARGET;

  // exponer la métrica derivada dentro del propio summary
  data.metrics.availability = {
    type: 'gauge',
    contains: 'default',
    values: { value: Number(availability.toFixed(4)) },
    thresholds: {
      [`availability>=${AVAILABILITY_TARGET}`]: { ok: met },
    },
  };

  const ts       = new Date().toISOString().replace(/[:.]/g, '-');
  const scenario = __ENV.SCENARIO_NAME || 'unknown';
  const date     = ts.split('T')[0];
  const base     = `results/${scenario}/${date}`;

  const metadata = {
    scenario,
    framework:             'k6',
    availability_target:   AVAILABILITY_TARGET,
    availability_observed: Number(availability.toFixed(4)),
    met,
    failure_rate:          Number(failureRate.toFixed(6)),
  };

  return {
    [`${base}/${ts}-summary.json`]:  JSON.stringify(data, null, 2),
    [`${base}/${ts}-metadata.json`]: JSON.stringify(metadata, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

## Reporte en `metadata.json`

El `metadata.json` por corrida (schema completo en ``results-structure-and-metadata.md``) debe incluir:

```json
{
  "availability_target":   99.5,
  "availability_observed": 99.7,
  "met":                   true
}
```

Cuando `met === false`, registrar la brecha en `delivery_gate.blockers` (ver `[[calidad-delivery-gate-contract]]`):

```json
{
  "blockers": [
    {
      "type":     "availability_below_target",
      "scenario": "carga",
      "target":   99.5,
      "observed": 98.7
    }
  ]
}
```

## Cuándo NO declarar el threshold

- Si el escenario es `estres` y el objetivo es encontrar el punto de quiebre, declarar `availability` como observada (no enforced). El stress test está diseñado para fallar; enforce de disponibilidad lo invalida.
- Si el RNF no declara un objetivo cuantificado, NO inventar uno. Reportar `availability_target: null` y `met: null`.

## Anti-cheating

- Aflojar `AVAILABILITY_TARGET` para que `met === true` es violación grave. El target proviene del RNF; si la observada no llega, se reporta el gap, no se mueve el target.
- Sumar `step:auth` al cálculo para inflar la base de requests y diluir los fallos del SUT también es violación. La fórmula se aplica sobre `step:main`.

## Cross-links

- `[[calidad-k6-greenfield]]`
- ``tag-policy-and-metrics-isolation.md``
- ``thresholds-three-tiers.md``
- ``results-structure-and-metadata.md``
- `[[calidad-delivery-gate-contract]]`
- `[[calidad-post-generation-protocol]]`
