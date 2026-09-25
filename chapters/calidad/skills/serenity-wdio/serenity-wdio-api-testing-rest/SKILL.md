---
id: serenity-wdio-api-testing-rest
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Implementar pruebas de API REST con @serenity-js/rest sobre Screenplay Pattern. Cubre setup de CallAnApi, Tasks con Send/GetRequest/PostRequest/PutRequest/DeleteRequest/PatchRequest, ChangeApiConfig, LastResponse, extracción tipada, encadenamiento de requests y autenticación.
tags: [serenity-wdio, api-testing, serenity-js-rest, http, callAnApi, screenplay, typescript]
---

## Instrucción

Este skill aplica cuando el modo de ejecución es `api` y el config activo es `configs/wdio.api.conf.ts`. El actor obtiene la ability `CallAnApi` mediante `whoCan(...)` en el step `Given`, usando el `baseUrl` declarado en el config como fuente del valor (nunca hardcoded). El `baseUrl` en `wdio.api.conf.ts` **no otorga la ability por sí solo** — es necesario declarar `runner: '@serenity-js/webdriverio'` en `wdio.shared.conf.ts` para que el adapter oficial otorgue `CallAnApi` de forma implícita a todos los actores; si el proyecto usa el `runner: 'local'` por defecto de WebdriverIO (el caso más común y el que genera este skill), el `whoCan(...)` explícito en el `Given` es obligatorio. Ver `references/actor-setup-verificado.md` para el detalle y la verificación de ambos caminos.

### Stack del proyecto

- `@serenity-js/rest@^3.31.10` (cliente HTTP basado en axios)
- `@serenity-js/assertions` para `Ensure.that(...)`
- `@serenity-js/webdriverio@^3.31.10` (requerida en `package.json` aunque no se declare `runner: '@serenity-js/webdriverio'`; sin ella el proyecto no compila porque `@serenity-js/core` la referencia como peer)
- Config en `configs/wdio.api.conf.ts` con `baseUrl: process.env.API_BASE_URL`
- Features en `features/api/Features/*.feature`
- Tasks en `features/api/Tasks/`
- Questions en `features/api/Questions/`
- Steps en `features/step-definitions/api/`

### Setup del actor (patrón verificado del proyecto)

```typescript
import { actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

Given('que {actor} consume el servicio API', async (actor: Actor) => {
  actorCalled(actor.name).whoCan(
    CallAnApi.at(process.env.API_BASE_URL || ''),
  );
});
```

Este `whoCan(...)` en el `Given` es el patrón que garantiza que el actor tenga `CallAnApi` sin depender del `runner` configurado. Es idempotente: si se repite en varios escenarios, no falla ni duplica la ability.

### Plantilla GET

```typescript
import { Task } from '@serenity-js/core';
import { GetRequest, Send } from '@serenity-js/rest';

export class ConsultarHealth {
  static delEndpoint = (endpoint: string) =>
    Task.where(
      `#actor consulta el endpoint ${ endpoint }`,
      Send.a(GetRequest.to(endpoint)),
    );
}
```

### Plantilla POST con body

```typescript
import { Task } from '@serenity-js/core';
import { PostRequest, Send } from '@serenity-js/rest';

export class CrearRecurso {
  static conBody = (endpoint: string, body: Record<string, unknown>) =>
    Task.where(
      `#actor crea un recurso en ${ endpoint }`,
      Send.a(PostRequest.to(endpoint).with(body)),
    );
}
```

### Aserción básica de status

```typescript
import { LastResponse } from '@serenity-js/rest';
import { Ensure, equals } from '@serenity-js/assertions';

await actor.attemptsTo(
  Ensure.that(LastResponse.status(), equals(200)),
);
```

### Anti-patrones

- Llamar `axios.get(...)` directo en steps.
- URLs hardcoded — usar `baseUrl` o `ChangeApiConfig.setUrlTo`.
- Validar el body sin tipar: `LastResponse.body() as any`.
- Esperas entre requests — HTTP es síncrono request/response.
- Encadenar requests sin `Ensure` del status intermedio.
- `Question.about` con efectos secundarios (debe ser pura lectura).
- Commitear tokens reales en `.env.api`.

Para el detalle completo de PUT/PATCH/DELETE, headers, query params, Questions tipadas, encadenamiento de requests, autenticación (Bearer/Basic), validación de schema con ajv, step definitions, timeouts y checklist de calidad, ver las referencias:

- `references/api-requests.md` — todas las variantes de request y configuración.
- `references/api-questions-assertions.md` — Questions, aserciones avanzadas y encadenamiento.
- `references/api-auth-y-estructura.md` — autenticación, estructura de carpetas, step definitions y timeouts.
