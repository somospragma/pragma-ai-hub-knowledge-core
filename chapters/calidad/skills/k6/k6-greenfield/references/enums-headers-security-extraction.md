
# Extracción de enums, headers y security desde el spec

Insumos para generar `config.js` y `utils.js`. Todos se extraen del spec; nada se inventa.

## Enums

- **Top-level**: `components.schemas.{Schema}.enum` → array de valores.
- **Property-level**: `components.schemas.{Schema}.properties.{field}.enum` → array de valores.

Cada enum se vuelve un array en `config.js`. El nombre del array es el plural en camelCase del campo (ej. `documentName` → `documentNames`).

```javascript
// En config.js
documentNames: ['CC', 'TI', 'CE'],
channels: ['APP', 'WEB'],
```

## Headers requeridos

Por endpoint, recorrer `parameters[*]` con `in: header` y `required: true`. Agregar al `getDefaultHeaders()` los headers transversales (los que aparecen en la mayoría de endpoints). Headers puntuales de un solo endpoint se inyectan en el test que lo use.

Mapeo de nombres: header con guiones a camelCase para la clave en `config.js`:

| Header HTTP | Clave en config.js |
|---|---|
| `X-Request-Id` | `xRequestId` |
| `X-Correlation-Id` | `xCorrelationId` |
| `True-Client-Ip` | `trueClientIp` |

## Security schemes

Extraer de:

- OpenAPI 3.x: `components.securitySchemes`.
- Swagger 2.0: `securityDefinitions`.

Si el spec NO declara security (ningún scheme ni `security` global / por operación):

- **NO** incluir `authToken` en `config.js`.
- **NO** incluir `Authorization` en `getDefaultHeaders()`.
- **NO** generar `auth.setup` ni helpers de token.

Si el spec SÍ declara security:

- Agregar `authToken: __ENV.AUTH_TOKEN || ''` en `config.js`.
- Agregar `'Authorization': \`Bearer ${config.authToken}\`` en `getDefaultHeaders()`.

## Naming convention

- Claves de objeto y variables: `camelCase` (`xRequestId`, `documentNames`).
- Function names de payload builders: `build` + PascalCase del `operationId` o del recurso. Ejemplos:
  - `operationId: create_user` → `buildCreateUserBody()`.
  - `operationId: updateOrderStatus` → `buildUpdateOrderStatusBody()`.

## Modo external-auth (override)

El comportamiento default ("spec drives auth") cubre microservicios cuya OpenAPI declara explícitamente `securitySchemes`. En entornos reales —típicamente arquitecturas con API gateway, IdP externo (Cognito/Keycloak/Okta/Auth0), mTLS o request signing— esa premisa falla a menudo: el spec sólo describe el contrato funcional del microservicio aguas arriba del gateway y no incluye los mecanismos de autenticación que sí se aplican en producción y en los ambientes de performance.

### Trigger

Activa este modo cuando se cumpla **cualquiera** de las siguientes condiciones:

- El usuario pasa el input `auth_mode: external` al workflow / skill.
- La variable de entorno `EXTERNAL_AUTH=true` está presente cuando se invoca la generación.

Cualquier otro caso mantiene el comportamiento por defecto (spec-driven).

### Comportamiento en este modo

- **Siempre** incluir `authToken: __ENV.AUTH_TOKEN || ''` en `config.js`, incluso si el spec NO declara `security`.
- **Siempre** incluir `'Authorization': \`Bearer ${config.authToken}\`` dentro de `getDefaultHeaders()`.
- Documentar en el `README.md` del proyecto que `AUTH_TOKEN` es **obligatorio** en runtime (el token se obtiene out-of-band y se inyecta como env var; los tests no resuelven el flujo de login).
- No se genera `auth.setup` ni helpers de token: el token es responsabilidad del operador/CI.

### Cuándo usarlo

Casos legítimos en los que el spec NO refleja la autenticación real:

- **API gateway por delante del microservicio**: AWS API Gateway, Kong, Apigee, etc. validan el token antes de llegar al servicio; el spec del servicio aguas abajo no declara `security` porque internamente confía en el gateway.
- **Token emitido por IdP externo**: Cognito, Keycloak, Okta, Auth0. El flujo de obtención del token vive fuera del scope del microservicio.
- **AWS SigV4 / JWS request signing**: la firma se calcula en un middleware/sidecar y no se modela en OpenAPI.
- **mTLS**: la autenticación es a nivel de transporte; el spec no la describe.
- **Tokens obtenidos out-of-band por el equipo de performance**: el QA performance recibe un token corto-vivo del equipo de seguridad, lo inyecta en `AUTH_TOKEN` y corre la suite.

### Implicancias de seguridad

- Los tokens nunca se hardcodean: viven sólo en `__ENV.AUTH_TOKEN`.
- En CI, `AUTH_TOKEN` se inyecta como secret enmascarado; nunca se imprime en logs.
- Si el modo external-auth se activa por error en un proyecto donde el spec sí declara security, el resultado es funcionalmente equivalente (Authorization se incluye igual); el riesgo es informativo, no de seguridad.

## Regla crítica

Por defecto, si el spec NO tiene security, no agregues `Authorization`. Excepción: modo external-auth explícito (input `auth_mode: external` o env `EXTERNAL_AUTH=true`). En ese caso, `authToken` y `Authorization` se incluyen siempre y `AUTH_TOKEN` se documenta como obligatorio en el README. El skill `[[k6-greenfield]]` valida ambas ramas en su checklist DoD.
