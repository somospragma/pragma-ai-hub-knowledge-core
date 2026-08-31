# Step Isolation — serenity-wdio (WebdriverIO + Serenity/JS + Cucumber)

Implementación del patrón universal `[step-isolation-pattern](../../../_all/step-isolation-pattern.md)` en el stack `serenity-wdio`. El mecanismo nativo: hooks `Before`/`After` de Cucumber para setup y cleanup, Tasks de negocio para el step main, y step-definitions separadas por canal (`web`, `mobile`, `api`) para que un cambio en un canal nunca contamine los otros.

## Mecanismo

- **Setup**: hook `Before` (global o por tag) que deja al Actor listo — `LoginTask.withCredentials(...)` en web, `LoginMobileTask.withCredentials(...)` en mobile, configuración de `baseUrl`/auth en api. Valida estructura, no contrato.
- **Main**: Tasks de dominio + Questions que codifican el contrato funcional (`Ensure.that(LastResponse.status(), equals(200))`, `Ensure.that(DashboardUI.totalText(), equals(...))`).
- **Cleanup**: hook `After` con Tasks de teardown (`LogoutTask.now()`, `ClearSessionTask.now()`). Su falla NO invalida el veredicto del step main.
- **Aislamiento por canal**: cada archivo de step-definitions vive en su propio directorio (`step-definitions/web/`, `step-definitions/mobile/`, `step-definitions/api/`) con su propio `setDefaultTimeout` explícito, para que un timeout ajustado en un canal no afecte a los demás.

## Snippet — Web

```typescript
// step-definitions/web/login.steps.ts
import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { actorCalled } from '@serenity-js/core';
import { Ensure, equals } from '@serenity-js/assertions';
import { LoginTask } from '../../features/web/Tasks/Login';
import { DashboardUI } from '../../features/web/UI/DashboardUI';

setDefaultTimeout(30_000);

// ---- SETUP: Task estructural, no contractual ----
Given('que {actor} inicia sesion con credenciales validas', async (actor) => {
  await actorCalled(actor).attemptsTo(
    LoginTask.withCredentials('alice', 'secret'), // setup auth — NO valida contrato del SUT
  );
});

// ---- MAIN: Task + Question que codifica el contrato ----
When('{actor} navega al dashboard', async (actor) => {
  await actorCalled(actor).attemptsTo(
    NavigateToDashboard.now(),
  );
});

Then('{actor} ve el resumen con el formato esperado', async (actor) => {
  await actorCalled(actor).attemptsTo(
    Ensure.that(DashboardUI.totalText(), equals('$1,234.00')),
  );
});
```

## Snippet — Mobile (hooks compartidos)

```typescript
// step-definitions/mobile/hooks.ts
import { Before, After, setDefaultTimeout } from '@cucumber/cucumber';
import { actorCalled } from '@serenity-js/core';
import { LoginMobileTask } from '../../features/mobile/shared/Tasks/LoginMobileTask';
import { LogoutMobileTask } from '../../features/mobile/shared/Tasks/LogoutMobileTask';

setDefaultTimeout(45_000); // timeouts mobile son mas largos que web; aislado en este archivo

Before({ tags: '@mobile' }, async function () {
  await actorCalled(this.actorName).attemptsTo(
    LoginMobileTask.withCredentials('alice', 'secret'),
  );
});

// ---- CLEANUP: opcional para el veredicto; warning si falla ----
After({ tags: '@mobile' }, async function () {
  try {
    await actorCalled(this.actorName).attemptsTo(LogoutMobileTask.now());
  } catch {
    // Log warning; no falla el escenario del step main.
  }
});
```

## Reglas serenity-wdio-específicas

- **Setup en hooks, nunca en el cuerpo del escenario main**: `Before` deja al Actor autenticado/posicionado. El `Then` del escenario NUNCA repite la aserción de login — eso pertenece al setup.
- **Questions de dominio sólo en main**: `Ensure.that(...)` sobre el contrato funcional (texto de dashboard, status HTTP, atributo mobile) se evalúa después de las Tasks main, nunca dentro del hook `Before`.
- **Un `setDefaultTimeout` por archivo de step-definitions**: web (`30_000` sugerido), mobile (`45_000` sugerido por el bootstrap de Appium), api (`15_000` sugerido, HTTP es rápido). Ajustar un timeout en `step-definitions/mobile/` nunca debe tocar `step-definitions/web/` ni `step-definitions/api/`.
- **Tags Gherkin**: usar el tag de canal (`@web`, `@mobile`, `@api`) para filtrar; el escenario marcado con el tag de canal correspondiente es el que cuenta para el cálculo de escenarios `@smoke`/`@regression` de esa plataforma.
- **Filtrado**: `node ./scripts/run.mjs --mode=web --tags="@web and @smoke"` corre sólo el flujo principal del canal web.
- **El `{ISO}-metadata.json`** debe reflejar únicamente los totales del step main (`passed`/`failed`/`skipped` del escenario Cucumber completo); un fallo aislado en `After` que no afecta el resultado del escenario no debe inflar `failed`.
- **Anti-pattern**: Question contractual evaluada dentro del hook `Before` — si el SUT cambia el flujo de login, todos los escenarios fallan en setup, ocultando si el flujo main (dashboard, checkout, endpoint) realmente funcionaba.

## Cross-links

`[step-isolation-pattern](../../../_all/step-isolation-pattern.md)`, `[screenplay-conventions](./screenplay-conventions.md)`, `[run-and-modes](./run-and-modes.md)`, `[metadata-emitter-serenity-wdio](./metadata-emitter-serenity-wdio.md)`, `[[serenity-wdio-greenfield]]`.
