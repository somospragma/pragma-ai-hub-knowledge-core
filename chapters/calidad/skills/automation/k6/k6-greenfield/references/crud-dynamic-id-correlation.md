
# Correlación dinámica de IDs en flujos CRUD

**MANDATORIO**: en cualquier flujo CRUD detectado, el ID que consumen GET/PUT/DELETE proviene del response del POST. Hardcodear IDs está prohibido.

## Detección CRUD

1. Normaliza el path recortando `/{param}` final (`/users/{id}` → `/users`).
2. Agrupa endpoints por path base normalizado.
3. Clasifica el grupo:
   - `full` si contiene POST + GET + DELETE.
   - `partial` si contiene ≥2 métodos sobre el mismo base path.

## Prioridad de detección del campo ID

Buscar en este orden y usar el primero presente:

1. `id`, `Id`, `ID`, `_id` en root del response.
2. `data.id`, `data.Id`, `data.ID`, `data._id`.

## Patrón obligatorio

```javascript
import http from 'k6/http';
import { check } from 'k6';
import { config } from './config.js';
import { getDefaultHeaders, buildCreateResourceBody } from './utils.js';

export default function () {
  const headers = getDefaultHeaders();

  // POST — crea y captura el ID
  const createRes = http.post(
    `${config.baseUrl}/resources`,
    JSON.stringify(buildCreateResourceBody()),
    { headers }
  );
  check(createRes, {
    'POST status is 201': (r) => r.status === 201,
    'POST returns id':    (r) => !!(r.json('id') || r.json('data.id')),
  });

  const resourceId = createRes.json('id') || createRes.json('data.id');

  // Guard clause (MANDATORIO)
  if (!resourceId) {
    console.warn('Failed to capture resourceId, skipping dependent operations');
    return;
  }

  // GET — usa ID dinámico
  const getRes = http.get(`${config.baseUrl}/resources/${resourceId}`, { headers });
  check(getRes, { 'GET status is 200': (r) => r.status === 200 });

  // PUT — usa ID dinámico
  const putRes = http.put(
    `${config.baseUrl}/resources/${resourceId}`,
    JSON.stringify({ name: 'updated' }),
    { headers }
  );
  check(putRes, { 'PUT status is 200': (r) => r.status === 200 });

  // DELETE — usa ID dinámico (cierra el ciclo)
  const delRes = http.del(`${config.baseUrl}/resources/${resourceId}`, null, { headers });
  check(delRes, { 'DELETE status is 204': (r) => r.status === 204 });
}
```

## Por qué es obligatorio

- **Data pollution**: IDs hardcoded dejan registros stale en la BD y referencias rotas en corridas siguientes.
- **Concurrency conflicts**: múltiples VUs operando sobre el mismo ID generan colisiones y falsos negativos.
- **Environment portability**: un ID válido en QA no existe en staging ni en prod; el script se rompe al cambiar de ambiente.
- **False baselines**: hits sobre datos cacheados generan latencias artificialmente bajas y enmascaran problemas reales.
- **Audit failure**: en sistemas con auditoría trazable (compliance, sectores regulados — financiero, salud, gobierno, IoT life-safety), operar siempre sobre el mismo ID es trazabilidad inaceptable.
