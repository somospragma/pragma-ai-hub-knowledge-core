# GraphQL API — Patrones y Adaptación

## Patrones canónicos

- **Operaciones**: `query` (lectura), `mutation` (escritura), `subscription` (push vía WebSocket / SSE). Cada una requiere tests con assertions diferentes — las subscriptions requieren un cliente que mantenga la conexión.
- **Introspección**: en producción debe estar deshabilitada (`introspection: false` en Apollo). Validar con `{ __schema { types { name } } }` y esperar `400`/`403` en prod-like. En dev/QA suele estar habilitada para el tooling.
- **N+1**: la query `users { posts { comments } }` puede disparar N+1 SQL queries si no hay DataLoader. Validar con APM (Apollo Studio, NewRelic) que el número de queries no escale linealmente con el tamaño del result set.
- **Complexity limits**: límite de profundidad (depth limit, p. ej. 7) y costo de query (query cost analysis con `graphql-query-complexity`). Validar que una query maliciosamente profunda sea rechazada con `400`/`429`.
- **Persisted queries**: el cliente envía un hash y el servidor resuelve la query del whitelist. Reduce surface de ataque. Validar que queries no registradas sean rechazadas en producción.
- **Errores**: GraphQL responde `200 OK` con `errors[]` en el body — incluso en fallos. Las assertions deben revisar `errors` además del status HTTP.

## Framework primario

**Karate** con request bodies GraphQL (es JSON sobre HTTP). Alternativa: **postman-newman** con colecciones GraphQL. Para validar el schema-only sin runtime: **EasyGraphQL** y **graphql-inspector** (schema diff).

```gherkin
@graphql
Scenario: query user con sus posts
  Given path '/graphql'
  And request { query: 'query($id: ID!){ user(id:$id){ id name posts{ id title } } }', variables: { id: '#(userId)' } }
  When method post
  Then status 200
  And match response.data.user.id == userId
  And match response.errors == '##null'
```

## Complementarios

- **k6** para perf con queries dinámicas (variar `variables` por iteración). Para subscriptions: `k6/ws` o `xk6-graphql`.
- **Apollo Studio Tracing** / **Apollo Sandbox** para análisis de resolvers.
- **graphql-inspector** para schema diff y breaking change detection en CI.
- **GraphQL Armor** para reglas de seguridad (depth, cost, alias, directive limits).

## Antipatrones

- Validar solo el status HTTP `200` sin revisar `response.errors` — un error de GraphQL devuelve `200` con `errors[]`.
- No probar N+1: una mutation rápida en dev puede colapsar en prod por explosión de queries SQL.
- Dejar introspección habilitada en prod.
- Tratar GraphQL como REST y crear un test por endpoint resolver — el modelo es operación, no recurso.
