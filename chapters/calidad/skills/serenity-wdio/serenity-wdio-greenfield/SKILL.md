---
id: serenity-wdio-greenfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Genera un proyecto WebdriverIO v9 + Serenity/JS v3 + Cucumber 11 multiplataforma (web, web_movil, movil, desktop, api) con Screenplay puro, listo para ejecutarse de primera.
tags: [serenity-wdio, webdriverio, serenity, cucumber, screenplay, typescript, greenfield]
---

# Serenity WDIO Greenfield

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto de automatización nuevo (greenfield) basado en TypeScript + WebdriverIO v9 + Serenity/JS v3 + Cucumber 11, con el patrón Screenplay puro y soporte multiplataforma: web, web_movil (WebView), movil nativo (Appium Android/iOS), desktop (Appium Windows) y api (REST). Este es el stack `serenity-wdio` del chapter `calidad`.

Para extender un proyecto WebdriverIO + Serenity/JS ya existente sin romper sus convenciones, usar el skill brownfield del stack `[[serenity-wdio-brownfield]]`.

Antes de generar, confirma el intent con `[[calidad-intent-detection]]` y recolecta los inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. La decisión greenfield frente a brownfield se resuelve con `[[calidad-brownfield-vs-greenfield]]`.

## Instrucción

Sigue estos pasos en orden. No generes código antes de resolver el contexto y los inputs obligatorios.

1. **Resolver contexto de plataforma.** Determina si el escenario objetivo es web, web_movil (WebView), movil nativo (Android/iOS), desktop o api. Nunca asumas el contexto; si no está declarado, solicítalo. El detalle de plataformas y su diferenciación con el stack `appium` (Java 21 + Gradle + Serenity Java, solo Android) está en `references/platforms-and-scope.md`.

2. **Validar inputs obligatorios.** Aplica `[[calidad-mandatory-inputs-protocol]]` y las reglas específicas del arquetipo descritas en `references/mandatory-inputs.md`. Rechaza la solicitud indicando el input faltante por nombre si alguno no se provee. Verifica el Bundle ID / Package real del binario antes de fijar identificadores en cualquier `.env.movil.*` (es la causa número uno de fallos al arrancar Appium).

3. **Generar la estructura del proyecto.** Materializa el árbol del arquetipo enumerado en `references/project-structure.md`, que incluye de forma explícita los siguientes artefactos. El `package.json` usa las dependencias exactas verificadas en `references/package-dependencies.md` (incluye paquetes periféricos obligatorios como `@wdio/spec-reporter`, `@wdio/cucumber-framework` y `@serenity-js/webdriverio`, y el fix de deduplicación de `@cucumber/cucumber` vía `overrides`):
   - `features/web` — automatizacion web desktop (Features, Tasks, UI con PageElement, Questions, Data, shared).
   - `features/mobile` — automatizacion movil nativo (android, ios, shared) con selectores como string.
   - `step-definitions` — steps de Cucumber por canal (`web`, `mobile`, `api`), con aislamiento de steps conforme a `[[calidad-step-isolation-pattern]]` (steps atomicos, sin estado compartido entre escenarios y `setDefaultTimeout` explicito por archivo).
   - `support/parameter.config.ts` — definicion de los parameter types `{actor}` y `{pronoun}`.
   - `configs/wdio.*.conf.ts` — configuraciones por modo que heredan de `wdio.shared.conf.ts`.
   - `scripts/run.mjs` — orquestador de ejecucion por `--mode`, `--platform` y `--tags`.

4. **Generar la capa Screenplay pura.** Crea Tasks, Interactions, Questions y UI Mapping siguiendo `references/screenplay-conventions.md`. En web usa `@serenity-js/web` con `PageElement` y `By`; en mobile encapsula `browser.$` dentro de Interactions (nunca en Tasks o Steps) y usa selectores string. Prohibido `Target`, `resolveFor`, `browser.$` directo en Tasks/Steps y hard waits.

5. **Generar las configuraciones WDIO.** Crea `wdio.shared.conf.ts` y los configs por modo segun `references/wdio-configs.md`. Toda capability de navegador (web y web_movil) DEBE incluir `'wdio:enforceWebDriverClassic': true`. El workaround de window handles para `NATIVE_APP` vive solo en `wdio.shared.conf.ts` y aplica cuando `browser.isMobile === true`. Regla critica verificada con ejecucion real: `specs` se resuelve relativo al archivo de config (`../features/...`), pero `cucumberOpts.require`/`import` se resuelven relativos a la raiz del proyecto (`./features/...`) — usar `../` en `require`/`import` hace que los step-definitions nunca se carguen, con el error enganoso `Step is not defined` en lugar de un error de archivo no encontrado. Ver `references/wdio-configs.md` seccion "Regla critica".

6. **Generar features etiquetados y organizados por escenario.** Cada `.feature` lleva al menos un tag de canal (`@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop`) a nivel Feature y un tag de suite (`@smoke` o `@regression`). Organiza los features por canal y por historia siguiendo `[[calidad-test-organization-by-scenario]]` (un escenario por responsabilidad; agrupacion jerarquica en `features/web/Features` y `features/mobile/**/Features`). Las reglas completas de tags estan en `references/cucumber-tags.md`.

7. **Cablear la sincronia atomica del orquestador.** Al crear cada `configs/wdio.<modo>.conf.ts`, genera en la misma entrega su `.env.<modo>`, la entrada en `scripts/run.mjs` y el script en `package.json`. La correspondencia modo a config y modo a env esta en `references/run-and-modes.md`.

8. **Emitir archivos de forma incremental.** Entrega los archivos generados aplicando `[[calidad-streaming-files-protocol]]` para no producir cortes parciales.

9. **Aplicar la compuerta smoke.** El proyecto debe pasar la compuerta definida por `[[calidad-smoke-gate-policy]]` ejecutando la suite `@smoke` via `scripts/run.mjs --tags=@smoke`. El mapeo de la compuerta se detalla en `references/gates-and-evidence.md`.

10. **Verificar la compuerta de entrega.** Antes de cerrar, cumple `[[calidad-delivery-gate-contract]]`: estructura completa, configs coherentes y features que parsean.

11. **Registrar evidencia, resultados y metadata.** El proyecto genera evidencia y trazabilidad conforme a `[[calidad-test-evidence-and-traceability]]` (Allure, serenity-bdd, cucumber JSON, video), proyecta resultados a la estructura de `[[calidad-results-structure-universal]]` y emite metadata de ejecucion conforme a `[[calidad-execution-metadata-schema]]`. El mapeo reporte a asset esta en `references/gates-and-evidence.md`.

## Salidas

Estructura completa del proyecto en `references/project-structure.md`. Convenciones de codigo Screenplay en `references/screenplay-conventions.md`. Configuraciones por modo en `references/wdio-configs.md`. Orquestacion y modos en `references/run-and-modes.md`. Cumplimiento de los assets transversales en `references/gates-and-evidence.md`.

## Restricciones

- **Prosa en espanol, codigo en ingles, sin emojis.** Todo el contenido generado respeta esta regla.
- **Screenplay puro obligatorio.** Prohibido `Target` (API v2 legacy), `resolveFor(actor)` y `browser.$` directo en Tasks o Steps.
- **Web usa `@serenity-js/web`** con `PageElement` y `By`; mobile NUNCA usa `@serenity-js/web` ni `PageElement`.
- **`'wdio:enforceWebDriverClassic': true`** obligatorio en toda capability de navegador (web y web_movil), no en mobile nativo ni desktop.
- **Sin hard waits** (`browser.pause()`, `setTimeout`); usar `Wait.until()` en web y `waitForDisplayed`/`waitForExist` encapsulados en Interactions en mobile.
- **Sincronia atomica** al crear un config nuevo: `.env.<modo>`, `run.mjs`, `package.json` y README en la misma entrega.
- **Verificar Bundle ID / Package real** del binario antes de fijarlos en `.env.movil.*`.
- **Detalle extendido en `references/*.md`** en markdown plano sin frontmatter; el SKILL.md se mantiene conciso.
