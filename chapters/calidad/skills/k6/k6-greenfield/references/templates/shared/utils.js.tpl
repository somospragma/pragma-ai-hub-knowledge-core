// {{project_name}} — shared/utils.js
// Helpers cross-cutting reutilizables por todos los scenarios.
//
// Exports:
//   - uuidv4()                     RFC 4122 v4 para Transaction-Id / Correlation-Id.
//   - getAuthHeaders()             headers default + Authorization si auth_mode lo requiere.
//   - getDefaultHeaders()          alias de getAuthHeaders para compatibilidad.
//   - randomIntBetween             re-export de la jslib oficial.
//   - buildXxxBody()               un builder por cada endpoint con request body.
//
// Reglas:
//   - Payloads usan randomIntBetween / Math.random para variabilidad realista.
//   - Nunca devolver el mismo body en cada iteracion: cache hits artificiales enmascaran latencia.

import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from './config.js';

export { randomIntBetween };

export function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function getAuthHeaders() {
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Transaction-Id': uuidv4(),
    'X-Correlation-Id': uuidv4(),
    'Channel': config.channels[Math.floor(Math.random() * config.channels.length)],
  };

  // Authorization solo si auth_mode='external' o el spec declara security.
  if (config.authToken) {
    headers['Authorization'] = `Bearer ${config.authToken}`;
  }

  return headers;
}

// Alias para compatibilidad con scenarios que usen el nombre historico.
export const getDefaultHeaders = getAuthHeaders;

// Ejemplo canonico: reemplazar por buildXxxBody() por cada endpoint con request body del spec.
export function buildCreateUserBody() {
  return {
    email: `test+${Math.random().toString(36).substring(7)}@example.com`,
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(randomIntBetween(1_000_000_000, 9_999_999_999)),
    age: randomIntBetween(18, 80),
  };
}
