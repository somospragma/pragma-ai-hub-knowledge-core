---
id: generate-appium-screenplay-android
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

Cuando `[[calidad-intent-detection]]` identifica un escenario greenfield para Appium Android: el usuario quiere automatizar pruebas mobile en Android con el patrón Screenplay (Serenity + Cucumber) sobre Gradle. iOS está fuera de scope (`[[appium-android-only-scope-rationale]]`).

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
| `firma` | No | Documento técnico complementario. |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`.

## Pasos

### 1. Validar inputs
Aplica las 5 reglas de `[[appium-mandatory-inputs-validation]]`. Si falla, abortar con el mensaje exacto.

### 2. Rechazar si no es Android
Si `platform_name` (cuando viene) en minúsculas no es `"android"`, responder `"En Appium V2 solo se soporta Android."` (`[[appium-android-only-scope-rationale]]`).

### 3. Extraer flows y normalizar defaults
Mapear `user_story` y `test_cases` a items para escenarios `@proposed` (≤80 chars, newlines → espacios). Normalizar defaults Android. Si falta `app_package`/`app_activity`, dejar TODO en README con `aapt dump badging`.

### 4. Generar Gradle scaffold
`build.gradle`, `settings.gradle`, `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.properties`, `serenity.properties`, `android.conf`, `README.md` con las versiones inmutables de `[[appium-gradle-version-matrix]]`. NO redefinir `aggregate`/`reports`/`clean` (`[[appium-no-aggregate-collision]]`).

### 5. Generar capa Screenplay
`LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage` bajo `co.com.pragma.*` siguiendo `[[appium-screenplay-layers]]`. Aplicar deferred locators (`[[appium-deferred-locators-strategy]]`).

### 6. Generar features
2 escenarios `@android @smoke` siempre + `@android @proposed` por cada item de `user_story`/`test_cases`. Cumplir `[[appium-gherkin-syntax-rules]]`. Detalle en `[[appium-smoke-vs-proposed-scenarios]]`.

### 7. Ejecutar health-check
14 stages estáticas + pipeline Gradle (`clean → compileJava → testClasses` mínimo). Calcular `generation_status` según `[[appium-health-check-pipeline]]`.

### 8. Validar 5 acceptance criteria
Exit 0 sin cambios manuales; cero colisiones; cero errores `compileJava`/`compileTestJava`; todos los `*.feature` parsean; `gradlew` ejecutable de primera.

### 9. Construir run command
`./gradlew clean test aggregate -p <project_path>` + variantes de `[[appium-run-and-tags]]`.

### 10. Reportar status
Entregar archivos con `[[calidad-streaming-files-protocol]]` solo si `generation_status = success`. Registrar trazabilidad por `[[calidad-test-evidence-and-traceability]]` y mapear casos según `[[calidad-route-test-generation]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Esta fase **extiende el health-check estático del paso 7** (14 stages + pipeline Gradle) con verificación de **runtime** real: instalar APK, levantar Appium server, correr los 2 escenarios `@android @smoke` y aplicar el loop de triage + auto-corrección. El health-check estático garantiza que el scaffold compila; este loop garantiza que arranca contra el binario real.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `scaffold-only` porque el paso 8 ya bloquea entrega si `generation_status != success`; el agente típicamente NO tiene emulador Android disponible. Subir a `full` sólo si el usuario confirma device/emulador + Appium server + APK válido. Clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) defaultean a `dry-run`. Si `scaffold-only`, reportar `partial` (el scaffold es válido, falta runtime).
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` cuando aplique: `./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`. Capturar `target/site/serenity/` como evidencia primaria.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky. Causas típicas: Appium server no responde, capabilities mal configuradas, APK no instalado, `app_package`/`app_activity` incorrectos (recordar TODO con `aapt dump badging`), locators diferidos aún en `TODO`.
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique (multi-locator fallback, accesibilidad como alternativa a `id`). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca eliminar el assert visual de `AppIsResponsive`, nunca reemplazar `TapOn` real por flags en memoria, nunca completar locators reales falsos (eso requiere Appium Inspector, ver `[[complete-deferred-locators]]`).
5. Reportar estado final: `success` (scaffold + smoke runtime pasa) | `partial` (scaffold válido, no se ejecutó runtime por falta de device/Appium server) | `failed` (escalado a humano con stage, logcat, screenshot Serenity, hipótesis).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. Recordar al usuario que los locators reales se completan con `[[complete-deferred-locators]]`.

## Criterios de finalización

1. `generation_status = success` (no `partial`, no `failed`).
2. Los 5 acceptance criteria pasan (`[[appium-health-check-pipeline]]`).
3. `build.gradle` NO redefine `aggregate`, `reports` ni `clean`.
4. Todos los `*.feature` parsean como Gherkin válido.
5. `gradlew` ejecutable de primera (mode 0755) o README documenta `chmod +x gradlew` / `sh ./gradlew`.
6. Los 2 escenarios `@android @smoke` ejecutables pasan en BUILD SUCCESSFUL sin selectores reales.
7. Reporte Serenity generado en `target/site/serenity/index.html`.
8. Si se aplicaron defaults `app_package=com.example.app` / `app_activity=.MainActivity`, el README lo declara como TODO con el comando `aapt dump badging`.
9. Health-check de runtime ejecutado al menos una vez (cuando hay device/Appium server). Estado: `success` / `partial` / `failed` reportado. `partial` es aceptable si el scaffold pasó health-check estático pero no hay device disponible.
10. Si hubo fallos en runtime: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada.
11. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Locators diferidos NUNCA se completaron con valores inventados (eso es `[[complete-deferred-locators]]`).
12. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando `./gradlew test` + checklist runtime pendiente entregados; ninguna corrección aplicada sin aprobación humana.
13. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@accessibility` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
