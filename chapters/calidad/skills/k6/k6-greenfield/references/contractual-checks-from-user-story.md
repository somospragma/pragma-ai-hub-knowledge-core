# Checks contractuales derivados del `user_story`

Un check K6 no debe limitarse a validar `status === 200` ni `body.length > 0`. Esas validaciones son demasiado débiles: un endpoint puede responder 200 con `{}` o `null` y aprobar el check, pero violar el contrato del dominio. Cada check debe validar el contrato declarado por el `user_story` y el schema de respuesta del spec.

## Regla

Por cada endpoint, derivar los checks contractuales mínimos a partir de:

1. El `user_story` (qué información necesita el consumidor).
2. El schema de respuesta del spec (qué campos garantiza el contrato).
3. Las RNF (p.ej. paginación, ordenamiento, formato de fecha).

Cada response tipo `dict`/`object` lleva al menos un check de status, un check de presencia de campo clave y un check de tipo o invariante del campo clave.

## Checks contractuales mínimos por tipo de respuesta

### Listados paginados

Validar la estructura `data` + `metadata` (o equivalente del spec):

```javascript
check(res, {
  'status is 200':                  (r) => r.status === 200,
  'data is array':                  (r) => Array.isArray(r.json('data')),
  'metadata.totalItems >= 0':       (r) => Number.isFinite(r.json('metadata.totalItems')) && r.json('metadata.totalItems') >= 0,
  'metadata.totalPages >= 0':       (r) => Number.isFinite(r.json('metadata.totalPages')) && r.json('metadata.totalPages') >= 0,
  'metadata.currentPage >= 1':      (r) => Number.isFinite(r.json('metadata.currentPage')) && r.json('metadata.currentPage') >= 1,
  'data length <= pageSize':        (r) => r.json('data').length <= (r.json('metadata.pageSize') || Infinity),
}, { endpoint: 'listTransactions', step: 'main', scenario: __ENV.SCENARIO_NAME });
```

### Transacciones (objeto de dominio)

Validar campos clave del dominio:

```javascript
check(res, {
  'status is 200':            (r) => r.status === 200,
  'has transactionId':        (r) => typeof r.json('transactionId') === 'string' && r.json('transactionId').length > 0,
  'amount is number':         (r) => typeof r.json('amount') === 'number',
  'currency is ISO 4217':     (r) => typeof r.json('currency') === 'string' && /^[A-Z]{3}$/.test(r.json('currency')),
  'status is valid enum':     (r) => ['PENDING', 'COMPLETED', 'FAILED', 'REVERSED'].includes(r.json('status')),
}, { endpoint: 'getTransaction', step: 'main', scenario: __ENV.SCENARIO_NAME });
```

### Auth

Validar `access_token` no vacío y `expires_in` numérico positivo:

```javascript
check(res, {
  'status is 200':                  (r) => r.status === 200,
  'has access_token':               (r) => typeof r.json('access_token') === 'string' && r.json('access_token').length > 0,
  'token_type is Bearer':           (r) => r.json('token_type') === 'Bearer',
  'expires_in positive number':     (r) => Number.isFinite(r.json('expires_in')) && r.json('expires_in') > 0,
}, { endpoint: 'auth', step: 'auth', scenario: __ENV.SCENARIO_NAME });
```

### CRUD POST (creación de recurso)

Validar que la respuesta retorna el identificador del recurso creado:

```javascript
check(res, {
  'status is 201':            (r) => r.status === 201,
  'response has id':          (r) => typeof r.json('id') === 'string' && r.json('id').length > 0,
  'location header set':      (r) => typeof r.headers['Location'] === 'string' && r.headers['Location'].length > 0,
}, { endpoint: 'createUser', step: 'main', scenario: __ENV.SCENARIO_NAME });
```

El check `response has id` es lo que permite el ``crud-dynamic-id-correlation.md``: sin id correlacionado, GET/PUT/DELETE quedan sin sujeto.

### CRUD DELETE

```javascript
check(res, {
  'status is 204':            (r) => r.status === 204,
  'body is empty':            (r) => r.body === '' || r.body === null,
}, { endpoint: 'deleteUser', step: 'cleanup', scenario: __ENV.SCENARIO_NAME });
```

## Tabla de patrones HU → checks

| Patrón en `user_story`                                                     | Checks contractuales derivados                                                                                            |
|----------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| "Como usuario quiero listar mis transacciones paginadas"                   | `data` array, `metadata.totalItems/totalPages/currentPage`, `data.length <= pageSize`                                     |
| "Como usuario quiero ver el detalle de una transacción por id"             | `transactionId`, `amount`, `currency`, `status` enum válido                                                               |
| "Como sistema quiero autenticar contra el IdP y obtener un token"          | `access_token` no vacío, `token_type === 'Bearer'`, `expires_in` numérico positivo                                        |
| "Como usuario quiero crear un recurso"                                     | status 201, `id` no vacío en response, `Location` header presente                                                         |
| "Como usuario quiero eliminar un recurso"                                  | status 204, body vacío                                                                                                    |
| "Como consumidor quiero recibir las transacciones ordenadas por fecha desc"| `data[0].createdAt >= data[1].createdAt` (si `data.length >= 2`)                                                          |
| "El campo `accountNumber` debe estar enmascarado"                          | `/^[*X]+\d{4}$/.test(r.json('data.0.accountNumber'))`                                                                     |
| "Las respuestas no deben exponer PII"                                      | `!('email' in r.json('data.0'))`, `!('document' in r.json('data.0'))` (lista por dominio)                                 |

## Anti-pattern explícito

```javascript
// MAL: el check pasa con cualquier 200, incluido { } o null
check(r, {
  'status is 200': r => r.status === 200,
  'has body':      r => r.body.length > 0,
});
```

Consecuencia: un endpoint que responde 200 con `{}` aprueba el check, pero el consumidor recibe un payload inútil. El test pasa, el SLA aparenta cumplirse, y el bug llega a producción.

## Reglas de oro

- Cada check produce 1 línea con tags. NO consolidar 5 validaciones en un solo callback `r => r.status === 200 && ...` — k6 reporta `checks` por entrada del objeto, agrupar oculta cuál validación falló.
- Si el spec declara `required: [...]`, todos los campos `required` deben tener un check de presencia.
- Si el spec declara `enum: [...]`, validar pertenencia al enum.
- Si el spec declara `format: date-time`, validar parseabilidad: `!Number.isNaN(Date.parse(r.json('createdAt')))`.
- Si el `user_story` cita una invariante (orden, máscara, ausencia de PII), agregar el check correspondiente.

## Cross-links

- `[[calidad-k6-greenfield]]`
- ``enums-headers-security-extraction.md``
- ``crud-dynamic-id-correlation.md``
- ``tag-policy-and-metrics-isolation.md``
- ``availability-metric-from-rnf.md``
- `[[calidad-pre-generation-protocol]]`
- `[[calidad-post-generation-protocol]]`
- `[[calidad-delivery-gate-contract]]`
