
# Formato del environment file de Mockoon

Cada mock es **un único archivo JSON autocontenido** (environment): servidor (port, hostname, TLS, CORS), headers globales, latencia, rutas, data buckets y callbacks. Es la fuente de verdad del mock y **se versiona en git** dentro del proyecto de tests, en `mocks/mockoon/environment.json`. Mockoon lo guarda pretty-printed, así que los diffs en PR son legibles.

## Estructura mínima

```json
{
  "uuid": "70d8639e-ef20-4d52-9749-c47d9ffc5c67",
  "lastMigration": 33,
  "name": "payments-api-mock",
  "endpointPrefix": "api",
  "latency": 0,
  "port": 3010,
  "routes": [
    {
      "uuid": "61ec2669-447e-4b55-a22b-2a1fda1e8da3",
      "method": "post",
      "endpoint": "payments",
      "type": "http",
      "responseMode": null,
      "responses": [
        {
          "uuid": "88b0679d-7a00-4875-8d29-e66eece1b539",
          "statusCode": 201,
          "body": "{ \"transactionId\": \"{{uuid}}\", \"status\": \"PENDING\" }",
          "latency": 0,
          "headers": [{ "key": "Content-Type", "value": "application/json" }],
          "rules": [],
          "rulesOperator": "OR",
          "bodyType": "INLINE",
          "databucketID": "",
          "crudKey": "id",
          "default": true,
          "fallbackTo404": false,
          "disableTemplating": false,
          "callbacks": []
        }
      ]
    }
  ],
  "proxyMode": false,
  "proxyHost": "",
  "cors": true,
  "headers": [{ "key": "Content-Type", "value": "application/json" }],
  "data": [],
  "callbacks": []
}
```

## Campos que importan al agente

| Campo | Semántica |
|---|---|
| `lastMigration` | Versión del schema interno. Si el CLI reporta archivo viejo, migrar con `mockoon-cli start --data ... --repair`. |
| `port` | Puerto del mock. Convención del chapter: `3010` para no chocar con frontends dev (`3000`). El CLI puede overridearlo con `--port`. |
| `routes[].type` | `http` (respuesta configurada), `crud` (persistencia stateful ligada a bucket, ver `stateful-crud-and-data-buckets.md`), `ws` (WebSocket). |
| `routes[].responses[]` | N respuestas por ruta; se selecciona por `rules` (default), `random` o `sequential` según `responseMode`. La respuesta con `default: true` responde cuando ninguna regla matchea. |
| `responses[].rules` | Discriminan por body (JSONPath/object-path), query param, header, cookie, route param, número de request o variable global. Operadores: equals, regex, null, array includes, valid JSON schema. Combinables AND/OR con inversión. |
| `responses[].latency` | Latencia por respuesta en ms (además de la global del environment). Útil para escenarios de timeout del test. |
| `bodyType` | `INLINE` (string en `body`), `FILE`, `DATABUCKET`. |
| `data[]` | Data buckets (estado compartido entre rutas). |
| `proxyMode` / `proxyHost` | Hybrid/partial mocking (ver `mock-vs-real-switchover.md` y el SKILL, paso 6). |

## Reglas de mantenimiento

- Un environment por SUT mockeado. Si la suite consume dos backends, dos data files y dos puertos (`mockoon-cli start --data a.json b.json --port 3010 3011`).
- El data file se regenera o se edita cuando el spec cambia; un mock desactualizado respecto al contrato produce falsos verdes. Tratar el diff del data file en PR con el mismo rigor que un cambio de test.
- No editar los `uuid` a mano; Mockoon los usa como identidad interna. Al generar el archivo por prompt, cada uuid debe ser único y estable (no regenerarlos en cada corrida, o el diff de git se vuelve ruido).
- Los escenarios de error del contrato (4xx/5xx declarados en el spec) se modelan como respuestas adicionales de la misma ruta con rules, no como rutas separadas.
