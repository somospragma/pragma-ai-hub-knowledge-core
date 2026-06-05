// {{project_name}} — workloads/estres.js
// Workload de Estres: 200-300% del peak esperado, progresivo.
// Objetivo: encontrar el punto de quiebre y validar degradacion controlada.
// Executor: ramping-arrival-rate (control de QPS, no de VUs).
//
// Por que ramping-arrival-rate y no ramping-vus:
//   - Si el backend se degrada, ramping-vus baja el QPS efectivo (VUs esperando).
//   - ramping-arrival-rate mantiene la presion declarada aunque la latencia explote.
//   - preAllocatedVUs ~ rate * latencia_p95_segundos. maxVUs >> preAllocatedVUs para soportar degradacion.

import { thresholdsEstres } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    estres: {
      executor: 'ramping-arrival-rate',
      startRate: 50,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      maxVUs: 500,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '5m', target: 300 },
        { duration: '5m', target: 500 },
        { duration: '3m', target: 50 },
      ],
      tags: { scenario: 'estres' },
    },
  },
  thresholds: thresholdsEstres,
};
