
# Cinco tipos de scripts K6

Todo proyecto K6 greenfield emite los cinco scripts. Cada uno tiene un propósito distinto, un perfil de VUs y stages característicos, y debe declarar `options.stages` y `options.thresholds`.

## Tabla maestra

| Script | Propósito | VUs | Duración | Forma de stages |
|---|---|---|---|---|
| `smoke-test.js` | Validación básica del flujo + baseline mínimo | 1-5 (típ. 3) | 5-10 min | plano |
| `load-test.js` | Carga normal y pico esperado, valida SLAs | 0 → 10 → 30 → 50 → 0 | 10-30 min | rampa |
| `stress-test.js` | Encontrar el punto de quiebre | 0 → 50 → 100 → 200 → 300 → 50 → 0 | 15-30 min | rampa agresiva |
| `spike-test.js` | Picos súbitos de demanda + recuperación | 10 → 200 → 10 | 5-10 min | spike + recovery |
| `soak-test.js` | Estabilidad a largo plazo (memory leaks, drift) | 50 constantes | 2-8 h | constante |

## Snippets de `options.stages` por tipo

```javascript
// smoke-test.js
export const options = {
  stages: [
    { duration: '1m', target: 3 },
    { duration: '5m', target: 3 },
    { duration: '1m', target: 0 },
  ],
  thresholds: { /* tier — ver k6-thresholds-three-tiers */ },
};

// load-test.js
export const options = {
  stages: [
    { duration: '2m',  target: 10 },
    { duration: '5m',  target: 30 },
    { duration: '10m', target: 50 },
    { duration: '3m',  target: 0 },
  ],
};

// stress-test.js
export const options = {
  stages: [
    { duration: '2m', target: 50 },
    { duration: '5m', target: 100 },
    { duration: '5m', target: 200 },
    { duration: '5m', target: 300 },
    { duration: '5m', target: 50 },
    { duration: '3m', target: 0 },
  ],
};

// spike-test.js
export const options = {
  stages: [
    { duration: '1m',  target: 10 },
    { duration: '30s', target: 200 },
    { duration: '3m',  target: 200 },
    { duration: '30s', target: 10 },
    { duration: '2m',  target: 10 },
  ],
};

// soak-test.js
export const options = {
  stages: [
    { duration: '5m',  target: 50 },
    { duration: '4h',  target: 50 },
    { duration: '5m',  target: 0 },
  ],
};
```

## Snippet de `options.thresholds` (Moderate, default)

```javascript
thresholds: {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed:   ['rate<0.01'],
  checks:            ['rate>0.95'],
},
```

Los valores de thresholds varían según el tier — ver `[[k6-thresholds-three-tiers]]`.
