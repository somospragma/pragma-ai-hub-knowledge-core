# API REST — Questions, aserciones y encadenamiento

## Patrón básico con LastResponse

```typescript
import { LastResponse } from '@serenity-js/rest';
import { Ensure, equals } from '@serenity-js/assertions';

// Status code
Ensure.that(LastResponse.status(), equals(200));

// Body completo (tipado)
Ensure.that(LastResponse.body<{ id: number }>(), equals({ id: 42 }));

// Header
Ensure.that(LastResponse.header('content-type'), equals('application/json; charset=utf-8'));
```

## Question custom para extraer datos

```typescript
import { Question } from '@serenity-js/core';
import { LastResponse } from '@serenity-js/rest';

interface HttpBinPostResponse {
  json: { name: string; role: string };
}

export const UserNameFromResponse = () =>
  Question.about<string>(
    'el nombre del usuario en la respuesta',
    async actor => {
      const response = await LastResponse.body<HttpBinPostResponse>().answeredBy(actor);
      return response.json.name;
    },
  );
```

## Patrón para extraer y validar (FakerAPI)

```typescript
// features/api/Questions/FakerApiTotalFromResponse.ts
import { Question } from '@serenity-js/core';
import { LastResponse } from '@serenity-js/rest';

interface FakerResponse {
  status: string;
  total: number;
  data: unknown[];
}

export const FakerApiTotalFromResponse = () =>
  Question.about<number>('el total de registros en la respuesta de FakerAPI', async actor => {
    const response = await LastResponse.body<FakerResponse>().answeredBy(actor);
    return response.total;
  });
```

## Aserciones avanzadas con @serenity-js/assertions

```typescript
import {
  Ensure, equals, includes, isGreaterThan,
  property, contain, startsWith, matches,
} from '@serenity-js/assertions';

// Status en rango
await actor.attemptsTo(
  Ensure.that(LastResponse.status(), isGreaterThan(199)),
);

// Body contiene clave con valor
await actor.attemptsTo(
  Ensure.that(LastResponse.body<{ status: string }>(),
              property('status', equals('OK'))),
);

// String incluye substring
await actor.attemptsTo(
  Ensure.that(UserNameFromResponse(), includes('Julio')),
);

// Array de respuesta tiene N elementos
await actor.attemptsTo(
  Ensure.that(
    Question.about('items count', async actor => {
      const body = await LastResponse.body<{ data: unknown[] }>().answeredBy(actor);
      return body.data.length;
    }),
    equals(5),
  ),
);

// Match contra regex
await actor.attemptsTo(
  Ensure.that(LastResponse.header('x-request-id'), matches(/^[\w-]{8,}$/)),
);
```

## Encadenamiento de requests

Para escenarios como "crea un usuario, captura su id, y consúltalo":

```typescript
const obtenerIdCreado = () =>
  Question.about<number>('id del recurso creado', async actor => {
    const body = await LastResponse.body<{ id: number }>().answeredBy(actor);
    return body.id;
  });

export const ConsultarRecursoCreado = () =>
  Task.where('#actor consulta el recurso recién creado',
    Interaction.where('captura id y dispara GET', async actor => {
      const id = await obtenerIdCreado().answeredBy(actor);
      await actor.attemptsTo(
        Send.a(GetRequest.to(`/users/${ id }`)),
      );
    }),
  );
```

## Validación de schema (opcional con ajv)

```typescript
// features/api/Questions/ResponseMatchesSchema.ts
import Ajv from 'ajv';
import { Question } from '@serenity-js/core';
import { LastResponse } from '@serenity-js/rest';

const ajv = new Ajv();

export const ResponseMatchesSchema = (schema: object) =>
  Question.about<boolean>('si la respuesta cumple el schema', async actor => {
    const body = await LastResponse.body().answeredBy(actor);
    const validate = ajv.compile(schema);
    return validate(body);
  });
```
