---
id: extend-serenity-wdio-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [serenity-wdio]
description: Flujo para extender un proyecto WebdriverIO + Serenity/JS existente con nuevos escenarios, artefactos o actualizaciones de selectores, respetando las convenciones detectadas y el patrón Screenplay puro.
tags: [serenity-wdio, brownfield, workflow, screenplay, typescript, webdriverio, cucumber, multiplataforma]
---

# Workflow — Extender proyecto serenity-wdio brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` identifica una solicitud de automatización sobre el stack `serenity-wdio` y `[[calidad-brownfield-vs-greenfield]]` la clasifica como **brownfield**: el usuario aporta archivos de un proyecto WebdriverIO + Serenity/JS + Cucumber existente y solicita extenderlo con nuevos escenarios, artefactos o actualizaciones de selectores. Para un proyecto nuevo desde cero, usar `[[generate-serenity-wdio-greenfield]]`.

### Pre-flight (OBLIGATORIO)

Antes de cualquier acción, verificar que el proyecto satisface la señal de detección del stack (`@serenity-js/webdriverio` en `package.json`). Si la señal no se cumple o el proyecto corresponde a otro stack, detener y reportar la discrepancia sin generar ningún artefacto.

Además, ejecutar el pre-flight de toolchain y ambiente según `[[serenity-wdio-greenfield]]` (consultar `references/preflight.md` en su subfolder), acotado al `target_module` declarado: si el módulo es `mobile`, validar `adb`/`aapt` (Android) o `xcrun`/`PlistBuddy` (iOS); si es `web`/`web_movil`/`api`, validar accesibilidad de `base_url`/`API_BASE_URL`. Si falla, degradar a `scaffold-only` con razón documentada en `.evidence/preflight-result.json`.

Cumplir el protocolo `[[calidad-pre-generation-protocol]]` incluso en brownfield: confirmar inputs (incluido módulo objetivo), declarar cobertura de los archivos NUEVOS (no de los preexistentes), esperar confirmación del usuario antes de generar.

### Paso previo — Análisis condicional con STRATEGY.md

Si el alcance del brownfield es **grande** (≥3 escenarios/artefactos nuevos, o cambios que afectan múltiples módulos preexistentes): generar `STRATEGY.md` según `references/templates/STRATEGY.md.tpl` del skill `[[serenity-wdio-greenfield]]` y `[[calidad-pre-design-strategy-document]]`. Esperar aprobación explícita del usuario antes de continuar.

Si el alcance es **pequeño** (1-2 cambios puntuales): omitir `STRATEGY.md` y proceder directo a generación, documentando la decisión en `.evidence/scope-decision.md`.

El `STRATEGY.md` del brownfield documenta lo NUEVO; no rediseña la infraestructura existente (`configs/`, `scripts/run.mjs`, `.env.*`).

### Regla brownfield específica — No modificar código preexistente

La auto-corrección y el self-healing aplican EXCLUSIVAMENTE a los archivos NUEVOS que este workflow genera. Los archivos preexistentes del proyecto (tests, UI mapping, Tasks, Questions, Interactions, configs, scripts) son intocables, aunque fallen o contengan anti-patrones. Si se detectan anti-patrones en código preexistente:

1. Registrar cada ocurrencia con su ruta relativa y tipo de anti-patrón (`Target`, `resolveFor`, `browser.$` en Tasks/Steps).
2. Nunca modificar el archivo preexistente.
3. Nunca ajustar fixtures, datos o configs preexistentes para hacer pasar tests.
4. Escalar al usuario con el contexto completo.

Esta regla es de cumplimiento obligatorio y complementa el `[[calidad-test-self-correction-loop]]`.

## Inputs

| Input                | Obligatorio | Notas                                                                                                          |
|----------------------|-------------|----------------------------------------------------------------------------------------------------------------|
| `project_root`       | Sí          | Ruta absoluta al proyecto existente (debe contener `package.json` con `@serenity-js/webdriverio`).            |
| `target_module`      | Sí          | Módulo a extender: `web`, `mobile`, `api`, `desktop` o `web_movil`.                                           |
| `change_type`        | Sí          | Uno de: `new-scenario`, `new-ui`, `selector-update`, `refactor`.                                              |
| `change_description` | Sí          | Descripción de lo que se quiere agregar o modificar (historia de usuario, captura, mapa de selectores nuevos). |
| `new_selectors`      | No          | Mapa `nombre → selector`, requerido cuando `change_type = selector-update`.                                   |
| `new_user_story`     | No          | Texto de la historia, requerido en `new-scenario` para asignar tag `@user-story:<ID>`.                        |
| `firma`              | No          | Documento técnico complementario (screenshot, spec parcial, contrato de API).                                 |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`. Si falta un obligatorio, detenerse y solicitarlo antes de continuar.

## Pasos

### 1. Analizar proyecto existente

Recorrer `project_root` e inventariar:

- **Estructura de carpetas**: presencia de `features/web/`, `features/mobile/`, `features/desktop/`, `step-definitions/`, `support/`, `configs/`.
- **Dependencias con versiones exactas**: leer `package.json` y registrar al menos `@serenity-js/webdriverio`, `@serenity-js/cucumber`, `@wdio/cli`, `@wdio/allure-reporter`, `@serenity-js/rest`, `@serenity-js/assertions`, TypeScript y Cucumber.
- **Configuraciones**: identificar todos los archivos `configs/wdio.*.conf.ts` presentes y verificar que cada uno hereda de `wdio.shared.conf.ts`.
- **Workarounds documentados**: verificar que `wdio.shared.conf.ts` contiene el parche de window handles para `NATIVE_APP` (`overwriteCommand('getWindowHandle', ...)` y `overwriteCommand('getWindowHandles', ...)`), activo solo cuando `browser.isMobile === true`.

Si el árbol no corresponde a la estructura esperada del arquetipo, detener y reportar la discrepancia al usuario.

### 2. Verificar Screenplay puro — detección de anti-patrones

Recorrer los archivos `Tasks/`, `step-definitions/` y `Interactions/` del proyecto existente y detectar las siguientes violaciones sin aplicar correcciones:

- Uso de `Target` (API legado de Serenity/JS v2).
- Uso de `resolveFor(actor)` (anti-patrón).
- Uso de `browser.$` expuesto directamente en Tasks o Steps (sin encapsular en una `Interaction`).

Por cada ocurrencia detectada, registrar: ruta relativa del archivo, número de línea aproximado y tipo de anti-patrón. Emitir el inventario como sección del reporte de análisis. **No modificar** ningún archivo preexistente.

### 3. Verificar workaround de window handles

Confirmar que `wdio.shared.conf.ts` declara el parche de `getWindowHandle` / `getWindowHandles` en el hook `before` del ciclo de vida de WebdriverIO, acotado a `browser.isMobile === true`. Verificar que el parche **no** está replicado en ningún archivo bajo `Tasks/`, `Interactions/` ni `step-definitions/`.

Si el workaround no existe en `wdio.shared.conf.ts` y el proyecto soporta mobile, registrar la ausencia como brecha crítica en el reporte de análisis. Si existe replicado en artefactos Screenplay, registrarlo como deuda técnica. No corregir ninguna de las dos situaciones de forma automática.

### 4. Identificar módulos a extender

A partir de `target_module` y del inventario de la estructura detectada, determinar con precisión qué artefactos aplican:

- **web / web_movil**: `PageElement` + `By`, `Click`, `Enter`, `Wait.until()`, UI Mapping en clases con métodos estáticos que retornan `PageElement`.
- **mobile (android / ios)**: selectores como `string`, `Interaction` para encapsular `browser.$`, sin `PageElement` ni APIs de `@serenity-js/web`.
- **api**: `CallAnApi`, `Send` con `GetRequest`/`PostRequest`/`PutRequest`/`DeleteRequest`/`PatchRequest`, `LastResponse`, `ChangeApiConfig`.
- **desktop**: verificar capabilities de `wdio.desktop.conf.ts`; aplicar el mismo patrón de Interactions que mobile.

Documentar el módulo activo y la capa de artefactos que se generará antes de proceder.

### 5. Generar nuevos artefactos respetando convenciones existentes

Producir los artefactos correspondientes al `change_type` detectado, respetando:

- **Estructura de carpetas**: ubicar cada artefacto en el directorio del módulo correcto (`features/web/Tasks/`, `features/mobile/android/UI/`, etc.).
- **Nomenclatura**: seguir el patrón `PascalCase` para clases TypeScript (`LoginTask.ts`, `LoginUI.ts`) y `kebab-case` para features (`registro-estudiante.feature`).
- **Tags obligatorios**: ver paso 6.
- **Composición Screenplay**: usar `Task.where(...)` para componer Interactions; nunca exponer `browser.$` fuera de una `Interaction`; nunca usar `Target` ni `resolveFor`.
- **Sincronía atómica**: si se crea un nuevo `configs/wdio.<modo>.conf.ts`, generar simultáneamente el archivo `.env.<modo>`, la entrada en `scripts/run.mjs`, el script en `package.json` y la actualización del `README.md`.

Entregar los archivos siguiendo `[[calidad-streaming-files-protocol]]` y registrar trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

#### Patrones de referencia por módulo

**Web — UI Mapping:**

```typescript
// features/web/UI/LoginUI.ts
import { By, PageElement } from '@serenity-js/web';

export class LoginUI {
  static userInput = () =>
    PageElement.located(By.css('#username')).describedAs('input de usuario');

  static submitButton = () =>
    PageElement.located(By.css('#submit')).describedAs('botón de envío');
}
```

**Web — Task con composición:**

```typescript
// features/web/Tasks/Login.ts
import { Task } from '@serenity-js/core';
import { Click, Enter, Wait, isClickable } from '@serenity-js/web';
import { Duration } from '@serenity-js/core';
import { LoginUI } from '../UI/LoginUI';

export const Login = {
  withCredentials: (username: string, password: string) =>
    Task.where(`#actor inicia sesión como ${username}`,
      Wait.upTo(Duration.ofSeconds(10)).until(LoginUI.userInput(), isClickable()),
      Enter.theValue(username).into(LoginUI.userInput()),
      Enter.theValue(password).into(LoginUI.passwordInput()),
      Click.on(LoginUI.submitButton()),
    ),
};
```

**Mobile — Interaction encapsulando `browser.$`:**

```typescript
// features/mobile/shared/Interactions/Tap.ts
import { Interaction, UsesAbilities, AnswersQuestions } from '@serenity-js/core';

export class Tap extends Interaction {
  static on(selector: string): Tap { return new Tap(selector); }

  constructor(private readonly selector: string) {
    super(`#actor toca ${selector}`);
  }

  async performAs(_actor: UsesAbilities & AnswersQuestions): Promise<void> {
    const el = await browser.$(this.selector);
    await el.waitForExist({ timeout: 15_000 });
    await el.waitForDisplayed({ timeout: 15_000 });
    await el.click();
  }
}
```

**Mobile — UI Mapping con selectores como `string`:**

```typescript
// features/mobile/android/UI/LoginUI.ts
export const LoginUI = {
  input_usuario: '~username-input',
  input_password: '~password-input',
  button_ingresar: '~submit-button',
};
```

**API — Task con `@serenity-js/rest`:**

```typescript
// features/api/Tasks/ConsultarProducto.ts
import { Task } from '@serenity-js/core';
import { Send, GetRequest, LastResponse } from '@serenity-js/rest';
import { Ensure, equals } from '@serenity-js/assertions';

export const ConsultarProducto = {
  conId: (id: number) =>
    Task.where(`#actor consulta el producto ${id}`,
      Send.a(GetRequest.to(`/products/${id}`)),
      Ensure.that(LastResponse.status(), equals(200)),
    ),
};
```

### 6. Verificar tags obligatorios en features nuevas o modificadas

Antes de cerrar cualquier archivo `.feature` generado o modificado, verificar que cumple la convención de tags del arquetipo:

- A nivel `Feature`: al menos un tag de **canal** (`@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop`) y al menos un tag de **suite** (`@smoke` o `@regression`).
- A nivel `Scenario`: al menos un tag de **tipo** (`@happy-path`, `@negative`, `@edge-case`).
- Si el escenario está incompleto o no puede ejecutarse en el estado actual, marcarlo `@wip`.

Ejemplo de feature correctamente etiquetada:

```gherkin
@web @regression
Feature: Registro de estudiante en el formulario

  @smoke @happy-path
  Scenario: Registro exitoso con datos válidos
    Given Ana navega al formulario de registro
    When Ana completa y envía el formulario con datos válidos
    Then Ana ve el mensaje de confirmación

  @negative
  Scenario: Registro fallido con campos obligatorios vacíos
    Given Ana navega al formulario de registro
    When Ana envía el formulario sin completar los campos obligatorios
    Then Ana ve los mensajes de error correspondientes
```

Si algún `.feature` no cumple los tags obligatorios, corregirlo antes de continuar con el paso 7.

### 7. Ejecutar smoke gate de los escenarios añadidos

Ejecutar el smoke gate del stack según `[[calidad-smoke-gate-policy]]` y `[[serenity-wdio-greenfield]]` (consultar `references/smoke-gate-wdio.md`), **exclusivamente sobre los escenarios nuevos o modificados** en esta sesión, filtrando por el tag `@smoke` combinado con el tag de canal del módulo extendido:

```bash
# Ejemplo para módulo web
node ./scripts/run.mjs --mode=web --tags="@smoke and @web"

# Ejemplo para módulo api
node ./scripts/run.mjs --mode=api --tags="@smoke and @api"

# Ejemplo para módulo mobile Android
node ./scripts/run.mjs --mode=movil --platform=android --tags="@smoke and @mobile"
```

Los escenarios preexistentes del proyecto no se incluyen en el gate para no ampliar el tiempo de ejecución ni contaminar los resultados. Si el gate falla en algún escenario nuevo, clasificar el fallo como determinístico o flaky mediante `[[calidad-failure-triage-and-classification]]` y corregir antes de declarar la extensión completada. Si no hay entorno disponible (dispositivo, navegador, servidor API), el gate degrada a estado `partial` con razón documentada.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Extiende el smoke gate del paso 7 con el loop completo de triage y auto-corrección. Brownfield: la auto-corrección aplica **EXCLUSIVAMENTE** a los archivos NUEVOS generados por este workflow; NUNCA a los preexistentes del proyecto, aunque fallen (ver la regla brownfield específica al inicio de este workflow y `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) que defaultea a `dry-run`. Si el agente carece de device/emulador, simulador o navegador disponible, degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` el comando del paso 7 (filtrado por `@smoke` y el tag de canal del módulo extendido).
3. Si hay fallos en los escenarios nuevos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky. Si un escenario preexistente falla por daño colateral, detenerse y reportar — NO auto-corregir.
4. Si el triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (fallback de selectores web `By.css` → `By.xpath`; fallback mobile Accessibility ID → TestID → texto visible). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca eliminar `enforceWebDriverClassic`, nunca degradar una aserción de negocio a un check trivial para forzar verde.
5. Reportar estado final: `success` (escenarios nuevos pasan determinísticamente) | `partial` (scaffold entregado, gate no ejecutable por falta de entorno) | `failed` (fallos no resueltos, escalado al usuario con feature, step, selector, screenshot/video e hipótesis).
6. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`.

### 8. Emitir entregables y cerrar

Una vez superada la fase final de ejecución, triage y auto-corrección:

1. Declarar el estado final de la extensión (heredado del paso anterior): `success`, `partial` o `failed`.
2. Emitir `results/serenity-wdio/{fecha}/{ISO}-metadata.json` con el schema universal `[[calidad-execution-metadata-schema]]`, incluyendo los campos `stack`, `mode`, `platform`, `tags`, totales `pass/fail/skip`, duración y estado del smoke gate.
3. Archivar la evidencia de trazabilidad según `[[calidad-test-evidence-and-traceability]]` (Allure results, cucumber JSON, video cuando aplique).
4. **Reporte ejecutivo**: invocar `[[generate-executive-report]]` con `results_path`, `strategy_md_path` (si se generó en el paso previo) y `output_format` (default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y debe segregar explícitamente "escenarios/artefactos nuevos (en scope de esta sesión)" de "escenarios preexistentes (referencia, no ejecutados en el gate)". Si el modo es `scaffold-only` o `dry-run` → omitir y registrar `null`.
5. Emitir el bloque `delivery_gate` según `[[calidad-delivery-gate-contract]]` con el manifest de archivos nuevos o modificados, la evidencia persistida (incluido el reporte ejecutivo) y el estado final.
6. Consultar `[[calidad-brownfield-vs-greenfield]]` para registrar las diferencias entre lo que se generó en esta sesión y lo que preexistía, como parte del informe de cierre.

## Criterios de finalización

- [ ] Pre-flight de detección de señal y de toolchain/ambiente ejecutado; degradación a `scaffold-only` documentada en `.evidence/preflight-result.json` si aplica.
- [ ] Decisión de alcance (`STRATEGY.md` vs omitido) documentada en `.evidence/scope-decision.md` o `STRATEGY.md` aprobado si el alcance fue grande.
- [ ] Inventario del proyecto completado: estructura de carpetas, dependencias con versiones, configs y workarounds documentados.
- [ ] Verificación de Screenplay puro realizada: anti-patrones detectados registrados por ruta y tipo, sin modificaciones sobre código preexistente.
- [ ] Workaround de window handles verificado en `wdio.shared.conf.ts`; ausencia o replicación registradas como brecha/deuda si aplica.
- [ ] Módulo a extender identificado y documentado con la capa de artefactos correspondiente.
- [ ] Artefactos nuevos generados respetando estructura de carpetas, nomenclatura y convenciones del proyecto existente.
- [ ] Ningún artefacto preexistente modificado.
- [ ] Todos los `.feature` nuevos o modificados llevan tags de canal, suite y tipo.
- [ ] Smoke gate ejecutado sobre los escenarios añadidos con resultado `success` o `partial` justificado.
- [ ] Fase final de triage y auto-corrección ejecutada: clasificación deterministic/flaky documentada para cualquier fallo nuevo; escenarios preexistentes nunca auto-corregidos.
- [ ] Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados.
- [ ] `results/serenity-wdio/{fecha}/{ISO}-metadata.json` emitido con el schema universal.
- [ ] Reporte ejecutivo emitido en `.evidence/report-{ISO}.{ext}` segregando artefactos nuevos de preexistentes (o `null` documentado si el modo fue `scaffold-only`/`dry-run`).
- [ ] Bloque `delivery_gate` emitido con manifest y estado coherente.
- [ ] No se introdujeron dependencias nuevas sin aprobación explícita del usuario.
