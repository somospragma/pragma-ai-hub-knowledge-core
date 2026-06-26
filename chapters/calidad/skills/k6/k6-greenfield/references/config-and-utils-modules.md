
# Módulos compartidos — `config.js` y `utils.js`

Todo proyecto K6 separa configuración (constantes, env vars, enums) de utilidades (UUID, headers, payload builders). Los tests importan ambos y nunca declaran headers o payloads inline.

El contenido exacto depende del **modo de autenticación** elegido. Hay dos modos soportados:

| Modo | Trigger | `authToken` en `config.js` | `Authorization` en `getDefaultHeaders()` | `AUTH_TOKEN` env var | Cuándo usar |
|---|---|---|---|---|---|
| `spec` (default) | Sin input explícito. El spec **sí** declara `security` → se incluye; si no, se omite. | Solo si el spec define `security`. | Solo si el spec define `security`. | Requerida solo si el spec define `security`. | Microservicios cuyo OpenAPI describe completa y fielmente su autenticación. |
| `external` (override) | Input `auth_mode: external` o env `EXTERNAL_AUTH=true`. | **Siempre** incluido. | **Siempre** incluido. | **Obligatoria** (documentar en README). | Gateway delante del servicio, IdP externo (Cognito/Keycloak/Okta), AWS SigV4 / JWS, mTLS, tokens out-of-band. |

Detalle del modo y rationale en ``enums-headers-security-extraction.md``.

## `tests/config.js` — Modo `spec` (default)

```javascript
export const config = {
  baseUrl: __ENV.BASE_URL || 'http://localhost:8080',
  // SOLO si el spec declara security (components.securitySchemes / securityDefinitions)
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraídos del spec (top-level y property-level)
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  // Valores constantes de headers
  trueClientIp: '192.168.1.100',
};
```

Reglas:
- `baseUrl` siempre desde `__ENV.BASE_URL` con fallback local.
- `authToken` SOLO si el spec define `security`. Si no, omitir la propiedad.
- Los arrays de enums se generan a partir de `schema.enum` (top-level) o `properties.{field}.enum` (property-level). Ver ``enums-headers-security-extraction.md``.

## `tests/config.js` — Modo `external` (override)

```javascript
export const config = {
  baseUrl: __ENV.BASE_URL || 'http://localhost:8080',
  // SIEMPRE incluido: el token viene de un IdP/gateway externo al spec.
  authToken: __ENV.AUTH_TOKEN || '',

  // Enums extraídos del spec
  documentNames: ['CC', 'TI', 'CE'],
  channels: ['APP', 'WEB'],

  trueClientIp: '192.168.1.100',
};
```

Reglas:
- `authToken` se incluye aunque el spec NO tenga `security`.
- `AUTH_TOKEN` debe documentarse como **obligatoria** en el README; sin ella todos los requests se enviarán con `Authorization: Bearer ` (vacío) y la API responderá 401.
- Resto de reglas idéntico al modo `spec`.

## `tests/utils.js` — Modo `spec` (default)

```javascript
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
    // 'Authorization': `Bearer ${config.authToken}`, // SOLO si spec.security
  };
}

export function buildCreateUserBody() {
  // Campos exactos del spec — no inventar
  return {
    email: 'test+' + Math.random().toString(36).substring(7) + '@example.com',
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(Math.floor(Math.random() * 1e10)),
  };
}
```

## `tests/utils.js` — Modo `external` (override)

```javascript
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
    // Modo external-auth: Authorization siempre incluido. AUTH_TOKEN obligatorio en runtime.
    'Authorization': `Bearer ${config.authToken}`,
  };
}

export function buildCreateUserBody() {
  return {
    email: 'test+' + Math.random().toString(36).substring(7) + '@example.com',
    documentName: config.documentNames[Math.floor(Math.random() * config.documentNames.length)],
    documentNumber: String(Math.floor(Math.random() * 1e10)),
  };
}
```

Reglas generales (ambos modos):
- `uuidv4()` RFC 4122 v4 (la versión es el `4` literal y el variant es `8|9|a|b`).
- `getDefaultHeaders()` incluye Content-Type, Accept, headers de UUID/correlation/transaction generados, enum random. `Authorization` se incluye según el modo.
- Un `buildXxxBody()` por cada endpoint con request body; el sufijo es PascalCase derivado del `operationId` (ver ``enums-headers-security-extraction.md``).
