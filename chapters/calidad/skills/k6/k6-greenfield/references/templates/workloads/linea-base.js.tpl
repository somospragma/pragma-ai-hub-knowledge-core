// {{project_name}} — workloads/linea-base.js
// Workload de Linea Base: 20-30% del peak esperado.
// Objetivo: validar el flow + baseline de latencia bajo carga minima.
// Executor: ramping-vus (rampa progresiva, control de concurrencia).

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
