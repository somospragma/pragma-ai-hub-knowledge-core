
# Thresholds — Tres tiers

K6 expone `options.thresholds` para definir criterios de pass/fail por métrica. Aplica uno de los tres tiers según el contexto del servicio.

## Tabla maestra

| Tier | Contexto típico | P95 | P99 | Error rate | Checks pass |
|---|---|---|---|---|---|
| Conservative | Sistemas mission-critical con SLA estricto: transacciones financieras, salud (EHR, prescripción), identidad/autenticación, life-safety IoT, gaming live, checkout en peak | <500 ms | <1000 ms | <0.001 | >0.99 |
| **Moderate (DEFAULT)** | APIs de negocio normales | <1000 ms | <2000 ms | <0.01 | >0.95 |
| Relaxed | Servicios internos, no críticos | <2000 ms | <5000 ms | <0.05 | >0.90 |

## Derivación del tier

1. Si `user_story` declara un SLA explícito (P95 o tiempo máximo), usa ese SLA.
2. Si no hay SLA en la historia pero la `firma` (perfil del cliente) lo declara, usa el de la firma.
3. Si ninguno aplica, usa **Moderate** por default.
4. Tras la primera corrida real de smoke, **calibra** con `[[calibrate-k6-thresholds]]` para alinear los thresholds al baseline observado.

## Snippet por tier

```javascript
// Conservative — sistemas mission-critical (financiero, salud, identidad, life-safety)
thresholds: {
  http_req_duration: ['p(95)<500',  'p(99)<1000'],
  http_req_failed:   ['rate<0.001'],
  checks:            ['rate>0.99'],
},

// Moderate (DEFAULT)
thresholds: {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed:   ['rate<0.01'],
  checks:            ['rate>0.95'],
},

// Relaxed — servicios internos
thresholds: {
  http_req_duration: ['p(95)<2000', 'p(99)<5000'],
  http_req_failed:   ['rate<0.05'],
  checks:            ['rate>0.90'],
},
```

## Requerimiento

Los thresholds generados desde un spec sin baseline real son una estimación. Es **obligatorio** recalibrar después del primer smoke con datos reales del servicio (workflow `[[calibrate-k6-thresholds]]`). Documenta el tier elegido y la justificación en el `README.md` del proyecto.
