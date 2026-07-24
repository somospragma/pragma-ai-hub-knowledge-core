
# CRUD stateful — data buckets y correlación de IDs

El caso que rompe a los mocks simples: el test crea un recurso (`POST`), captura el `id` de la respuesta y lo usa en el `GET/PUT/DELETE` siguiente. Con respuestas estáticas ese flujo es imposible. Mockoon lo resuelve con **CRUD routes + data buckets**.

## Data buckets

Un bucket es un key-value store **en memoria** generado al arrancar el server; su estado persiste durante toda la vida del proceso y **se comparte entre todas las rutas**. Se define en `data[]` del environment:

```json
{
  "data": [
    {
      "uuid": "d1b1a1c1-0000-4000-8000-000000000001",
      "id": "usrs",
      "name": "users",
      "value": "[\n  {{#repeat 5}}\n  { \"id\": \"{{uuid}}\", \"email\": \"{{faker 'internet.email'}}\", \"status\": \"ACTIVE\" }\n  {{/repeat}}\n]"
    }
  ]
}
```

El contenido soporta templating (se evalúa una sola vez, al arranque). Con `--faker-seed` fijo, el dataset inicial es **idéntico en cada arranque** — determinismo garantizado.

## CRUD routes

Una ruta `type: "crud"` con endpoint `users` ligada al bucket autogenera:

| Operación | Comportamiento |
|---|---|
| `GET /users` | Lista con paginación `?page=&limit=` (default 10), orden `?sort=&order=`, búsqueda `?search=`, filtros `campo_eq/_ne/_gt/_gte/_lt/_lte/_like=`; headers `X-Total-Count` y `X-Filtered-Count` |
| `GET /users/:id` | Recurso por id, 404 si no existe |
| `POST /users` | Crea; si el body no trae id, autogenera (UUID v4, o autoincremento si los ids del bucket son numéricos) |
| `PUT /users/:id` | Reemplazo completo |
| `PATCH /users/:id` | Merge parcial |
| `DELETE /users/:id` | Elimina |

El campo clave es configurable con `crudKey` (default `id`; soporta dot-notation como `data.id` para respuestas envueltas). Se pueden sobreescribir operaciones puntuales declarando una ruta `http` encima en el orden de rutas (ej. un `DELETE` que debe responder 409 por regla de contrato).

Con esto, el flujo Karate `POST → capturar id → GET → DELETE` y la guard clause de correlación dinámica de K6 (ver [[calidad-k6-greenfield]], `references/crud-dynamic-id-correlation.md`) funcionan contra el mock exactamente igual que contra el SUT real.

## Reset de estado entre corridas (obligatorio para determinismo)

El estado de los buckets sobrevive entre tests dentro del mismo proceso. Para que cada corrida arranque del mismo estado, purgar vía Admin API en el setup de la suite (o reiniciar el proceso):

```bash
curl -X POST http://localhost:3010/mockoon-admin/state/purge \
  -H "Authorization: Bearer $MOCKOON_ADMIN_API_TOKEN"
```

`state/purge` resetea buckets, variables globales, contador de requests y logs. El token se fija con `--admin-api-token` (o env `MOCKOON_ADMIN_API_TOKEN`); si no se define, Mockoon genera uno aleatorio y lo imprime en logs. Hook por stack: Karate `Setup.feature` con `callonce`, K6 `setup()`, Playwright `globalSetup` — los mismos puntos donde `[[calidad-test-data-management]]` ancla seeding/cleanup.

## Correlación entre rutas no-CRUD

Para flujos que cruzan rutas sin bucket (ej. `POST /auth/login` devuelve un token que `GET /profile` espera), usar variables globales del templating:

- En la respuesta del login: `{{setGlobalVar 'sessionToken' (uuid)}}`
- En rutas posteriores: `{{getGlobalVar 'sessionToken'}}` en el body, o una rule sobre variable global para discriminar autenticado vs no.

Las variables globales también se purgan con `state/purge`.
