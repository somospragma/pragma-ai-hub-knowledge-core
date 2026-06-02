---
id: appium-brownfield
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium]
description: Extiende un proyecto Appium existente con nuevos escenarios, Tasks, Questions, o cambios de selectores respetando convenciones del proyecto.
tags: [appium, brownfield, mobile, screenplay, conventions]
---

# Appium Brownfield

## Cuándo aplicar

Cuando el usuario provee un **proyecto Appium ya inicializado** (Android **o** iOS) y solicita uno de los siguientes cambios:

- Agregar nuevos escenarios `@proposed` para historias adicionales sin tocar la infraestructura existente.
- Agregar nuevas Tasks, Questions, Interactions o UserInterfaces a la capa Screenplay actual.
- Actualizar selectores tras un cambio de UI o nueva versión de la app.
- Refactor localizado de Screenplay (renombrar Task, mover método, extraer Question) sin reescribir el runner ni el build.

Si el proyecto **no existe** todavía, no aplicar este skill: usar el scaffolder greenfield `[[appium-screenplay-android]]` para Android, o el workaround manual descrito en `references/android-only-scope-rationale.md` para iOS. Decisión brownfield vs greenfield en `[[calidad-brownfield-vs-greenfield]]`.

Antes de activar este skill, confirma intent con `[[calidad-intent-detection]]` y recolecta inputs obligatorios con `[[calidad-mandatory-inputs-protocol]]`. Aplica la perspectiva del chapter en `[[calidad-chapter-perspective]]`.

## Instrucción

1. **Recolectar inputs** — Exige los siguientes inputs:
   - `project_root` (ruta absoluta al proyecto Appium existente).
   - `change_type` ∈ {`new-scenario`, `new-page`, `selector-update`, `refactor`}.
   - `change_description` (qué se quiere agregar/modificar; user story, screenshot, nuevos selectores, etc.).
   - Opcionales según `change_type`: `new_apk_path` (si cambió el binario), `new_selectors` (mapa nombre → selector real), `new_user_story` (para `new-scenario`).
   Si falta cualquiera de los obligatorios, detente y solicítalos vía `[[calidad-mandatory-inputs-protocol]]`.
2. **Analizar proyecto existente** — Recorre el árbol bajo `project_root`. Detecta:
   - `build_system`: `gradle` (presencia de `build.gradle` + `settings.gradle` + `gradlew`) o `maven` (`pom.xml`).
   - `base_package`: paquete Java declarado en el runner Cucumber (`co.com.pragma`, `com.client.tests`, `com.empresa.qa.mobile`, etc.).
   - `screenplay_layers_present`: cuáles de `tasks/`, `questions/`, `interactions/`, `userinterfaces/` ya existen.
   - `cucumber_runner_class`: nombre y path del runner (`CucumberTestRunner`, `RunCucumberTest`, etc.).
   - `gherkin_language`: leyendo `# language: en|es` en los `.feature` o el default observado.
3. **Detectar convenciones** — Aplica `references/convention-detection.md` para extraer el objeto completo de convenciones (naming de features, tags estándar, plataforma detectada Android/iOS, pages existentes, runner filter tags). Este objeto es el contrato del paso 4.
4. **Generar SOLO lo solicitado** — Según `change_type`:
   - `new-scenario`: emitir `.feature` nuevo (o append a `.feature` existente, respetando estilo) y, si es necesario, Tasks/Questions/Pages nuevas. Reusar Tasks/Questions existentes cuando cubran el flujo.
   - `new-page`: emitir UserInterface + Tasks asociadas + Questions asociadas + (opcional) escenarios `@proposed`.
   - `selector-update`: aplicar `references/selector-update-strategy.md`. Solo cambian asignaciones `Target.the(...).located(...)`. Métodos, signatures, comentarios, imports y orden permanecen literales.
   - `refactor`: cambios mínimos enfocados; no introducir nuevas capas ni renombrar paquetes.
5. **NO modificar build/infra** — `build.gradle`, `settings.gradle`, `pom.xml`, `gradlew`, `serenity.conf`, `serenity.properties`, `junit-platform.properties`, `logback-test.xml`, runner Cucumber existente: NO se tocan. Excepción única: si el cambio requiere una dependencia nueva (ej. una librería de visual regression), se reporta al usuario para que apruebe la edición puntual del `build.gradle`/`pom.xml`; no se decide unilateralmente.
6. **Validar coherencia** — Antes de entregar:
   - Validar Gherkin (`[[appium-gherkin-syntax-rules]]`) en cada `.feature` nuevo o tocado.
   - Validar que el `package` de cada `.java` nuevo coincide con el path físico bajo `base_package` detectado.
   - Validar que los tags usados son subset o extensión coherente de los `scenario_tag_conventions` detectados.
   - Validar que el `gherkin_language` se respetó.
7. **Comando run** — Reportar al usuario el comando de ejecución filtrado por el tag de la nueva historia, usando el build system detectado y las convenciones de `[[appium-run-and-tags]]`. Entregar archivos con `[[calidad-streaming-files-protocol]]` y trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

## Salidas

- Cero o más `.feature` nuevos o modificados en `features_dir` detectado.
- Cero o más `*.java` nuevos o modificados bajo `base_package` (Tasks, Questions, Interactions, UserInterfaces).
- **Ningún** archivo de infraestructura modificado salvo aprobación explícita por nueva dependencia.

## Restricciones

- **NUNCA** regenerar `build.gradle`, `settings.gradle`, `pom.xml`, `gradlew`, `gradlew.bat`, `gradle-wrapper.properties`, `serenity.conf`, `serenity.properties`, `junit-platform.properties`, `logback-test.xml`, ni el runner Cucumber existente, salvo solicitud explícita del usuario.
- **Respetar 100% el `base_package` detectado.** No introducir `co.com.pragma` si el proyecto usa `com.client.tests`.
- **Preservar tags existentes.** Si el proyecto usa `@smoke @regression @mobile`, los nuevos escenarios usan el mismo set; los nuevos tags propios (`@user-story:HUT-XXX`) se agregan sin reemplazar.
- **Preservar `gherkin_language` detectado.** No cambiar `en` por `es` ni viceversa, aunque el chapter prefiera uno; el proyecto manda.
- **Soporta Android y iOS.** La plataforma se detecta del `serenity.conf`/`android.conf`/`ios.conf` y de las capabilities (`automationName=UiAutomator2` → Android, `automationName=XCUITest` → iOS). Para iOS, los selectores nuevos usan `AppiumBy.iOSClassChain`, `AppiumBy.iOSNsPredicateString` o `AppiumBy.accessibilityId` (ver `references/android-only-scope-rationale.md` del skill greenfield para guidance).
- **No introducir dependencias nuevas** salvo que el feature lo requiera y el usuario lo apruebe.
- **No "mejorar" el estilo del proyecto.** Si los Page Objects existentes no usan Lombok pero el chapter sí, no introducir Lombok aquí.
- Entrega los archivos usando `[[calidad-streaming-files-protocol]]`.
