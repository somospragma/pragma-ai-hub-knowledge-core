---
id: serenity-wdio-run-and-tags
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Ejecucion del arquetipo WebdriverIO + Serenity/JS + Cucumber via el orquestador scripts/run.mjs, con seleccion por modo, plataforma y tags de Cucumber.
tags: [serenity-wdio, webdriverio, cucumber, run, tags, orquestador]
---

# Ejecucion y filtros de tags (serenity-wdio)

## Instrucción

Ejecuta las pruebas del arquetipo siempre a través del orquestador `scripts/run.mjs`, nunca invocando `wdio` de forma directa. El orquestador resuelve tres decisiones antes de arrancar WebdriverIO: el modo (`--mode`), la plataforma móvil cuando aplica (`--platform`) y la expresión de tags de Cucumber (`--tags` o la variable de entorno `TAGS`). Con esas tres entradas selecciona el config `configs/wdio.<modo>.conf.ts` correcto, carga el archivo `.env.<modo>` correspondiente y reenvía la expresión de tags a Cucumber como `--cucumberOpts.tags=<expr>`.

La regla operativa es: primero decidir el modo, luego (solo para móvil nativo) la plataforma, y por último acotar el conjunto de escenarios con una expresión de tags. Antes de declarar una corrida como exitosa, valida siempre la compuerta smoke ejecutando el subconjunto `@smoke` con el mismo orquestador (ver la sección "Compuerta smoke").

## Valores válidos de `--mode` y `--platform`

- `--mode` acepta: `web`, `web_movil`, `movil`, `desktop`, `api`, `all`.
- `--platform` acepta: `android`, `ios`. Solo es obligatorio cuando `--mode=movil`; el orquestador aborta con código de error si se pide `movil` sin plataforma.
- El modo también puede fijarse por la variable de entorno `MODE` y la plataforma por `MOBILE_PLATFORM` o `PLATFORM`.

## Comando de ejemplo por cada modo soportado

```bash
# Modo web (navegador desktop)
node ./scripts/run.mjs --mode=web

# Modo web_movil (navegador con emulacion movil)
node ./scripts/run.mjs --mode=web_movil

# Modo movil nativo Android (requiere --platform)
node ./scripts/run.mjs --mode=movil --platform=android

# Modo movil nativo iOS (requiere --platform)
node ./scripts/run.mjs --mode=movil --platform=ios

# Modo desktop (Appium Windows)
node ./scripts/run.mjs --mode=desktop

# Modo api (pruebas REST)
node ./scripts/run.mjs --mode=api

# Modo all (ejecuta web, web_movil, movil, desktop y api en secuencia)
node ./scripts/run.mjs --mode=all
```

Cada modo tiene además un atajo declarado en `package.json`:

```bash
npm run test:web
npm run test:web_movil
npm run test:movil            # requiere platform; usa test:movil:android o test:movil:ios
npm run test:movil:android
npm run test:movil:ios
npm run test:desktop
npm run test:api
npm run test:all
```

## Correspondencia `--mode` → `.env.<modo>`

El orquestador carga el archivo de entorno según el modo (y la plataforma en móvil) antes de arrancar la suite. La correspondencia completa es:

| `--mode` | `--platform` | Archivo de entorno cargado |
|---|---|---|
| `web` | (no aplica) | `.env.web` |
| `web_movil` | (no aplica) | `.env.web_movil` |
| `movil` | `android` | `.env.movil.android` |
| `movil` | `ios` | `.env.movil.ios` |
| `desktop` | (no aplica) | `.env` (no existe `.env.desktop`; usa el `.env` por defecto) |
| `api` | (no aplica) | `.env.api` |
| `all` | (no aplica) | `.env` (por defecto; cada sub-modo hereda ese entorno) |

Si el archivo esperado no existe, el orquestador informa por consola y continúa con `.env` o con las variables ya presentes en `process.env`.

## Selección por tags de Cucumber (`--tags`)

La expresión se pasa con `--tags=<expr>` o mediante la variable de entorno `TAGS`. El orquestador la reenvía a WebdriverIO como `--cucumberOpts.tags=<expr>`. Las expresiones admiten los operadores `and`, `or`, `not` y la agrupación con paréntesis.

```bash
# Operador and: escenarios que son @regression y ademas no estan @wip
node ./scripts/run.mjs --mode=api --tags="@regression and not @wip"

# Operador or: escenarios @smoke o @happy-path
node ./scripts/run.mjs --mode=web --tags="@smoke or @happy-path"

# Operador not: excluir escenarios marcados @flaky
node ./scripts/run.mjs --mode=web --tags="not @flaky"

# Agrupacion por parentesis: combina precedencia de or con and y not
node ./scripts/run.mjs --mode=api --tags="(@smoke or @happy-path) and @api and not @wip"

# Equivalente por variable de entorno
TAGS="@smoke" node ./scripts/run.mjs --mode=all
```

Convención del arquetipo: los escenarios en construcción se marcan `@wip` o `@skip` y se excluyen por defecto con `--tags="not @wip and not @skip"`. El tag `@smoke` es un subconjunto crítico de `@regression`.

## Compuerta smoke

Antes de promover cualquier resultado, ejecuta el subconjunto `@smoke` y confirma que pasa. La política, el comando por stack y el comportamiento ante fallo se definen en `[[calidad-smoke-gate-policy]]`.

```bash
# Smoke gate del arquetipo (equivale a run.mjs --tags=@smoke)
npm run test:smoke
```
