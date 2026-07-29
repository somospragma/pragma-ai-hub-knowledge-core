---
id: calidad-generate-appium-screenplay-android
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [appium]
description: Flujo completo para generar un proyecto Appium V2 Android con Screenplay + Serenity + Cucumber listo para ejecutarse.
tags: [appium, mobile, android, screenplay, workflow, greenfield]
---

# Workflow — Generar proyecto Appium Screenplay Android

## Cuándo usar

Cuando `[[calidad-intent-detection]]` identifica un escenario greenfield para Appium Android: el usuario quiere automatizar pruebas mobile en Android con el patrón Screenplay (Serenity + Cucumber) sobre Gradle. iOS está fuera de scope (`[[calidad-appium-screenplay-android]] (consultar `references/android-only-scope-rationale.md` en su subfolder)`).

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `project_name` | Sí | kebab-case. |
| `apk_path` | Sí | Ruta absoluta al APK. |
| `include_login_case` | Sí | Bool o "true"/"si"/"sí"/"yes"/"1". |
| `user_story` o `test_cases` | Sí (uno) | Genera escenarios `@proposed`. |
| `app_package` | No | Default `com.example.app` + TODO. |
| `app_activity` | No | Default `.MainActivity` + TODO. |
| `platform_version` | No | Default `12.0`. |
| `device_name` | No | Default `Android Emulator`. |
| `automation_name` | No | Default `UiAutomator2`. |
| `appium_server_url` | No | Default `http://127.0.0.1:4723`. |
| `selectors` | No | Si viene, mapeo `AppiumBy.id|xpath|accessibilityId`. |
| `locator_map` | Condicional | **Obligatorio si las pruebas se construyen antes del desarrollo** (`execution_target != real`): accessibility ids acordados con dev según `[[calidad-ui-locator-map-contract]]`; alimenta los deferred locators. |
| `firma` | No | Documento técnico complementario. |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`, incluido el SUT readiness gate (`[[calidad-sut-readiness-gate]]`). Sin APK no hay runtime: pre-desarrollo el alcance es scaffold + deferred locators desde el `locator_map`, modo `scaffold-only`. Mock de backend (`[[calidad-service-virtualization-mockoon]]`) aplica solo si el APK existe y permite override de base URL.

**Enforcement del locator map (pre-desarrollo)**: si `execution_target != real` y no hay `locator_map`, detenerse con blocker `locator_map_missing` antes de generar la capa Screenplay; continuar solo con waiver explícito del usuario registrado en el delivery gate (`locator_map: waived`). Ver `[[calidad-ui-locator-map-contract]]` (sección Enforcement).

## Pasos

### 1. Pre-flight check del stack (OBLIGATORIO)

Antes de cualquier otra acción, ejecutar el pre-flight según [[calidad-appium-screenplay-android]] (consultar `references/preflight.md` en su subfolder):
- Si pasa: continuar al paso 2.
- Si falla: aplicar las degradaciones documentadas en `preflight.md` y reportar al usuario antes de proceder.
- Persistir el resultado en `.evidence/preflight-result.json`.

Este paso es enforcement obligatorio según `[[calidad-pre-generation-protocol]]`.

### 2. Análisis previo (STRATEGY.md)

Antes de generar cualquier código, generar `STRATEGY.md` en el `output_path` según ``references/templates.md` (sección `STRATEGY.md`)` y `[[calidad-pre-design-strategy-document]]`. Presentar al usuario y esperar:
- "aprobado" → continuar al siguiente paso.
- "modificar X" → iterar el documento; volver a presentar.

NUNCA generar código sin STRATEGY.md aprobado explícitamente.

### 3. Validar inputs
Aplica las 5 reglas de `[[calidad-appium-screenplay-android]] (consultar `references/mandatory-inputs-validation.md` en su subfolder)`. Si falla, abortar con el mensaje exacto.

### 4. Rechazar si no es Android
Si `platform_name` (cuando viene) en minúsculas no es `"android"`, responder `"En Appium V2 solo se soporta Android."` (`[[calidad-appium-screenplay-android]] (consultar `references/android-only-scope-rationale.md` en su subfolder)`).

### 5. Decidir estrategia de locators (auto-discovery vs deferred)

Si el pre-flight (paso 1) detectó:
- APK válido (aapt dump badging legible)
- adb funcional con ≥1 device/emulator
- appium binary disponible

→ **PREGUNTAR al usuario explícitamente**:

> "Detecto APK + emulador/device + Appium server disponibles. Puedo:
> 
> (a) **Auto-descubrir selectores reales** recorriendo la app (~3-5 min, recomendado). Aplica `[[calidad-appium-apk-auto-discovery]]`. Los Page Objects se generan con selectores reales del DOM (resource-id, content-desc, etc.) y score de confianza por cada uno.
> 
> (b) **Continuar con locators diferidos** (`// TODO: update real locator`). Aplica `[[calidad-appium-screenplay-android]] (consultar `references/deferred-locators-strategy.md` en su subfolder)`. Tú completas los selectores manualmente después usando Appium Inspector.
> 
> ¿Cuál prefieres?"

- Si elige (a) → invocar `[[calidad-appium-apk-auto-discovery]]` antes de generar Page Objects (paso 8). Persistir resultados en `.evidence/locators-discovered.json`.
- Si elige (b) o no respondió → comportamiento actual (deferred).
- Si pre-flight no detectó capacidades → omitir la pregunta, ir directo a deferred. Si hay `locator_map`, los deferred locators usan los accessibility ids del mapa (contrato con dev, no placeholders inventados — ver `[[calidad-ui-locator-map-contract]]` y `references/deferred-locators-strategy.md`).

### 6. Extraer flows y normalizar defaults
Mapear `user_story` y `test_cases` a items para escenarios `@proposed` (≤80 chars, newlines → espacios). Normalizar defaults Android. Si falta `app_package`/`app_activity`, dejar TODO en README con `aapt dump badging`.

### 7. Generar Gradle scaffold
`build.gradle`, `settings.gradle`, `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.properties`, `serenity.properties`, `android.conf`, `README.md` con las versiones inmutables de `[[calidad-appium-screenplay-android]] (consultar `references/gradle-version-matrix.md` en su subfolder)`. NO redefinir `aggregate`/`reports`/`clean` (`[[calidad-appium-screenplay-android]] (consultar `references/no-aggregate-collision.md` en su subfolder)`).

### 8. Generar capa Screenplay
`LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage` bajo `co.com.pragma.*` siguiendo `[[calidad-appium-screenplay-android]] (consultar `references/screenplay-layers.md` en su subfolder)`. Si el paso 5 eligió auto-discovery: inyectar selectores reales desde `.evidence/locators-discovered.json` (`[[calidad-appium-apk-auto-discovery]]`). Si eligió deferred o no había capacidades: aplicar deferred locators (`[[calidad-appium-screenplay-android]] (consultar `references/deferred-locators-strategy.md` en su subfolder)`).

### 9. Generar features
2 escenarios `@android @smoke` siempre + `@android @proposed` por cada item de `user_story`/`test_cases`. Cumplir `[[calidad-appium-screenplay-android]] (consultar `references/gherkin-syntax-rules.md` en su subfolder)`. Detalle en `[[calidad-appium-screenplay-android]] (consultar `references/smoke-vs-proposed-scenarios.md` en su subfolder)`.

### 10. Ejecutar health-check
14 stages estáticas + pipeline Gradle (`clean → compileJava → testClasses` mínimo). Calcular `generation_status` según `[[calidad-appium-screenplay-android]] (consultar `references/health-check-pipeline.md` en su subfolder)`.

### 11. Validar 5 acceptance criteria
Exit 0 sin cambios manuales; cero colisiones; cero errores `compileJava`/`compileTestJava`; todos los `*.feature` parsean; `gradlew` ejecutable de primera.

### 12. Construir run command
`./gradlew clean test aggregate -p <project_path>` + variantes de `[[calidad-appium-run-and-tags]]`.

### 13. Reportar status
Entregar archivos con `[[calidad-streaming-files-protocol]]` solo si `generation_status = success`. Registrar trazabilidad por `[[calidad-test-evidence-and-traceability]]` y mapear casos según `[[calidad-route-test-generation]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Esta fase **extiende el health-check estático del paso 7** (14 stages + pipeline Gradle) con verificación de **runtime** real: instalar APK, levantar Appium server, correr los 2 escenarios `@android @smoke` y aplicar el loop de triage + auto-corrección. El health-check estático garantiza que el scaffold compila; este loop garantiza que arranca contra el binario real.

0. **Smoke gate 1:1 (obligatorio en modo full)** — Antes de ejecutar la suite completa, validar que el scaffold corre end-to-end con 1 escenario `@android @smoke`. Aplicar [[calidad-smoke-gate-policy]] y [[calidad-appium-screenplay-android]] (consultar `references/smoke-gate-gradle.md`). Comando: `./gradlew test -Dcucumber.filter.tags=@smoke`. Si falla con exit ≠ 0 → status `partial` con `blocker: "smoke_gate_failed_appium"` y escalar al usuario; NO continuar a ejecución de `@proposed` ni a auto-corrección.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `scaffold-only` porque el paso 8 ya bloquea entrega si `generation_status != success`; el agente típicamente NO tiene emulador Android disponible. Subir a `full` sólo si el usuario confirma device/emulador + Appium server + APK válido. Clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) defaultean a `dry-run`. Si `scaffold-only`, reportar `partial` (el scaffold es válido, falta runtime).
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` cuando aplique: `./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`. Capturar `target/site/serenity/` como evidencia primaria.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky. Causas típicas: Appium server no responde, capabilities mal configuradas, APK no instalado, `app_package`/`app_activity` incorrectos (recordar TODO con `aapt dump badging`), locators diferidos aún en `TODO`.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (multi-locator fallback, accesibilidad como alternativa a `id`). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca eliminar el assert visual de `AppIsResponsive`, nunca reemplazar `TapOn` real por flags en memoria, nunca completar locators reales falsos (eso requiere Appium Inspector, ver `[[calidad-complete-deferred-locators]]`).
5. Reportar estado final: `success` (scaffold + smoke runtime pasa) | `partial` (scaffold válido, no se ejecutó runtime por falta de device/Appium server) | `failed` (escalado a humano con stage, logcat, screenshot Serenity, hipótesis).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. Recordar al usuario que los locators reales se completan con `[[calidad-complete-deferred-locators]]`.

### Paso final — Reporte ejecutivo

Invocar `[[calidad-generate-executive-report]]` con `results_path`, `strategy_md_path` y `output_format` (preguntar al usuario o usar default `html`). El reporte se persiste en `.evidence/report-{ISO}.{ext}` y se referencia en el `delivery_gate.evidence_persisted.executive_report`. Si modo es `scaffold-only` o `dry-run` → omitir este paso y registrar `null`.

## Criterios de finalización

1. `generation_status = success` (no `partial`, no `failed`).
2. Los 5 acceptance criteria pasan (`[[calidad-appium-screenplay-android]] (consultar `references/health-check-pipeline.md` en su subfolder)`).
3. `build.gradle` NO redefine `aggregate`, `reports` ni `clean`.
4. Todos los `*.feature` parsean como Gherkin válido.
5. `gradlew` ejecutable de primera (mode 0755) o README documenta `chmod +x gradlew` / `sh ./gradlew`.
6. Los 2 escenarios `@android @smoke` ejecutables pasan en BUILD SUCCESSFUL sin selectores reales.
7. Reporte Serenity generado en `target/site/serenity/index.html`.
8. Si se aplicaron defaults `app_package=com.example.app` / `app_activity=.MainActivity`, el README lo declara como TODO con el comando `aapt dump badging`.
9. Health-check de runtime ejecutado al menos una vez (cuando hay device/Appium server). Estado: `success` / `partial` / `failed` reportado. `partial` es aceptable si el scaffold pasó health-check estático pero no hay device disponible.
10. Si hubo fallos en runtime: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
11. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Locators diferidos NUNCA se completaron con valores inventados (eso es `[[calidad-complete-deferred-locators]]`).
12. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando `./gradlew test` + checklist runtime pendiente entregados; ninguna corrección aplicada sin aprobación humana.
13. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@accessibility` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
