// {{project_name}} — helpers compartidos
//
// uuidv4() RFC 4122 v4
// getDefaultHeaders() respetando auth_mode (spec/external)
// buildXxxBody() por cada endpoint con request body
//
// Reglas:
//   - Payloads usan randomIntBetween / Math.random para variabilidad realista (no constantes).
//   - Nunca devolver el mismo body en cada iteracion: VUs con payloads identicos generan
//     cache hits artificiales y enmascaran latencia real.

import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import { config } from './config.js';

export function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

export function getDefaultHeaders() {
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Transaction-Id': uuidv4(),
    'X-Correlation-Id': uuidv4(),
    'Channel': config.channels[Math.floor(Math.random() * config.channels.length)],
    // 'Authorization': `Bearer ${config.authToken}`, // descomentar segun auth_mode
  };
}

// Ejemplo canonico: buildCreateUserBody. Reemplazar por buildXxxBody por endpoint del spec.
export function buildCreateUserBody() {
  return {
    email: `test+${Math.random().toString(36).substring(7)}@example.com`,
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(randomIntBetween(1_000_000_000, 9_999_999_999)),
    age: randomIntBetween(18, 80),
  };
}
