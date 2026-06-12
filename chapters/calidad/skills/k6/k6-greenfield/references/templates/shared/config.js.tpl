// {{project_name}} — shared/config.js
// Configuracion centralizada. Todos los modulos (scenarios, workloads, tests) la importan desde aqui.
//
// Reglas:
//   - baseUrl / authUrl SIEMPRE desde __ENV con fallback local.
//   - Nunca hardcodear credenciales en tests/*.js — solo aqui o via __ENV.
//   - Enums y headers constantes extraidos del spec se declaran aqui.

export const config = {
  baseUrl: __ENV.BASE_URL || '{{baseUrl}}',
  authUrl: __ENV.AUTH_URL || '{{authUrl}}',
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraidos del spec (top-level y property-level).
  // {{enumArrays}} — placeholder a expandir por el generador.
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  // Headers constantes documentados en el spec.
  trueClientIp: '192.168.1.100',
};
