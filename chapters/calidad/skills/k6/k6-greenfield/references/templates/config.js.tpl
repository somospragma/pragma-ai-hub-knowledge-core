// {{project_name}} — configuracion compartida
//
// Slots dependientes del spec:
//   {{baseUrl}}             — URL base por default (puede sobrescribirse con BASE_URL).
//   {{enumArrays}}           — arrays generados desde schema.enum / properties.{f}.enum.
//   {{constantHeaders}}      — valores constantes de headers (e.g. True-Client-IP).
//
// Reglas:
//   - baseUrl SIEMPRE desde __ENV.BASE_URL con fallback local.
//   - authToken SOLO si auth_mode='spec' y el spec declara security, o si auth_mode='external'.
//   - Nunca hardcodear credenciales o URLs en los tests/*.js — solo aqui o via __ENV.

export const config = {
  baseUrl: __ENV.BASE_URL || '{{baseUrl}}',
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraidos del spec (top-level y property-level)
  // {{enumArrays}} — placeholder a expandir por el generador.
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  // Valores constantes de headers documentados en el spec
  trueClientIp: '192.168.1.100',
};
