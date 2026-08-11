---
id: calidad-appium-screenplay-android
version: 1.1.0
scope: stack
type: skill
chapter: calidad
stack: [appium-serenity]
description: Genera proyecto Appium Android sobre JVM con Serenity + Cucumber, en patrón Screenplay (por defecto) o Page Object Model, listo para ejecutarse de primera.
tags: [appium, mobile, android, screenplay, pom, serenity, cucumber, gradle, jvm]
---

# Appium Screenplay Android

## Cuándo aplicar

Cuando el usuario solicita generar un proyecto greenfield de pruebas mobile en Appium sobre **JVM**: Serenity BDD y Cucumber sobre Gradle.

**Patrón de diseño**: el stack soporta **Screenplay** (por defecto del chapter) y **Page Object Model**. Se pregunta al usuario cuál usar cuando no lo declara, y en brownfield **manda el patrón que el proyecto ya usa** — introducir Screenplay en un proyecto POM, o al revés, produce dos modelos conviviendo y es motivo de rechazo en revisión. Las capas de Screenplay están en `references/screenplay-layers.md`; con POM, la capa de objetos de pantalla cumple el mismo rol y el resto del scaffold (Gradle, runner, reportería, tags) es idéntico.

**Este stack requiere `appium-core` instalado**: el conocimiento mobile que no depende del lenguaje —resolución de locators, comportamiento de Flutter, catálogo de interacciones, auto-discovery de APK— vive ahí y no se duplica aquí. Si no está, decláralo como carencia: sin el protocolo de locators se generan selectores plausibles en vez de verificados. **El scaffolder V2 solo genera proyectos Android**: si el `platform_name` indica iOS, este skill rechaza la solicitud. Esto es una **limitación del auto-generador**, no del Chapter — Pragma's Chapter Calidad sí soporta Appium iOS mediante scaffold manual con el mismo patrón Screenplay. Ver la separación completa entre alcance del scaffolder y capacidad del chapter en `references/android-only-scope-rationale.md`.

Para extender un proyecto Appium existente (Android **o** iOS), usar `[[calidad-appium-brownfield]]`.

Antes de activar este skill confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Lectura obligatoria antes de generar

Este SKILL es el índice; el detalle que hace funcionar el proyecto vive en `references/`. **Abrir estos archivos ANTES de emitir el primer archivo** y declarar en el turno cuáles se leyeron (queda en la traza del pipeline):

| Reference | Para qué |
|---|---|
| `references/gradle-version-matrix.md` | Versiones y scopes (fuente de verdad sobre los templates) |
| `references/templates.md` | Contenido textual de build.gradle, serenity.conf, Hooks, runner, junit-platform.properties |
| [[calidad-mobile-locator-resolution]] | Cómo resolver locators ANTES de escribir Targets (stack `appium-core`) |
| [[calidad-mobile-interactions]] | Escritura, taps, scroll, esperas, recuperación (stack `appium-core`) |
| `references/mobile-evidence-and-triage.md` | Instrumentación previa y orden de triage |
| [[calidad-mobile-locator-resolution]] (`references/flutter-under-appium.md`) | Solo si la app es Flutter o hay prototipo |

Ignorar esta lectura es la causa raíz verificada de una PoC completa: el agente redescubrió por ensayo y error —y reportó como defectos del chapter— cosas ya escritas en estas references, incluida una que su propio insumo le daba resuelta.

## Reglas duras (no negociables, resumen de las references)

1. **Locators**: `AppiumBy.id` NO resuelve `Semantics(identifier:)` de Flutter → `androidUIAutomator` con `resourceId` **anclado** (un `resourceIdMatches` parcial matchea también `..._label`). El identificador da identidad, no capacidad: el nodo capaz suele ser un descendiente. Conteo de nodos válido = 1.
2. **Texto en Flutter**: `getText()` devuelve vacío; el texto visible está en `content-desc`. Centralizar en un único helper, nunca leer atributos ad hoc por Question.
3. **Cast**: `Cast.ofStandardActors()` + `webdriver.driver=provided` + `webdriver.autodownload=false`. `OnlineCast` dispara ChromeDriver y abre Chrome en cada corrida.
4. **Runner**: uno solo, **sin tags hardcodeados**; el filtro llega por CLI. Sin defaults de tags en `build.gradle`.
5. **Reportería**: `SerenityReporter` primero en `cucumber.plugin`, `junit-vintage` presente, `aggregate` no UP-TO-DATE, sin `cucumber.features`. Verificar el conteo del reporte contra lo diseñado en la primera corrida.
6. **Imports Serenity 4.x**: `net.serenitybdd.annotations.Step`, `net.thucydides.model.util.EnvironmentVariables`. `Ensure` requiere la dependencia `serenity-ensure` (existe; no está "eliminada").
7. **Evidencia primero**: screenshot → page source como árbol → log del mock → recién entonces hipótesis. Instrumentar ANTES de la primera corrida.
8. **JDK 21 no se degrada**: si falta, el toolchain lo descarga; bajar la matriz por conveniencia está prohibido.

## Instrucción

1. **Validar inputs** — Aplica las 5 reglas de ``references/mandatory-inputs-validation.md``. Rechaza con mensaje exacto si falla. Coerciona "true"/"si"/"sí"/"yes"/"1" a booleano para `include_login_case`.
2. **Extraer metadata** — Normaliza defaults Android: `appium_server_url=http://127.0.0.1:4723`, `device_name=Android Emulator`, `automation_name=UiAutomator2`, `platform_version=12.0`, Java 21. Si falta `app_package`/`app_activity`, usa `com.example.app` / `.MainActivity` y deja TODO en el README con el comando `aapt dump badging`.
3. **Extraer selector templates** — Solo si el input `selectors` viene provisto. Mapea a `AppiumBy.xpath`, `AppiumBy.accessibilityId`, `androidUIAutomator` o `AppiumBy.id` **aplicando el protocolo de resolución de [[calidad-mobile-locator-resolution]]** (en apps Flutter, `AppiumBy.id` NO resuelve `Semantics(identifier:)` — verificado en campo). Si no viene, sigue el patrón diferido de ``references/deferred-locators-strategy.md``.
4. **Generar Gradle scaffold** — Crea `build.gradle`, `settings.gradle`, wrapper (`gradlew`, `gradlew.bat`, `gradle-wrapper.properties`) usando las versiones inmutables de ``references/gradle-version-matrix.md``. Respeta las reglas de scope (Serenity/Appium en `implementation`, Cucumber/JUnit en `testImplementation`, Lombok en `compileOnly` + `annotationProcessor`).
5. **Generar capa Screenplay** — Crea las 4 capas (Task, Question, Interaction, UserInterface) bajo `co.com.pragma.*` siguiendo ``references/screenplay-layers.md`` y el repertorio de `[[calidad-mobile-interactions]]` (canon de escritura Click→Enter→HideKeyboard, esperas por presencia de ancla, Check.whether para condicionales). Incluye `LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage` con locators diferidos marcados `// TODO: update real locator`.
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
- `junit-platform.properties` — naming-strategy, plugin (SerenityReporter primero), glue; SIN `cucumber.features`.
- `serenity.conf` — bloque `appium{}` con claves sin prefijo, `app` con ruta absoluta, screenshots AFTER_EACH_STEP.
- `Hooks.java` — evidencia por fallo (screenshot + page source) y purga del mock entre escenarios cuando aplica.
- `SuiteRunner.java` — runner ÚNICO, sin tags hardcodeados (el filtro llega por CLI).

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
- **NUNCA usar `OnlineCast` en proyectos Appium** (ni `new OnlineCast()` ni `OnlineCast.whereEveryoneCan(...)`): Serenity intenta crear un ChromeDriver además del driver de Appium y abre Chrome en cada corrida. Usar `OnStage.setTheStage(Cast.ofStandardActors())` + `webdriver.driver=provided` + `webdriver.autodownload=false`, y asignar el AndroidDriver al actor en el hook.
- **Triage con evidencia primero.** Ante cualquier fallo de UI: screenshot → page source parseado como árbol → log del mock/backend → recién entonces hipótesis. Protocolo completo, reglas de método y checklist de verificación de reportería en ``references/mobile-evidence-and-triage.md``. La reportería se verifica en la PRIMERA corrida (los falsos verdes de reportería son indetectables leyendo el reporte).
- **No `# note` inline tras step keyword.** Gherkin lo rechaza. Comentarios solo al inicio de línea.
- **Package declarations deben coincidir con el path físico** (`co.com.pragma.tasks` → `src/main/java/co/com/pragma/tasks/`). De lo contrario, cascade de `cannot find symbol` en `compileJava`.
- **`build.gradle` DEBE seguir la matriz inmutable** de ``references/gradle-version-matrix.md`` y ``references/templates.md` (sección `build.gradle`)`: Serenity 4.1.14, Appium Java Client 8.6.0, Cucumber JUnit Platform 7.14.0, JUnit Jupiter 5.10.2, JUnit Platform Suite 1.10.2.
- **Wrapper Gradle obligatorio** (`gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.properties`, `gradle/wrapper/gradle-wrapper.jar`) generado con `gradle wrapper --gradle-version 8.10`. `gradlew` con permisos `0755`.
- **JUnit Platform obligatorio**: `useJUnitPlatform()` en `test { }`. NO `useJUnit()` (eso es JUnit 4 y rompe Cucumber JUnit Platform).
- **Scopes correctos**: src/main → `implementation` (Serenity Core/Cucumber/Screenplay/Screenplay-WebDriver, Appium Java Client, SLF4J, Logback). Tests → `testImplementation` (Cucumber JUnit Platform engine, JUnit Platform Suite, JUnit Jupiter, AssertJ). Lombok → `compileOnly` + `annotationProcessor`.
- **`junit-platform.properties` obligatorio** en `src/test/resources/` con `cucumber.glue`, `cucumber.plugin` (con `io.cucumber.core.plugin.SerenityReporter` en PRIMERA posición — sin él los pasos "pasan" sin ejecutarse) y `cucumber.junit-platform.naming-strategy=long`. **PROHIBIDO `cucumber.features`** (anula los selectores del `@Suite` y el filtro de tags — el smoke gate dejaría de existir). Ver ``references/templates.md` (sección `junit-platform.properties`)`.
- **Runner ÚNICO `SuiteRunner`** (`co.com.pragma.runners.SuiteRunner`) con `@Suite + @IncludeEngines("cucumber") + @SelectClasspathResource("features")` y **sin** `FILTER_TAGS_PROPERTY_NAME`: un tag fijo en el runner sobreescribe el de la CLI. Prohibido crear runners adicionales. Ver ``references/templates.md` (sección `SuiteRunner.java`)`.
- **Step isolation obligatorio** cuando el escenario tiene setup/auth/main/cleanup: Tasks separadas para Setup vs Main; Questions de dominio (contractuales) evaluadas SOLO en main; cleanup en `@After` con falla no-fatal. La cobertura sólo cuenta escenarios `@main-step`. Detalle en `references/step-isolation-appium.md`.
- **Questions contractuales obligatorias** para validar datos del dominio: regla "no sólo `displayed()`" — usar Questions que devuelvan valores específicos (`rowCount`, `firstRowAmountText`, `paginationText`) comparados con matchers explícitos. Detalle, tabla por tipo de pantalla y anti-patterns en [[calidad-mobile-interactions]] (`references/contractual-assertions.md`).
- Aplica `[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]` y `[[calidad-delivery-gate-contract]]` para declarar/verificar la matriz de versiones y la presencia del wrapper antes de cerrar la entrega.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]`.
