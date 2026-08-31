# API REST — Autenticación, estructura de carpetas, step definitions y timeouts

## Autenticación

### Bearer token

```typescript
import { ChangeApiConfig } from '@serenity-js/rest';

export const Autenticar = (token: string) =>
  Task.where(`#actor se autentica`,
    ChangeApiConfig.setHeader('Authorization', `Bearer ${ token }`),
  );
```

### Login que captura el token y lo aplica

```typescript
export const LoginYUsarToken = (user: string, password: string) =>
  Task.where('#actor inicia sesión y aplica token',
    Send.a(PostRequest.to('/auth/login').with({ user, password })),
    Ensure.that(LastResponse.status(), equals(200)),
    Interaction.where('aplica token', async actor => {
      const body = await LastResponse.body<{ token: string }>().answeredBy(actor);
      await actor.attemptsTo(
        ChangeApiConfig.setHeader('Authorization', `Bearer ${ body.token }`),
      );
    }),
  );
```

### Basic auth

```typescript
const credentials = Buffer.from(`${ user }:${ pass }`).toString('base64');

ChangeApiConfig.setHeader('Authorization', `Basic ${ credentials }`);
```

## Estructura de carpetas API (patrón del proyecto)

```
features/api/
├── Features/                       # archivos .feature
│   ├── health-check.feature
│   ├── crear-recurso.feature
│   └── cambiar-base-url.feature
├── Tasks/                          # acciones de negocio
│   ├── ConsultarHealth.ts
│   ├── CrearRecurso.ts
│   ├── ConsultarDireccionesFaker.ts
│   └── UsarApi.ts                  # ChangeApiConfig wrappers
├── Questions/                      # extracción de respuestas
│   ├── FakerApiStatusFromResponse.ts
│   ├── FakerApiTotalFromResponse.ts
│   ├── ResponseBody.ts
│   └── UserNameFromResponse.ts
├── Interactions/                   # custom (raras en API)
└── Data/                           # JSON de fixtures
```

## Step definitions API (patrón del proyecto)

```typescript
import { Given, When, Then, setDefaultTimeout, DataTable } from '@cucumber/cucumber';
import { Actor, actorCalled } from '@serenity-js/core';
import { Ensure, equals } from '@serenity-js/assertions';
import { LastResponse, CallAnApi } from '@serenity-js/rest';

import { ConsultarHealth } from '../../api/Tasks/ConsultarHealth';
import { CrearRecurso } from '../../api/Tasks/CrearRecurso';

setDefaultTimeout(60_000);   // API: 60s, no 200s

Given('que {actor} consume el servicio API', async (actor: Actor) => {
  actorCalled(actor.name).whoCan(
    CallAnApi.at(process.env.API_BASE_URL || ''),
  );
});

When('{actor} consulta el endpoint {string}', async (actor: Actor, endpoint: string) => {
  await actor.attemptsTo(ConsultarHealth.delEndpoint(endpoint));
});

When('{actor} crea un recurso en {string} con:',
  async (actor: Actor, endpoint: string, table: DataTable) => {
    const body = table.rowsHash();    // { name: 'Julio', role: 'qa' }
    await actor.attemptsTo(CrearRecurso.conBody(endpoint, body));
  },
);

Then('{actor} debería recibir un código {int}', async (actor: Actor, code: number) => {
  await actor.attemptsTo(Ensure.that(LastResponse.status(), equals(code)));
});
```

## Timeouts recomendados

| Capa | Timeout recomendado |
|---|---|
| `cucumberOpts.timeout` | `60_000` ms (suficiente para API) |
| `setDefaultTimeout` (steps) | `60_000` ms |
| Axios `timeout` por request | `15_000` – `30_000` ms |
| `connectionRetryTimeout` (wdio) | `120_000` ms (default) |

## Checklist de calidad

- [ ] El `baseUrl` viene de `process.env.API_BASE_URL` (no hardcoded)
- [ ] Cada Task tiene descripción `#actor ...` clara
- [ ] Las Questions están tipadas (`Question.about<T>`)
- [ ] El body del response se castea con genérico (`LastResponse.body<MyType>()`)
- [ ] Los headers de auth se configuran con `ChangeApiConfig.setHeader`
- [ ] Las aserciones usan `@serenity-js/assertions` (no `expect` puro de chai/jest)
- [ ] No hay credenciales reales en `.env.api` ni en código
- [ ] El step file tiene `setDefaultTimeout(60_000)` (no 200_000)
- [ ] Encadenamiento de requests valida cada paso con `Ensure`
- [ ] Las Questions no tienen side effects
