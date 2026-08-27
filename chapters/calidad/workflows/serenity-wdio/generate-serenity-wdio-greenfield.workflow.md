---
id: generate-serenity-wdio-greenfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [serenity-wdio]
description: Flujo completo para generar un proyecto WebdriverIO v9 + Serenity/JS v3 + Cucumber 11 multiplataforma con Screenplay puro, listo para ejecutarse de primera.
tags: [serenity-wdio, webdriverio, serenity, cucumber, screenplay, typescript, greenfield, workflow]
---

# Workflow — Generar proyecto Serenity WDIO Greenfield

## Cuando usar

Cuando `[[calidad-intent-detection]]` identifica un escenario greenfield para el stack `serenity-wdio`: el usuario quiere generar un proyecto de automatizacion nuevo basado en TypeScript + WebdriverIO v9 + Serenity/JS v3.31 + Cucumber 11, con el patron Screenplay puro y soporte multiplataforma (web, web_movil, movil nativo Android/iOS, desktop, api).

Para extender un proyecto WebdriverIO + Serenity/JS ya existente, usar el workflow `[[extend-serenity-wdio-brownfield]]` en su lugar.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `project_name` | Si | kebab-case, nombre del directorio raiz. |
| `platform_context` | Si | `web`, `web_movil`, `movil`, `desktop` o `api`. Nunca asumir. |
| `base_url` / `target` | Si (segun contexto) | URL base para web/api; ruta al binario para movil/desktop. |
| `platform_name` | Si (movil) | `android` o `ios`. |
| `app` | Recomendado (movil) | Ruta absoluta al `.apk`, `.app` o `.ipa`; permite deducir identificadores. |
| `app_package` / `app_activity` | Condicional (Android) | Verificar contra el binario real con `aapt dump badging`. |
| `bundle_id` | Condicional (iOS) | Leer `CFBundleIdentifier` real del `.app/Info.plist`. |
| `user_story` o `test_cases` | Recomendado | Genera escenarios iniciales con tags correctos. |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

### 1. Pre-flight check del stack (OBLIGATORIO)

Antes de cualquier otra accion, ejecutar el pre-flight segun `[[serenity-wdio-greenfield]]` (consultar `references/preflight.md` en su subfolder):

- Si pasa: continuar al paso 2.
- Si falla: aplicar las degradaciones documentadas en `preflight.md` (scaffold-only por plataforma afectada) y reportar al usuario antes de proceder.

Este paso es enforcement obligatorio segun `[[calidad-pre-generation-protocol]]`.

### 2. Analisis previo (STRATEGY.md)

Antes de generar cualquier codigo, generar `STRATEGY.md` en el `output_path` segun `references/templates/STRATEGY.md.tpl` y `[[calidad-pre-design-strategy-document]]`. Presentar al usuario y esperar:

- "aprobado" → continuar al siguiente paso.
- "modificar X" → iterar el documento; volver a presentar.

NUNCA generar codigo sin `STRATEGY.md` aprobado explicitamente.

### 3. Verificar inputs obligatorios

Aplicar `[[calidad-mandatory-inputs-protocol]]` y las reglas de validacion especificas del arquetipo antes de generar cualquier archivo:

- Confirmar presencia de `project_name` (kebab-case), `platform_context` y `base_url` o `target` segun el contexto declarado.
- En modo movil: exigir `platform_name` (`android` o `ios`) y la ruta al binario en `app`.
- Para Android: verificar `app_package` y `app_activity` contra el binario real con `aapt dump badging`; nunca inventar el identificador.
- Para iOS: leer `CFBundleIdentifier` real del `.app/Info.plist` con `/usr/libexec/PlistBuddy`; nunca suponer el bundle ID a partir del nombre del repositorio.
- Si falta cualquier input obligatorio, rechazar la solicitud indicando el input faltante por nombre y detener la ejecucion. No generar ningun archivo hasta que todos los inputs esten presentes.

```bash
# Android — verificar package y launchable activity
aapt dump badging ./apps/android/<App>.apk | grep -E "package|launchable"

# iOS — leer bundle ID real
/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" \
  ./apps/ios/<App>.app/Info.plist
```

### 4. Generar la estructura del arquetipo

Materializar el arbol de directorios y archivos base del proyecto, incluyendo de forma explicita los siguientes artefactos:

- **`features/web`** — automatizacion web desktop: subcarpetas `Features`, `Tasks`, `UI` (con `PageElement` y `By`), `Questions`, `Data` y `shared` (Interactions, Questions, Tasks, Utils reutilizables).
- **`features/mobile`** — automatizacion movil nativo: subcarpetas `android`, `ios` (cada una con `Features`, `Tasks`, `UI`) y `shared` (Interactions, Questions, Tasks); los selectores son `string` (Accessibility ID prioritario), nunca `PageElement`.
- **`step-definitions`** — glue de Cucumber separado por canal (`web`, `mobile`, `api`); cada archivo de steps declara `setDefaultTimeout` explicito.
- **`support/parameter.config.ts`** — define los parameter types `{actor}` y `{pronoun}`.
- **`configs/wdio.*.conf.ts`** — un config por modo (`wdio.web.conf.ts`, `wdio.web_mobile.conf.ts`, `wdio.android.conf.ts`, `wdio.ios.conf.ts`, `wdio.desktop.conf.ts`, `wdio.api.conf.ts`), todos heredando de `wdio.shared.conf.ts` mediante merge.
- **`scripts/run.mjs`** — orquestador de ejecucion con soporte para `--mode`, `--platform` y `--tags`.

Usar `.gitkeep` en directorios vacios para conservarlos en git.

```
{project_name}/
├── package.json
├── tsconfig.json
├── wdio.shared.conf.ts
├── configs/
│   ├── wdio.web.conf.ts
│   ├── wdio.web_mobile.conf.ts
│   ├── wdio.android.conf.ts
│   ├── wdio.ios.conf.ts
│   ├── wdio.desktop.conf.ts
│   └── wdio.api.conf.ts
├── scripts/
│   └── run.mjs
├── .env.web
├── .env.web_movil
├── .env.movil.android
├── .env.movil.ios
├── .env.api
├── README.md
└── features/
    ├── web/
    ├── mobile/
    ├── api/
    ├── step-definitions/
    └── support/
        └── parameter.config.ts
```

### 5. Generar las configuraciones WDIO

Crear `wdio.shared.conf.ts` con la base compartida y el workaround de window handles para `NATIVE_APP`, que aplica unicamente cuando `browser.isMobile === true`. Crear cada `configs/wdio.<modo>.conf.ts` por modo:

- Toda capability de navegador en configs **web** y **web_movil** DEBE incluir `'wdio:enforceWebDriverClassic': true` para forzar WebDriver Classic sobre BiDi.
- Las configs **movil** (`android`, `ios`) usan `UiAutomator2` y `XCUITest` respectivamente; no incluyen `enforceWebDriverClassic`.
- La config **desktop** usa Appium Windows.
- La config **api** no lanza navegador.

El workaround de window handles vive unicamente en `wdio.shared.conf.ts` y no se replica en Tasks, Interactions ni Steps.

```typescript
// wdio.shared.conf.ts — workaround NATIVE_APP (no replicar en Tasks ni Steps)
b.overwriteCommand('getWindowHandle', async (orig, ...args) => {
  try { return await orig(...args); }
  catch (e) { if (isUnsupported(e)) return 'NATIVE-APP'; throw e; }
});
b.overwriteCommand('getWindowHandles', async (orig, ...args) => {
  try { return await orig(...args); }
  catch (e) { if (isUnsupported(e)) return ['NATIVE-APP']; throw e; }
});

// configs/wdio.web.conf.ts — capability web con WebDriver Classic obligatorio
capabilities: [
  {
    browserName: 'chrome',
    'wdio:enforceWebDriverClassic': true,
    'goog:chromeOptions': { args: ['--headless=new', '--disable-gpu'] },
  },
],
```

### 6. Generar la capa Screenplay pura

Crear Tasks, Interactions, Questions y UI Mapping respetando el patron Screenplay:

- **Web**: usar `@serenity-js/web` con `PageElement` localizado por `By.xpath()` o `By.css()`; Tasks componen Interactions con `Task.where`; Questions sin efectos secundarios; Interactions encapsulan `Click`, `Enter`, `Clear`, `Wait`.
- **Mobile**: encapsular `browser.$` dentro de Interactions (nunca en Tasks ni Steps); selectores como `string` (Accessibility ID prioritario); prohibido `@serenity-js/web`, `PageElement` y `By`.
- **API**: usar `@serenity-js/rest` con `CallAnApi`, `Send`, `LastResponse` y `ChangeApiConfig`.

Prohibiciones absolutas: `Target` (API v2 legacy), `resolveFor(actor)`, `browser.$` directo en Tasks o Steps, hard waits (`browser.pause()`, `setTimeout`).

```typescript
// Tasks/web — patron Task.where (web)
export const ClickWhenReady = {
  on: (element: Answerable<PageElement>) =>
    Task.where(`#actor hace clic cuando el elemento esta listo`,
      Wait.upTo(Duration.ofSeconds(10)).until(element, isClickable()),
      Click.on(element),
    ),
};

// Interactions/mobile — browser.$ encapsulado en Interaction (movil)
export class Tap extends Interaction {
  static on(selector: string): Tap { return new Tap(selector); }
  constructor(private readonly selector: string) {
    super(`#actor toca ${selector}`);
  }
  async performAs(_actor: UsesAbilities & AnswersQuestions): Promise<void> {
    const el = await browser.$(this.selector);
    await el.waitForExist({ timeout: 15_000 });
    await el.click();
  }
}
```

### 7. Cablear la sincronía atomica del orquestador

Al crear cada `configs/wdio.<modo>.conf.ts`, generar en la misma entrega los cuatro artefactos de sincronía:

1. **`.env.<modo>`** en la raiz con variables mock documentadas y comentarios `# <descripcion>`; nunca credenciales reales.
2. **`scripts/run.mjs`**: agregar la entrada en `modeToConfig` y el mapeo `mode -> envFile`.
3. **`package.json`**: agregar el script `"test:<modo>": "node ./scripts/run.mjs --mode=<modo>"`.
4. **`README.md`**: agregar el comando y la fila en la tabla modo -> config -> env.

| `--mode` | Config | Env |
|---|---|---|
| `web` | `configs/wdio.web.conf.ts` | `.env.web` |
| `web_movil` | `configs/wdio.web_mobile.conf.ts` | `.env.web_movil` |
| `movil` (android) | `configs/wdio.android.conf.ts` | `.env.movil.android` |
| `movil` (ios) | `configs/wdio.ios.conf.ts` | `.env.movil.ios` |
| `desktop` | `configs/wdio.desktop.conf.ts` | `.env` |
| `api` | `configs/wdio.api.conf.ts` | `.env.api` |

### 8. Generar los features con tags obligatorios

Generar al menos dos scenarios `@smoke` iniciales por plataforma declarada. Cada `.feature` DEBE cumplir la convencion de tags del arquetipo:

- **Tag de canal** a nivel `Feature` (exactamente uno de: `@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop`).
- **Tag de suite** a nivel `Feature` o `Scenario` (`@smoke` o `@regression`; `@smoke` es subconjunto critico de `@regression`).
- Tags de tipo y dominio a nivel `Scenario` (`@happy-path`, `@negative`, `@edge-case`, etc.).

Organizar los features por canal siguiendo `[[calidad-test-organization-by-scenario]]`: un escenario por responsabilidad, agrupacion jerarquica en `features/web/Features` y `features/mobile/**/Features`.

```gherkin
@web @regression
Feature: Gestion de formulario de registro

  @smoke @happy-path
  Scenario: Registro exitoso con datos validos
    Given que Ana quiere registrarse en el sistema
    When completa el formulario con datos validos
    Then el sistema confirma el registro exitoso

  @negative
  Scenario: Rechazo con campos obligatorios vacios
    Given que Ana quiere registrarse en el sistema
    When envía el formulario sin completar los campos obligatorios
    Then el sistema muestra los mensajes de error correspondientes
```

Rechazar features sin tag de canal o sin tag de suite; no etiquetar como `@smoke` escenarios no criticos.

### 9. Emitir archivos de forma incremental

Entregar todos los archivos generados aplicando `[[calidad-streaming-files-protocol]]` para garantizar que no se producen cortes parciales durante el scaffolding. Cada archivo se emite completo antes de pasar al siguiente.

### 10. Aplicar la compuerta smoke

El proyecto debe superar la compuerta definida por `[[calidad-smoke-gate-policy]]` y `[[serenity-wdio-greenfield]]` (consultar `references/smoke-gate-wdio.md`) ejecutando la suite `@smoke` a traves del orquestador:

```bash
# Via orquestador
node ./scripts/run.mjs --tags=@smoke

# Via package.json (script generado en el paso 7)
npm run test:smoke
```

Si la compuerta smoke no pasa con exit 0:
- Marcar la ejecucion como fallida con `blocker: "smoke_gate_failed_serenity-wdio"`.
- Impedir la promocion de resultados.
- Reportar el criterio incumplido al usuario.
- No continuar a la compuerta de entrega hasta resolver el fallo.

### 11. Verificar la compuerta de entrega

Antes de cerrar, cumplir `[[calidad-delivery-gate-contract]]` verificando:

- Estructura completa del proyecto (todos los directorios y archivos del arbol del paso 4).
- Configs coherentes: `enforceWebDriverClassic: true` presente en todas las capabilities web y web_movil.
- Todos los `.feature` parsean como Gherkin valido sin errores de sintaxis.
- Scripts de ejecucion presentes en `package.json` (`test:web`, `test:api`, `test:movil:android`, etc.).
- `scripts/run.mjs` contiene la correspondencia completa modo -> config -> env.

Si algun criterio no se cumple, reportarlo con precision e impedir la entrega hasta subsanarlo.

### 12. Registrar evidencia, resultados y metadata

El proyecto generado satisface los assets transversales `_all` de la siguiente forma:

- **`[[calidad-test-evidence-and-traceability]]`**: los reportes `@wdio/allure-reporter`, `@serenity-js/serenity-bdd`, `wdio-cucumberjs-json-reporter` y `wdio-video-reporter` (web) cubren la evidencia y trazabilidad por caso de prueba.
- **`[[calidad-results-structure-universal]]`**: un adaptador post-ejecucion no destructivo proyecta los artefactos existentes a `results/{categoria}/{fecha}/` sin modificar ni eliminar los reportes originales.
- **`[[calidad-execution-metadata-schema]]`**: el adaptador emite `{ISO}-metadata.json` con los campos obligatorios: timestamp ISO, stack (`serenity-wdio`), modo, plataforma, tags, totales pass/fail/skip, duracion, estado del smoke gate y ruta de evidencia.

```
results/
  web/
    2025-07-10/
      2025-07-10T14-00-00-metadata.json
      allure/
      cucumber/
      video/
```

Si falta un artefacto o campo obligatorio, marcar la ejecucion como fallida y listar los elementos faltantes preservando los ya generados.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Extiende la compuerta smoke del paso 10 con el loop completo de triage y auto-correccion que usan los demas stacks del chapter.

0. **Smoke gate 1:1 (obligatorio en modo full)** — el paso 10 ya ejecuta `@smoke` via el orquestador; si falla, aplica el `blocker` documentado alli antes de continuar.
1. **Resolver modo de operacion** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de device/emulador Android, simulador iOS o navegador instalado, degradar la plataforma afectada a `scaffold-only` y reportar `partial` para esa plataforma unicamente (las demas continuan en su modo resuelto).
2. **Ejecutar** via `[[calidad-test-execution-orchestration]]`: `node ./scripts/run.mjs --mode=<modo> [--platform=<android|ios>] --tags=@smoke`, y luego la suite `@regression` si el modo es `full`. Capturar `allure-results/`, `target/site/serenity/`, cucumber JSON y video (web) como evidencia.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky. Causas tipicas: `NATIVE_APP` sin el workaround de window handles, `app_package`/`app_activity`/`bundle_id` incorrectos, selectores `DEFERRED` aun sin resolver, `enforceWebDriverClassic` ausente en una capability web.
4. Si el triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (fallback de selectores web `By.css` → `By.xpath`; fallback mobile Accessibility ID → TestID → texto visible). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca eliminar `enforceWebDriverClassic`, nunca reemplazar una aserción de negocio por un `isDisplayed()` trivial para forzar verde.
5. Reportar estado final: `success` (smoke y, si aplica, regression pasan deterministicamente) | `partial` (scaffold valido, alguna plataforma sin runtime por falta de device/navegador/simulador) | `failed` (escalado a humano con stage, selector, screenshot/video Serenity e hipotesis).
6. Archivar evidencia + audit log de correcciones aplicadas segun `[[calidad-test-evidence-and-traceability]]`. Recordar al usuario que los locators `DEFERRED` se completan con `[[complete-deferred-locators]]`.

### Paso final — Reporte ejecutivo

Invocar `[[calidad-generate-executive-report]]` con `results_path`, `strategy_md_path` y `output_format` (preguntar al usuario o usar default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y se referencia en el `delivery_gate.evidence_persisted.executive_report`. Si el modo es `scaffold-only` o `dry-run` → omitir este paso y registrar `null`.

## Criterios de finalizacion

1. Pre-flight del paso 1 ejecutado; degradaciones por plataforma documentadas en `.evidence/preflight-result.json` si aplica.
2. `STRATEGY.md` generado y aprobado explicitamente por el usuario antes de emitir el primer archivo de codigo.
3. Todos los inputs obligatorios del paso 3 estan presentes y verificados.
4. La estructura del arbol del paso 4 esta completa (incluidos `.gitkeep` en directorios vacios).
5. Todas las capabilities de navegador web y web_movil incluyen `'wdio:enforceWebDriverClassic': true`.
6. El workaround de window handles reside unicamente en `wdio.shared.conf.ts`.
7. La sincronía atomica del paso 7 esta completa: `.env.<modo>`, `run.mjs`, `package.json` y `README.md` actualizados por cada config creado.
8. Todos los `.feature` tienen tag de canal y tag de suite; ningun escenario critico omite `@smoke`.
9. `npm run test:smoke` (smoke gate) ejecuta con exit 0 sin modificaciones manuales.
10. La compuerta de entrega del paso 11 esta superada: estructura completa, configs coherentes, features validos, scripts presentes.
11. `results/{categoria}/{fecha}/{ISO}-metadata.json` generado tras la ejecucion smoke.
12. Reportes originales (Allure, serenity-bdd, cucumber JSON, video) intactos tras el adaptador de resultados.
13. Fase final de triage y auto-correccion ejecutada: estado final (`success`/`partial`/`failed`) reportado, con clasificacion deterministic/flaky documentada para cualquier fallo.
14. Si hubo correcciones aplicadas: audit log persistido y guardrails anti-cheating verificados (ningun `enforceWebDriverClassic` eliminado, ninguna asercion de negocio degradada).
15. Reporte ejecutivo emitido en `.evidence/report-{ISO}.{ext}` (o `null` documentado si el modo fue `scaffold-only`/`dry-run`).
