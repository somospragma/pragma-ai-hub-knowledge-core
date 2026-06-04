// {{project_name}} — soak-test.js
// Proposito: estabilidad a largo plazo (memory leaks, drift, connection pools).
// VUs constante 50, duration 2h por default (rango 2-8h). Tier por default: Moderate.

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

import { config } from './config.js';
import { getDefaultHeaders, buildCreateUserBody } from './utils.js';

export const options = {
  stages: [
    { duration: '5m', target: 50 },
    { duration: '2h', target: 50 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
};

export default function () {
  let resourceId;

  group('users-crud', function () {
    const createRes = http.post(
      `${config.baseUrl}/users`,
      JSON.stringify(buildCreateUserBody()),
      { headers: getDefaultHeaders(), tags: { endpoint: 'POST /users', scenario: 'soak' } },
    );
    check(createRes, {
      'POST /users status is 201': (r) => r.status === 201,
    }, { endpoint: 'POST /users', scenario: 'soak' });

    try {
      resourceId = createRes.json('id');
    } catch (_e) {
      resourceId = undefined;
    }

    sleep(randomIntBetween(1, 5));

    if (!resourceId) {
      console.warn('soak: skipping GET/DELETE because resourceId is missing from POST response');
      return;
    }

    const getRes = http.get(
      `${config.baseUrl}/users/${resourceId}`,
      { headers: getDefaultHeaders(), tags: { endpoint: 'GET /users/{id}', scenario: 'soak' } },
    );
    check(getRes, {
      'GET /users/{id} status is 200': (r) => r.status === 200,
    }, { endpoint: 'GET /users/{id}', scenario: 'soak' });

    sleep(randomIntBetween(1, 5));

    const delRes = http.del(
      `${config.baseUrl}/users/${resourceId}`,
      null,
      { headers: getDefaultHeaders(), tags: { endpoint: 'DELETE /users/{id}', scenario: 'soak' } },
    );
    check(delRes, {
      'DELETE /users/{id} status is 204': (r) => r.status === 204,
    }, { endpoint: 'DELETE /users/{id}', scenario: 'soak' });
  });

  sleep(randomIntBetween(1, 5));
}

export function handleSummary(data) {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${timestamp}-summary.json`]: JSON.stringify(data, null, 2),
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
  };
}
