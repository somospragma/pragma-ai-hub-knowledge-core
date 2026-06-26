---
id: calidad-appium-screenplay-android
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium]
description: Genera proyecto Appium V2 Android con Screenplay + Serenity + Cucumber listo para ejecutarse de primera.
tags: [appium, mobile, android, screenplay, serenity, cucumber, gradle]
---

# Appium Screenplay Android

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto greenfield de pruebas mobile en Appium V2 sobre Android, usando el patrón Screenplay con Serenity BDD y Cucumber sobre Gradle. **El scaffolder V2 solo genera proyectos Android**: si el `platform_name` indica iOS, este skill rechaza la solicitud. Esto es una **limitación del auto-generador**, no del Chapter — Pragma's Chapter Calidad sí soporta Appium iOS mediante scaffold manual con el mismo patrón Screenplay. Ver la separación completa entre alcance del scaffolder y capacidad del chapter en `references/android-only-scope-rationale.md`.

Para extender un proyecto Appium existente (Android **o** iOS), usar `[[calidad-appium-brownfield]]`.

Antes de activar este skill confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Instrucción

1. **Validar inputs** — Aplica las 5 reglas de ``references/mandatory-inputs-validation.md``. Rechaza con mensaje exacto si falla. Coerciona "true"/"si"/"sí"/"yes"/"1" a booleano para `include_login_case`.
2. **Extraer metadata** — Normaliza defaults Android: `appium_server_url=http://127.0.0.1:4723`, `device_name=Android Emulator`, `automation_name=UiAutomator2`, `platform_version=12.0`, Java 21. Si falta `app_package`/`app_activity`, usa `com.example.app` / `.MainActivity` y deja TODO en el README con el comando `aapt dump badging`.
3. **Extraer selector templates** — Solo si el input `selectors` viene provisto. Mapea a `AppiumBy.id`, `AppiumBy.xpath` o `AppiumBy.accessibilityId`. Si no viene, sigue el patrón diferido de ``references/deferred-locators-strategy.md``.
4. **Generar Gradle scaffold** — Crea `build.gradle`, `settings.gradle`, wrapper (`gradlew`, `gradlew.bat`, `gradle-wrapper.properties`) usando las versiones inmutables de ``references/gradle-version-matrix.md``. Respeta las reglas de scope (Serenity/Appium en `implementation`, Cucumber/JUnit en `testImplementation`, Lombok en `compileOnly` + `annotationProcessor`).
5. **Generar capa Screenplay** — Crea las 4 capas (Task, Question, Interaction, UserInterface) bajo `co.com.pragma.*` siguiendo ``references/screenplay-layers.md``. Incluye `LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage` con locators diferidos marcados `// TODO: update real locator`.
6. **Generar escenarios** — Siempre 2 escenarios `@android @smoke` ejecutables (login base + carga/DOM). Si los inputs traen `user_story` o `test_cases`, agrega escenarios `@android @proposed` aspiracionales (opt-in). Aplica ``references/smoke-vs-proposed-scenarios.md`` y ``references/gherkin-syntax-rules.md``.
7. **Ejecutar health-check** — Aplica las 14 stages estáticas + el pipeline de compilación Gradle (`clean → compileJava → testClasses`, 300s timeout). Calcula `generation_status` según ``references/health-check-pipeline.md``.
8. **Construir run command** — `./gradlew clean test aggregate -p <project_path>`; documenta filtros por tag y override de `-Denv=staging` (ver `[[calidad-appium-run-and-tags]]`).
9. **Asegurar los 5 acceptance criteria** — Exit 0 sin cambios manuales; cero colisiones con `aggregate`/`reports`/`clean`; cero errores `compileJava`/`compileTestJava`; todos los `*.feature` parsean; `gradlew` ejecutable de primera (mode 0755).
10. **Entregar** — Solo si `generation_status = success`. Usa `[[calidad-streaming-files-protocol]]` y registra trazabilidad por `[[calidad-test-evidence-and-traceability]]`. Mapea casos con `[[calidad-route-test-generation]]`.

## Capacidades adicionales

Las siguientes capacidades aplican al proyecto generado y pueden activarse en escenarios `@proposed` o suites dedicadas:

- **Accesibilidad mobile (WCAG 2.1 AA).** Patrón Screenplay (`AccessibilityIssuesFound` Question + `AssertAccessibilityCompliance` Task) y herramientas (Accessibility Scanner, Espresso a11y, accessibility-test-framework). Detalle en `references/mobile-accessibility.md`. Tags `@accessibility @a11y @mobile`.
- **Regresión visual mobile.** Patrón Screenplay (`CaptureScreenshot` Interaction + `VisualMatchesBaseline` Question) con Applitools (`com.applitools.eyes.appium`) o Percy (`io.percy.appium`). Detalle en `references/mobile-visual-regression.md`. Tag `@visual`. Ejecutar en job dedicado del CI, no en cada test.

Para proyectos iOS, la misma capa Screenplay es portable; solo cambia el set de selectores y capabilities. Ver guidance en `references/android-only-scope-rationale.md`.

## Salidas

Estructura completa Gradle + Screenplay en ``references/project-structure.md``. La fuente autoritativa del contenido textual de los archivos clave está en `references/templates/`:

- `build.gradle` — matriz inmutable de versiones + scopes correctos.
- `gradle-wrapper.properties` — distribution URL Gradle 8.10.
- `gradlew` — nota operativa (el script lo genera `gradle wrapper`, no el agente).
- `junit-platform.properties` — naming-strategy, plugin, glue, features path.
- `LoginRunner.java` — runner canónico filtrado por `@smoke`.

```
{project_name}/
├── build.gradle
├── settings.gradle
├── gradlew + gradlew.bat
├── gradle/wrapper/gradle-wrapper.properties
├── serenity.properties
├── android.conf
├── README.md
└── src/
    ├── main/java/co/com/pragma/{tasks,questions,interactions,userinterfaces,models,utils}/
    └── test/
        ├── java/co/com/pragma/{runners,stepdefinitions}/
        └── resources/{serenity.conf, logback-test.xml, junit-platform.properties, features/}
```

## Restricciones

- **Scaffolder Android-only (V2).** Si `platform_name` (cuando viene) en minúsculas no es `"android"`, este skill responde exactamente `"En Appium V2 solo se soporta Android."` y aborta el scaffolding automático. Esto NO impide trabajar en iOS: el chapter soporta iOS Appium con scaffold manual (ver `references/android-only-scope-rationale.md`) o brownfield iOS via `[[calidad-appium-brownfield]]`.
- **JAMÁS redefinir la tarea `aggregate`.** El plugin `serenity-gradle-plugin` 4.1.14 ya la registra. Prohibido `task aggregate { ... }` o `tasks.register('aggregate') { ... }`. Lo mismo aplica a `reports` y `clean`. Solo se permite `tasks.named('aggregate') { ... }`. Ver ``references/no-aggregate-collision.md``.
- **Locators diferidos son deuda explícita.** El scaffold ship con `// TODO: update real locator` y `LoginTask.performAs` no invoca gestos UI reales. `@smoke` debe pasar SIN selectores finales (BUILD SUCCESSFUL). Riesgo y mitigación en ``references/deferred-locators-strategy.md`` y workflow `[[calidad-complete-deferred-locators]]`.
- **No mover Serenity/Appium a `testImplementation`** — rompe `compileJava` cuando la capa Screenplay vive en `src/main/java`. Ver ``references/gradle-version-matrix.md``.
- **No usar `OnStage.setTheStage(OnlineCast.whereEveryoneCan(...))`.** Ambigüedad de sobrecargas en Serenity 4.1.14. Usar `new OnlineCast()`.
- **No `# note` inline tras step keyword.** Gherkin lo rechaza. Comentarios solo al inicio de línea.
- **Package declarations deben coincidir con el path físico** (`co.com.pragma.tasks` → `src/main/java/co/com/pragma/tasks/`). De lo contrario, cascade de `cannot find symbol` en `compileJava`.
- **`build.gradle` DEBE seguir la matriz inmutable** de ``references/gradle-version-matrix.md`` y ``references/templates.md` (sección `build.gradle`)`: Serenity 4.1.14, Appium Java Client 8.6.0, Cucumber JUnit Platform 7.14.0, JUnit Jupiter 5.10.2, JUnit Platform Suite 1.10.2.
- **Wrapper Gradle obligatorio** (`gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.properties`, `gradle/wrapper/gradle-wrapper.jar`) generado con `gradle wrapper --gradle-version 8.10`. `gradlew` con permisos `0755`.
- **JUnit Platform obligatorio**: `useJUnitPlatform()` en `test { }`. NO `useJUnit()` (eso es JUnit 4 y rompe Cucumber JUnit Platform).
- **Scopes correctos**: src/main → `implementation` (Serenity Core/Cucumber/Screenplay/Screenplay-WebDriver, Appium Java Client, SLF4J, Logback). Tests → `testImplementation` (Cucumber JUnit Platform engine, JUnit Platform Suite, JUnit Jupiter, AssertJ). Lombok → `compileOnly` + `annotationProcessor`.
- **`junit-platform.properties` obligatorio** en `src/test/resources/` con `cucumber.glue`, `cucumber.features`, `cucumber.plugin`, `cucumber.junit-platform.naming-strategy=long`. Ver ``references/templates.md` (sección `junit-platform.properties`)`.
- **Runner canónico `LoginRunner`** (`co.com.pragma.runners.LoginRunner`) con `@Suite + @IncludeEngines("cucumber") + @SelectClasspathResource("features")` y filtro `@smoke`. Ver ``references/templates.md` (sección `LoginRunner.java`)`.
- **Step isolation obligatorio** cuando el escenario tiene setup/auth/main/cleanup: Tasks separadas para Setup vs Main; Questions de dominio (contractuales) evaluadas SOLO en main; cleanup en `@After` con falla no-fatal. La cobertura sólo cuenta escenarios `@main-step`. Detalle en `references/step-isolation-appium.md`.
- **Questions contractuales obligatorias** para validar datos del dominio: regla "no sólo `displayed()`" — usar Questions que devuelvan valores específicos (`rowCount`, `firstRowAmountText`, `paginationText`) comparados con matchers explícitos. Detalle, tabla por tipo de pantalla y anti-patterns en `references/contractual-questions.md`.
- Aplica `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]` y `[[calidad-delivery-gate-contract]]` para declarar/verificar la matriz de versiones y la presencia del wrapper antes de cerrar la entrega.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]`.
