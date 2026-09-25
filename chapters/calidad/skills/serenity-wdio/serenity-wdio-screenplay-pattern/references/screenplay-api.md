# Screenplay Pattern — Implementación API REST

## Imports correctos

```typescript
import { actorCalled, Task } from '@serenity-js/core';
import { CallAnApi, Send, GetRequest, PostRequest, ChangeApiConfig, LastResponse } from '@serenity-js/rest';
import { Ensure, equals } from '@serenity-js/assertions';
```

## Setup del Actor con CallAnApi

`CallAnApi` se otorga con `whoCan(...)` en el step `Given`; declarar `baseUrl` en `configs/wdio.api.conf.ts` no basta por sí solo (ver `[[serenity-wdio-api-testing-rest]]`, `references/actor-setup-verificado.md`, para el detalle verificado con ejecución real):

```typescript
// En step Given:
import { actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

actorCalled('Jorge').whoCan(CallAnApi.at(process.env.API_BASE_URL!));
```

## Task: cambiar base URL

```typescript
// features/api/Tasks/UsarApi.ts
import { Task } from '@serenity-js/core';
import { ChangeApiConfig } from '@serenity-js/rest';

export class UsarApi {
  static baseUrl = (url: string) =>
    Task.where(
      `#actor usa la API ${ url }`,
      ChangeApiConfig.setUrlTo(url),
    );
}
```

## Tasks: GET / POST

```typescript
// features/api/Tasks/ConsultarHealth.ts
import { Task } from '@serenity-js/core';
import { Send, GetRequest } from '@serenity-js/rest';

export class ConsultarHealth {
  static en = (endpoint: string) =>
    Task.where(`#actor consulta ${ endpoint }`,
      Send.a(GetRequest.to(endpoint)),
    );
}

// features/api/Tasks/CrearRecurso.ts
import { Task } from '@serenity-js/core';
import { Send, PostRequest } from '@serenity-js/rest';

export class CrearRecurso {
  static en = (endpoint: string, body: Record<string, unknown>) =>
    Task.where(`#actor crea recurso en ${ endpoint }`,
      Send.a(PostRequest.to(endpoint).with(body)),
    );
}
```

## Question: extraer del response

```typescript
// features/api/Questions/ResponseBody.ts
import { Question } from '@serenity-js/core';
import { LastResponse } from '@serenity-js/rest';

export const StatusCode = () =>
  Question.about<number>('status code', async actor =>
    LastResponse.status().answeredBy(actor),
  );

// O directamente en el step:
import { LastResponse } from '@serenity-js/rest';
import { Ensure, equals } from '@serenity-js/assertions';

await actor.attemptsTo(
  Ensure.that(LastResponse.status(), equals(200)),
);
```

## Checklist de calidad (API)

- [ ] El contexto está claro (API REST)
- [ ] Los imports usan `@serenity-js/rest`
- [ ] `baseUrl` viene de variable de entorno, no hardcoded
- [ ] Cada Task tiene descripción `#actor ...` clara
- [ ] Las Questions están tipadas (`Question.about<T>`)
- [ ] No hay `axios.get(...)` directo en steps
