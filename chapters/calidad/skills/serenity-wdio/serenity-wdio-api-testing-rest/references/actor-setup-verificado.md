# Setup del actor con `CallAnApi` — verificado contra ejecución real

Este documento resuelve una ambigüedad real detectada al ejecutar un proyecto `serenity-wdio` modo `api` de punta a punta: declarar `baseUrl` en `configs/wdio.api.conf.ts` **no es suficiente por sí solo** para que el actor obtenga `CallAnApi`. Hay dos caminos válidos, y solo uno de ellos aplica sin configuración adicional.

## Camino 1 — `whoCan(...)` explícito en el step (recomendado, verificado)

Es el patrón que genera este skill por defecto. Funciona con el `runner: 'local'` estándar de WebdriverIO, sin dependencias de configuración adicionales:

```typescript
import { Given } from '@cucumber/cucumber';
import { Actor, actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

Given('que {actor} consume el servicio API', async (actor: Actor) => {
  actorCalled(actor.name).whoCan(
    CallAnApi.at(process.env.API_BASE_URL || ''),
  );
});
```

- El `baseUrl` sigue viniendo de `configs/wdio.api.conf.ts` (o de `process.env.API_BASE_URL` directamente); el `Given` solo lo lee, nunca lo hardcodea.
- Verificado con ejecución real: `node ./scripts/run.mjs --mode=api --tags=@smoke` contra un endpoint HTTP real, 3 corridas consecutivas en verde.
- Es la opción que debe generar el greenfield y la que debe esperar el brownfield al detectar convenciones existentes.

## Camino 2 — `runner: '@serenity-js/webdriverio'` en `wdio.shared.conf.ts` (automático, requiere adapter completo)

`@serenity-js/webdriverio` expone un `WebdriverIOFrameworkAdapter` que, cuando se declara como `runner` del proyecto, otorga automáticamente `CallAnApi.using({ baseURL: webdriverIOConfig.baseUrl })` (además de `BrowseTheWebWithWebdriverIO` y `TakeNotes`) a **todos** los actores sin necesidad de `whoCan(...)` manual. Esto es lo que el skill documentaba como "automático vía baseUrl", pero el mecanismo real requiere:

1. Declarar explícitamente `runner: '@serenity-js/webdriverio'` en `wdio.shared.conf.ts` (no el `runner: 'local'` por defecto).
2. Que el paquete `@serenity-js/webdriverio` esté resuelto correctamente como plugin de `runner` (WebdriverIO lo carga vía `initializePlugin`, con requisitos de formato de export que pueden variar entre versiones del paquete y de `@wdio/cli`).

Esta vía **no se pudo verificar de punta a punta** durante la ejecución real: al declarar `runner: '@serenity-js/webdriverio'` con las versiones fijadas en este stack (`@wdio/cli@9.10.1`, `@serenity-js/webdriverio@3.31.10`), WebdriverIO lanzó `TypeError: Runner is not a constructor`. No usar este camino como el flujo generado por defecto hasta verificarlo con una combinación de versiones concreta.

## Regla de generación

- El greenfield y el brownfield de este stack usan **siempre el Camino 1** (`whoCan(...)` explícito). Es el único camino con ejecución real verificada extremo a extremo.
- Si un proyecto brownfield ya declara `runner: '@serenity-js/webdriverio'` en su `wdio.shared.conf.ts` existente (Camino 2), respetar esa convención detectada y no forzar `whoCan(...)` en los steps nuevos — pero documentar la brecha si el `Given` nuevo queda vacío sin verificación local de que el Cast automático realmente aplica.
- `@serenity-js/webdriverio` es una dependencia obligatoria en `package.json` en ambos caminos (peer dependency de `@serenity-js/core` en el ecosistema WebdriverIO), aunque el Camino 1 no la use directamente en código.

## Cross-links

`[[serenity-wdio-api-testing-rest]]`, `[[serenity-wdio-screenplay-pattern]]`, `references/api-requests.md`, `references/api-auth-y-estructura.md`.
