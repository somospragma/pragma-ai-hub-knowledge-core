---
id: serenity-wdio-brownfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Extiende un proyecto TypeScript + WebdriverIO v9 + Serenity/JS v3 + Cucumber 11 existente con nuevos escenarios, Tasks, Questions, Interactions o cambios de selectores, respetando sus convenciones y sin romper Screenplay puro.
tags: [serenity-wdio, brownfield, webdriverio, serenity, cucumber, screenplay, typescript]
---

# Serenity/JS + WebdriverIO Brownfield

## Cuándo aplicar

Cuando el usuario provee un **proyecto WebdriverIO + Serenity/JS + Cucumber ya inicializado** (multiplataforma: web, web_movil, movil, desktop, api) y solicita uno de los siguientes cambios:

- Agregar nuevos escenarios `.feature` para historias adicionales sin tocar la infraestructura existente.
- Agregar nuevas Tasks, Questions, Interactions o UI Mappings a la capa Screenplay actual.
- Actualizar selectores tras un cambio de UI o una nueva versión de la app.
- Refactor localizado de Screenplay (renombrar Task, extraer Question, mover una Interaction) sin reescribir el orquestador ni las configuraciones.

Si el proyecto **no existe** todavía, no aplicar este skill: usar el scaffolder greenfield `[[serenity-wdio-greenfield]]`. La decisión brownfield vs greenfield se resuelve con `[[calidad-brownfield-vs-greenfield]]`.

Antes de activar este skill, confirma el intent con `[[calidad-intent-detection]]` y recolecta los inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`.

## Instrucción

1. **Recolectar inputs** — Exige los siguientes inputs antes de cualquier acción:
   - `project_root` (ruta absoluta al proyecto WebdriverIO + Serenity/JS existente).
   - `context` ∈ {`web`, `mobile`, `hibrido`}. NUNCA asumir el contexto; si no se provee, solicitarlo (regla crítica del arquetipo).
   - `change_type` ∈ {`new-scenario`, `new-page`, `selector-update`, `refactor`}.
   - `change_description` (qué se quiere agregar o modificar: user story, cambios de UI, nuevos selectores).
   - Opcionales según `change_type`: `new_selectors` (mapa nombre logico → selector real), `new_user_story` (para `new-scenario`).
   Si falta cualquiera de los obligatorios, detente y solicítalos vía `[[calidad-mandatory-inputs-protocol]]`.

2. **Completar el análisis previo (BLOQUEANTE)** — Ejecuta el análisis previo descrito en la sección "Análisis previo obligatorio" de este skill y en `references/prior-analysis.md`. **No generes ningún cambio** hasta completar y consolidar el objeto de análisis previo. Este objeto es el contrato que gobierna los pasos siguientes.

3. **Detectar convenciones** — Aplica `references/convention-detection.md` para extraer el objeto completo de convenciones (estructura `features/web` vs `features/mobile`, naming de features, tags de canal y suite, patrón de UI Mapping por contexto, timeouts, correspondencia `--mode` → `.env.<modo>`). Coherencia con el `context` declarado: si no coincide, reportarlo al usuario antes de continuar.

4. **Auditar anti-patrones sin corregir código preexistente** — Aplica `references/anti-pattern-audit.md`. Escanea el código existente en busca de los anti-patrones prohibidos (`Target`, `resolveFor`, `browser.$` directo en Tasks o Steps) y **marca cada ocurrencia** con su ruta relativa y número de línea en un reporte. NO apliques correcciones automáticas sobre código preexistente: solo se reporta para que el usuario decida. El código **nuevo** que generes SÍ debe estar libre de estos anti-patrones.

5. **Generar SOLO lo solicitado** — Según `change_type`:
   - `new-scenario`: emitir `.feature` nuevo (o append a un `.feature` existente respetando estilo y tags) y, si es necesario, Tasks/Questions/UI nuevas. Reusar Tasks/Questions existentes cuando cubran el flujo.
   - `new-page`: emitir el UI Mapping + Tasks asociadas + Questions asociadas + (opcional) escenarios nuevos, según el patrón del contexto (web usa `PageElement`/`By`; mobile usa selectores `string`).
   - `selector-update`: aplicar `references/selector-update-strategy.md`. Solo cambian las asignaciones de selectores dentro del UI Mapping; métodos, firmas, imports y orden permanecen literales.
   - `refactor`: cambios mínimos enfocados; no introducir nuevas capas ni renombrar módulos completos.

6. **Preservar Screenplay puro** — Todo código nuevo respeta el patrón Screenplay del arquetipo:
   - Web: `PageElement.located(By.xpath|css)` en el UI Mapping; `Click`, `Enter`, `Clear`, `Wait.until()` de `@serenity-js/web`; composición con `Task.where()`.
   - Mobile: selectores `string` (Accessibility ID prioritario); `browser.$` **encapsulado únicamente dentro de Interactions**; nunca expuesto en Tasks ni Steps.
   - PROHIBIDO en código nuevo: `Target` (API legacy v2), `resolveFor(actor)` (anti-patrón), `browser.$` directo en Tasks o Steps, hard waits (`browser.pause()`, `setTimeout`), callbacks en `Task.where` (usar `async/await`).

7. **NO modificar infraestructura ni replicar workarounds** — No regenerar `configs/wdio.*.conf.ts`, `scripts/run.mjs`, `package.json`, `tsconfig.json` ni los `.env.<modo>`, salvo solicitud explícita del usuario. En particular, **NO replicar** el workaround de window handles para `NATIVE_APP` (`getWindowHandle`/`getWindowHandles`) descrito en `references/native-app-window-handles.md`: ya vive centralizado en `wdio.shared.conf.ts` y solo aplica cuando `browser.isMobile === true`. Replicarlo en Tasks, Interactions o Steps está prohibido.

8. **Validar coherencia** — Antes de entregar:
   - Validar el Gherkin de cada `.feature` nuevo o tocado (tags de canal y suite conforme al arquetipo).
   - Validar que el código nuevo no contiene los anti-patrones prohibidos.
   - Validar que los selectores nuevos respetan la prioridad del arquetipo (Accessibility ID > TestID > texto > CSS > XPath).
   - Validar que se respetó el contexto declarado (web vs mobile vs híbrido).

9. **Reportar comando de ejecución** — Indicar al usuario el comando `scripts/run.mjs` filtrado por el `--mode` correspondiente y el tag de la nueva historia (por ejemplo `--tags=@smoke`), según `[[serenity-wdio-run-and-tags]]`. Entregar los archivos con `[[calidad-streaming-files-protocol]]` y su trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

## Análisis previo obligatorio

**Regla:** cuando el skill se aplica sobre un proyecto existente, es OBLIGATORIO completar el análisis previo ANTES de generar cualquier cambio. El detalle del procedimiento está en `references/prior-analysis.md`. El análisis debe identificar, como mínimo, los siguientes elementos del proyecto existente:

1. **Estructura de carpetas** — Mapa real de `features/web/`, `features/mobile/`, `step-definitions/`, `support/`, `configs/` y `scripts/`, con las subcarpetas de Screenplay presentes (`Tasks/`, `UI/`, `Questions/`, `Interactions/`, `Data/`, `shared/`).
2. **Dependencias con sus versiones** — Leídas de `package.json`: `@serenity-js/*`, `@wdio/*`, `webdriverio`, `@cucumber/cucumber`, `typescript`, y los reporters (`@wdio/allure-reporter`, `@serenity-js/serenity-bdd`, `wdio-video-reporter`). Registrar la versión exacta declarada, sin asumirla.
3. **Configuraciones** — `configs/wdio.shared.conf.ts` y cada `configs/wdio.<modo>.conf.ts`, el patrón de merge, las capabilities (incluido `wdio:enforceWebDriverClassic` en web), `tsconfig.json`, y los `.env.<modo>` disponibles.
4. **Workarounds documentados** — En especial el workaround de window handles para `NATIVE_APP` en `wdio.shared.conf.ts` (ver `references/native-app-window-handles.md`), y cualquier otro parche técnico comentado en el código.
5. **Convenciones de nomenclatura y tags** — Naming de `.feature`, tags de canal (`@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop`) y de suite (`@smoke`, `@regression`), patrón de UI Mapping por contexto, y `setDefaultTimeout` por step file.

Si alguno de estos elementos no puede determinarse por lectura directa del proyecto, se registra como pendiente y se solicita al usuario; no se asume.

## Salidas

- Cero o más `.feature` nuevos o modificados en el directorio de features detectado (`features/web/Features/` o `features/mobile/**/Features/`).
- Cero o más archivos TypeScript nuevos o modificados en la capa Screenplay (Tasks, Questions, Interactions, UI Mapping) respetando la estructura y el contexto.
- Un reporte de anti-patrones detectados en código preexistente (ruta relativa + línea), **sin** correcciones automáticas aplicadas.
- **Ningún** archivo de infraestructura modificado salvo aprobación explícita del usuario.

## Restricciones

- **NUNCA** generar cambios antes de completar el análisis previo obligatorio.
- **NUNCA** regenerar `configs/wdio.*.conf.ts`, `scripts/run.mjs`, `package.json`, `tsconfig.json` ni los `.env.<modo>`, salvo solicitud explícita.
- **NUNCA** replicar el workaround de window handles `NATIVE_APP` en Tasks, Interactions o Steps: vive solo en `wdio.shared.conf.ts` y aplica únicamente cuando `browser.isMobile === true`.
- **PROHIBIDO en código nuevo:** `Target`, `resolveFor`, `browser.$` directo en Tasks o Steps, hard waits y callbacks en `Task.where`.
- **NO corregir automáticamente** los anti-patrones detectados en código preexistente: solo marcarlos y reportarlos al usuario.
- **Respetar el contexto declarado** (web / mobile / híbrido). Web usa `@serenity-js/web` con `PageElement`/`By`; mobile usa selectores `string` con `browser.$` encapsulado en Interactions. No mezclar.
- **Preservar las convenciones del proyecto** (naming, tags, timeouts, estructura). El brownfield respeta el proyecto; no lo realinea al estándar del chapter.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]`.
