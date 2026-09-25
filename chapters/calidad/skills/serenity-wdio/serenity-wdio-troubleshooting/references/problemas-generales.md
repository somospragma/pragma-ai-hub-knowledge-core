# Problemas generales y plantilla de documentación

## Problema 5: Timeouts insuficientes

### Sintomas

- `Function timed out, ensure the promise resolves within X milliseconds`
- Cucumber aborta steps en escenarios largos (formularios extensos, mobile lento)

### Configuración correcta del proyecto

| Lugar | Timeout | Comentario |
|---|---|---|
| `setDefaultTimeout` (web/mobile steps) | `200_000` | Cubre Appium + animaciones |
| `setDefaultTimeout` (api steps) | `60_000` | API más rápida |
| `cucumberOpts.timeout` | `60_000` | Por step individual |
| `Wait.upTo(...)` (web) | `Duration.ofSeconds(10–30)` | Por condición |
| `waitForDisplayed` (mobile) | `15_000 ms` | Por elemento |
| `waitforTimeout` (wdio) | `10_000` | Default WDIO |

Subir timeouts solo cuando el problema sea real (red lenta, animaciones largas). NO usarlos para enmascarar flakiness.

---

## Problema 6: Target o resolveFor(actor) (anti-patrones legacy)

### Sintomas

- Código copiado de tutoriales antiguos (Serenity/JS v2)
- Errores de tipos al usar `Target.the(...)`
- Componentes que no se reportan correctamente

### Causa

APIs legacy de v2. En v3 (`^3.31`) están deprecadas o removidas.

### Alternativa moderna

```typescript
// v2 legacy — PROHIBIDO
const button = Target.the('login button').located(by.xpath('...'));

// v3 moderno
const button = () =>
  PageElement.located(By.xpath('...'))
             .describedAs('login button');
```

```typescript
// v2 anti-patrón — PROHIBIDO
await someQuestion.resolveFor(actor);

// v3 — Question.answeredBy(actor) o Ensure.that
await actor.attemptsTo(
  Ensure.that(someQuestion, equals(expected)),
);
```

---

## Problema 7: Hard waits (browser.pause, setTimeout)

### Sintomas

- Tests que pasan local pero fallan en CI
- Tiempos de ejecución innecesariamente largos
- Race conditions intermitentes

### Causa

`browser.pause(N)` espera N ms ciegamente sin verificar el estado real del DOM/UI.

### Alternativa correcta

```typescript
// MAL
await browser.pause(3000);

// BIEN (web)
await actor.attemptsTo(
  Wait.upTo(Duration.ofSeconds(10)).until(LoginUI.spinner(), not(isVisible())),
);

// BIEN (mobile, encapsulado en Interaction)
await el.waitForDisplayed({ timeout: 15_000 });
```

---

## Problema 8: Reportes Allure/Serenity vacios o incompletos

### Causas comunes y fixes

| Causa | Fix |
|---|---|
| `serenity-bdd update` no ejecutado | `npm run serenity:update` |
| `crew` mal configurada | Verificar `wdio.shared.conf.ts` incluye `@serenity-js/serenity-bdd` y `ArtifactArchiver` |
| Reporter mezclado mal | No mezclar `@wdio/allure-reporter` y serenity-bdd sin cuidado |
| Falta `outputDirectory` | `[ '@serenity-js/core:ArtifactArchiver', { outputDirectory: 'target/site/serenity' } ]` |

---

## Problema 9: Steps reportados como "is not defined" aunque el archivo existe

### Sintomas

- Cucumber reporta `Step "..." is not defined. You can ignore this error by setting cucumberOpts.ignoreUndefinedDefinitions as true.` para TODOS los steps del feature.
- El archivo de step-definitions existe en la ruta correcta y no tiene errores de sintaxis.
- El `.feature` parsea correctamente (Cucumber sí lo encuentra y lo lista en el reporte).

### Causa raiz (verificada con ejecucion real)

`specs` en `configs/wdio.<modo>.conf.ts` se resuelve relativo al **archivo de config** (por eso usa `../features/...`). En cambio, `cucumberOpts.require` y `cucumberOpts.import` se resuelven relativos a la **raiz del proyecto** (el `cwd` desde donde se invoca `wdio`), no al archivo de config. Si se copia el patron `../features/step-definitions/...` de `specs` hacia `cucumberOpts.require`, el glob no matchea nada y los step-definitions nunca se cargan — sin ningun error de "archivo no encontrado", solo el mensaje enganoso de "step is not defined".

### Fix

```typescript
// configs/wdio.api.conf.ts
export const config: any = merge(shared, {
  specs: ['../features/api/Features/*.feature'],              // relativo al archivo de config
  cucumberOpts: {
    require: ['./features/step-definitions/api/*.ts', './features/support/*.ts'],  // relativo a la raiz del proyecto
    // ...
  },
});
```

Verificacion rapida cuando aparece el sintoma: correr `node -e "console.log(require('glob').sync('<patron>'))"` desde la raiz del proyecto con el patron exacto declarado en `cucumberOpts.require`; si devuelve `[]`, la ruta esta mal resuelta.

---

## Problema 10: "You're calling functions... instance of Cucumber that isn't running (status: PENDING)"

### Sintomas

```
Error:
          You're calling functions (e.g. "Given") on an instance of Cucumber that isn't running (status: PENDING).
          This means you may have an invalid installation, potentially due to:
          - Cucumber being installed globally
          - A project structure where your support code is depending on a different instance of Cucumber
```

- Ocurre justo al cargar el step-definitions file (antes de ejecutar ningun step).
- El proyecto no tiene Cucumber instalado globalmente.

### Causa raiz (verificada con ejecucion real)

`npm install` puede instalar dos copias fisicas de `@cucumber/cucumber` con la **misma version exacta**: una en `node_modules/@cucumber/cucumber` (la que importan los step-definitions) y otra anidada en `node_modules/@wdio/cucumber-framework/node_modules/@cucumber/cucumber` (la que usa internamente `@wdio/cucumber-framework` para registrar el `supportCodeLibraryBuilder`). Aunque sean la misma version, Node.js las trata como instancias de modulo distintas — los `Given`/`When`/`Then` que importan los steps quedan registrados contra una instancia que el framework nunca marca como `RUNNING`.

### Diagnostico

```bash
find node_modules -name "@cucumber" -type d
# Si aparece mas de una ruta con /cucumber/ dentro, hay duplicacion
```

### Fix

1. Declarar en `package.json` un bloque `overrides` que fuerza resolucion unica:

```json
{
  "overrides": {
    "@cucumber/cucumber": "11.0.1"
  }
}
```

2. Si tras `npm install` la copia anidada persiste con exactamente la misma version que la de la raiz, eliminarla manualmente y dejar que Node.js resuelva hacia arriba en el arbol de `node_modules`:

```bash
rm -rf node_modules/@wdio/cucumber-framework/node_modules/@cucumber/cucumber
```

Ver `[[serenity-wdio-greenfield]]` (`references/package-dependencies.md`) para el detalle completo de dependencias verificadas.

---

## Problema 11: El actor no tiene la ability CallAnApi aunque `baseUrl` está declarado

### Sintomas

```
ConfigurationError: <Actor> can PerformActivities, AnswerQuestions, RaiseErrors, ScheduleWork.
They can't, however, CallAnApi yet. Did you give them the ability to do so?
```

- El `Given` del escenario pasa (no hace nada).
- El error ocurre en el primer `Send.a(...)` del `When`.
- `configs/wdio.api.conf.ts` sí declara `baseUrl: process.env.API_BASE_URL`.

### Causa raiz (verificada con ejecucion real)

Declarar `baseUrl` en el config **no otorga la ability por si solo**. Solo el `runner: '@serenity-js/webdriverio'` (en vez del `runner: 'local'` por defecto de WebdriverIO) activa el adapter que otorga `CallAnApi` automaticamente a todos los actores. El arquetipo de este stack usa `runner: 'local'`, por lo que la ability se otorga siempre con `whoCan(...)` explicito en el `Given`.

### Fix

```typescript
import { actorCalled } from '@serenity-js/core';
import { CallAnApi } from '@serenity-js/rest';

Given('que {actor} consume el servicio API', async (actor: Actor) => {
  actorCalled(actor.name).whoCan(
    CallAnApi.at(process.env.API_BASE_URL || ''),
  );
});
```

Ver `[[serenity-wdio-api-testing-rest]]` (`references/actor-setup-verificado.md`) para el detalle de ambos caminos y por que solo uno esta verificado con ejecucion real end-to-end.

---

## Plantilla para documentar nuevos workarounds

Cuando aparezca un nuevo impedimento, documentarlo así al inicio del archivo donde se aplica el patch:

```typescript
/**
 * WORKAROUND <NOMBRE_CORTO> (<plataforma afectada>)
 *
 * Contexto:
 *   <Qué hace Serenity/JS o WDIO que causa el problema>
 *
 * Problema:
 *   <Síntoma observable y por qué falla>
 *
 * Solución:
 *   <Qué hace este código y por qué resuelve>
 *
 * Alcance:
 *   - SOLO se aplica en <condición>
 *   - NO replicar en <Tasks/Steps/Interactions>
 *
 * Referencias:
 *   - <link a docs / issue / handbook>
 */
```
