# Política de tags y aislamiento de métricas

Cada `check()` y cada request HTTP emitido por la suite K6 DEBE llevar tags estandarizados. Los tags son el único mecanismo confiable para aislar métricas por endpoint, etapa del flujo y escenario, evitando que fallos de un componente (por ejemplo, el provider de auth) contaminen la métrica del endpoint objetivo y enmascaren un cumplimiento (o incumplimiento) real del SLA.

## Regla obligatoria de tags

Todo `http.<verb>(...)` y todo `check(...)` debe llevar el bloque `tags` con estas tres claves:

```javascript
tags: {
  endpoint: '<nombre-operacion>',           // p.ej. 'retrieveTransactions', 'auth', 'createUser'
  step:     'auth' | 'main' | 'cleanup',    // etapa del flujo dentro del iterate
  scenario: 'linea-base' | 'carga' | 'estres' | 'spike' | 'soak',
}
```

- `endpoint`: identifica la operación de negocio (preferir `operationId` del spec; si no existe, usar `<verb>-<resource>`). NO usar la URL cruda con `{id}` interpolados — eso explota la cardinalidad.
- `step`: ubica el request dentro del flujo. `auth` aísla todo lo relativo a obtención/refresco de token. `main` cubre el endpoint objetivo (el SUT). `cleanup` cubre teardown (DELETE de recursos creados, logout, etc.).
- `scenario`: alinea con el vocabulario decidido en `[[vocabulary-and-scenario-mapping]]`. Permite filtrar métricas cuando varios scripts vuelcan al mismo backend de observabilidad.

## Thresholds aislados por tag

Los thresholds se declaran filtrando por tag con la sintaxis `metric{tagName:tagValue}`. Esto garantiza que el SLA del endpoint objetivo se evalúe sobre su propia métrica, no sobre el agregado del proyecto.

```javascript
export const options = {
  thresholds: {
    // métricas del endpoint objetivo (SUT)
    'http_req_failed{step:main}':                       ['rate<0.01'],
    'http_req_duration{name:retrieveTransactions}':     ['p(95)<800', 'p(99)<2000'],
    'checks{endpoint:retrieveTransactions}':            ['rate>0.99'],

    // métricas de auth: tolerar más latencia, no contaminan el SLA del SUT
    'http_req_failed{step:auth}':                       ['rate<0.05'],
    'http_req_duration{name:auth}':                     ['p(95)<2000'],

    // métrica global secundaria (sanity check transversal)
    'http_req_failed':                                  ['rate<0.02'],
  },
};
```

Notas sobre la sintaxis:

- `name:` es un tag implícito que k6 popula automáticamente para `http.*` cuando se pasa `tags.name` o cuando se usa la firma `http.get(url, { tags: { name: 'retrieveTransactions' } })`. Sirve para agrupar varias URLs distintas bajo una sola operación (path templating).
- `endpoint:` y `step:` son tags custom: deben declararse explícitamente en cada request/check.
- Combinar filtros: `'http_req_duration{name:retrieveTransactions,step:main}': ['p(95)<800']`.

## Snippet de uso en request y check

```javascript
const res = http.get(
  `${config.baseUrl}/transactions`,
  {
    headers: getDefaultHeaders(token),
    tags: { name: 'retrieveTransactions', endpoint: 'retrieveTransactions', step: 'main', scenario: __ENV.SCENARIO_NAME },
  },
);
check(
  res,
  {
    'status is 200': (r) => r.status === 200,
    'has data array': (r) => Array.isArray(r.json('data')),
  },
  { endpoint: 'retrieveTransactions', step: 'main', scenario: __ENV.SCENARIO_NAME },
);
```

## Anti-pattern

Declarar thresholds globales sin tags:

```javascript
// MAL: la métrica del endpoint objetivo se contamina con la latencia del auth flow
thresholds: {
  http_req_duration: ['p(95)<800'],
  http_req_failed:   ['rate<0.01'],
}
```

Consecuencia: una corrida con auth lento (p95=1500ms) hace fallar el threshold global aunque el endpoint objetivo cumpla holgadamente con p95=400ms. O al revés: un endpoint objetivo lento queda enmascarado por miles de requests de auth rápidos. En ambos casos el SLA del SUT no se evalúa correctamente.

## Anti-cheating

La política de tags NO es un mecanismo para aflojar thresholds. Aislar métricas hace que el SLA del SUT se mida sobre su propia muestra, lo cual es más estricto, no más laxo. Tolerar latencia mayor en `step:auth` es legítimo porque auth no es el SUT, pero si la corrida observa que auth degrada el flujo completo eso debe documentarse como hallazgo, no esconderse subiendo el threshold del SUT.

## Cross-links

- `[[k6-greenfield]]`
- `[[k6-thresholds-three-tiers]]`
- `[[auth-strategy-setup-vs-per-vu]]`
- `[[results-structure-and-metadata]]`
- `[[calidad-pre-generation-protocol]]`
- `[[calidad-post-generation-protocol]]`
- `[[calidad-delivery-gate-contract]]`
