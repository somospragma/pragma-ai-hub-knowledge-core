// {{project_name}} — workloads/carga.js
// Workload de Carga: 100% del peak esperado.
// Objetivo: validar SLAs bajo carga nominal sostenida.
// Executor: ramping-vus (rampa progresiva hasta peak, sostener, descender).

import { thresholdsCarga } from '../shared/thresholds.js';

export const options = {
  scenarios: {
    carga: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m',  target: 10 },
        { duration: '5m',  target: 30 },
        { duration: '10m', target: 50 },
        { duration: '3m',  target: 0 },
      ],
      tags: { scenario: 'carga' },
    },
  },
  thresholds: thresholdsCarga,
};
