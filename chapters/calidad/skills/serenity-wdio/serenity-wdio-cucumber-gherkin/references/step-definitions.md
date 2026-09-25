# Cucumber/Gherkin — Step definitions por contexto

## Patrón Web

```typescript
// features/step-definitions/web/<modulo>.steps.ts
import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { Actor } from '@serenity-js/core';
import { <Task> } from '../../web/Tasks/<Modulo>/<Task>';

setDefaultTimeout(200_000);

Given('que {actor} <precondición>', async (actor: Actor) => {
  await actor.attemptsTo(
    <Task>.<metodo>(),
  );
});

When('{actor} <acción> con {string}', async (actor: Actor, dato: string) => {
  await actor.attemptsTo(
    <Task>.<metodo>(dato),
  );
});

Then('{actor} debería <resultado> de acuerdo a {string}', async (actor: Actor, dataset: string) => {
  await actor.attemptsTo(
    <Task>.<metodo>(dataset),
  );
});
```

## Patrón Mobile

```typescript
// features/step-definitions/mobile/<modulo>.steps.ts
import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { Actor } from '@serenity-js/core';
import { <Task> } from '../../mobile/shared/Tasks/<Task>';
import { PlatformUI } from '../../mobile/shared/Resolvers/PlatformUI';

setDefaultTimeout(200_000);

Given('the user named {actor} opens the application', async (_actor: Actor) => {
  // Inicialización si aplica
});

When('{pronoun} logs in with username {string} and password {string}',
  async (actor: Actor, username: string, password: string) => {
    await actor.attemptsTo(
      <Task>.withCredentials(PlatformUI.<modulo>(), username, password),
    );
  },
);
```

## Patrón API

```typescript
// features/step-definitions/api/<modulo>.steps.ts
import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { Actor } from '@serenity-js/core';
import { <Task> } from '../../api/Tasks/<Task>';

setDefaultTimeout(60_000);   // API: 60s, no 200s

Given('que {actor} consume el servicio API', async (_actor: Actor) => {
  // Setup del actor con CallAnApi ability
});

When('{actor} consulta el endpoint {string}', async (actor: Actor, endpoint: string) => {
  await actor.attemptsTo(
    <Task>.get(endpoint),
  );
});

Then('{actor} debería recibir un código {int}', async (actor: Actor, statusCode: number) => {
  await actor.attemptsTo(
    Ensure.that(<Question>, equals(statusCode)),
  );
});
```

## Timeouts por contexto

| Contexto | `setDefaultTimeout` |
|---|---|
| Web | `200_000` ms |
| Mobile (Appium) | `200_000` ms |
| API REST | `60_000` ms |

## Checklist de calidad (step definitions)

- [ ] El step definition tiene `setDefaultTimeout` con el valor correcto para el contexto
- [ ] Cada step delega a una Task (nunca lógica directa en el step)
- [ ] No hay `browser.pause()` ni `setTimeout` en ningún step
- [ ] El archivo está en la carpeta correcta según el contexto (web/mobile/api)
- [ ] Los imports usan rutas relativas correctas desde `step-definitions/`
- [ ] Se usa `{actor}` en el primer step y `{pronoun}` en los siguientes cuando aplica
