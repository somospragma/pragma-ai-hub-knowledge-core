// {{project_name}} — scenarios/{{endpoint_name}}.js
// Flow HTTP reusable para el endpoint objetivo. NO define options.
// El workload (workloads/*.js) decide la curva de carga.
//
// Slots:
//   {{endpoint_name}}  — nombre logico (e.g. retrieveTransactions, createUser)
//   {{path}}           — path relativo (e.g. /transactions, /users/{id})
//   {{method}}         — get | post | put | del | patch
//   {{checks}}         — checks especificos del endpoint

import http from 'k6/http';
import { group, check, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from '../shared/config.js';
import { getAuthHeaders } from '../shared/utils.js';
// import { login } from './auth.js'; // descomentar si el endpoint requiere auth previa

export default function () {
  // const { token } = login(); // opcional, solo si el flow requiere auth dinamica por iteracion

  group('{{endpoint_name}}', () => {
    const res = http.{{method}}(
      `${config.baseUrl}{{path}}`,
      // null, // payload: usar JSON.stringify(buildXxxBody()) para POST/PUT/PATCH
      {
        headers: getAuthHeaders(),
        tags: { endpoint: '{{endpoint_name}}', step: 'main' },
      },
    );

    check(res, {
      'status 200': (r) => r.status === 200,
      // {{checks}} — agregar checks especificos del contrato (campos requeridos, tipos, rangos)
    }, { endpoint: '{{endpoint_name}}', step: 'main' });

    sleep(randomIntBetween(1, 3));
  });
}
