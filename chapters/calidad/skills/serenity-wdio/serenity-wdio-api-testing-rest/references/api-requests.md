# API REST — Variantes de request y configuración

## Setup del actor: opciones completas

Ver `references/actor-setup-verificado.md` para el detalle completo y la verificación de ambos caminos. Resumen:

### Opción A: `whoCan` explícito en el Given (usado en el proyecto, verificado con ejecución real)

```typescript
import { actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

Given('que {actor} consume el servicio API', async (actor: Actor) => {
  actorCalled(actor.name).whoCan(
    CallAnApi.at(process.env.API_BASE_URL || ''),
  );
});
```

El `baseUrl` sigue viniendo de `process.env.API_BASE_URL` (el mismo valor declarado en `configs/wdio.api.conf.ts`); el step solo lo lee, nunca lo hardcodea. Esta es la opción que debe generar el skill por defecto.

### Opción B: automático vía `runner: '@serenity-js/webdriverio'` (requiere adapter completo, no verificado end-to-end en este stack)

Declarar `baseUrl` en `configs/wdio.api.conf.ts` **no otorga la ability por sí solo**. Solo si `wdio.shared.conf.ts` declara `runner: '@serenity-js/webdriverio'` (en vez del `runner: 'local'` por defecto), el adapter oficial de Serenity/JS otorga `CallAnApi` automáticamente a todos los actores. No usar esta vía como flujo generado por defecto: ver `references/actor-setup-verificado.md` para el error concreto encontrado al intentar verificarla.

### Opción C: manual con whoCan fuera del Given (equivalente a la Opción A, para setup a nivel de suite)

```typescript
import { actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

actorCalled('Jorge').whoCan(
  CallAnApi.at(process.env.API_BASE_URL!),
);
```

### Opción D: con axios config personalizada

```typescript
import { CallAnApi } from '@serenity-js/rest';
import axios from 'axios';

actorCalled('Jorge').whoCan(
  CallAnApi.using(axios.create({
    baseURL: process.env.API_BASE_URL,
    timeout: 30_000,
    headers: { 'X-Client': 'qa-arquetipo' },
  })),
);
```

## PUT / PATCH / DELETE

```typescript
import { PutRequest, PatchRequest, DeleteRequest, Send } from '@serenity-js/rest';

// PUT (reemplaza recurso completo)
Send.a(PutRequest.to(`/users/${ id }`).with({ name: 'nuevo' }));

// PATCH (actualización parcial)
Send.a(PatchRequest.to(`/users/${ id }`).with({ status: 'active' }));

// DELETE
Send.a(DeleteRequest.to(`/users/${ id }`));
```

## Request con headers, query params y config

```typescript
Send.a(
  GetRequest.to('/users')
    .using({
      headers: {
        'Authorization': `Bearer ${ token }`,
        'Content-Type': 'application/json',
      },
      params: {
        page: 1,
        size: 20,
      },
      timeout: 15_000,
    }),
);
```

## Cambiar base URL en runtime (patrón UsarApi.ts)

```typescript
import { Task } from '@serenity-js/core';
import { ChangeApiConfig } from '@serenity-js/rest';

export class UsarApi {
  static baseUrl = (url: string) =>
    Task.where(
      `#actor usa la API ${ url }`,
      ChangeApiConfig.setUrlTo(url),
    );

  static withHeader = (name: string, value: string) =>
    Task.where(
      `#actor configura header ${ name }`,
      ChangeApiConfig.setHeader(name, value),
    );
}
```

## Manejo de errores HTTP

`Send.a(...)` no lanza automáticamente en respuestas 4xx/5xx — se evalúan con `LastResponse.status()`. Si se quiere que falle inmediatamente:

```typescript
Send.a(
  GetRequest.to('/users/999').using({
    validateStatus: (status: number) => status >= 200 && status < 300,
    // axios lanzará excepción si el status no cumple
  }),
);
```

Lo recomendado es NO lanzar y validar con `Ensure.that(LastResponse.status(), ...)` para reportes claros.
