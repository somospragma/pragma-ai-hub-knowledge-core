---
id: extend-appium-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Flujo para extender un proyecto Appium existente (Android o iOS) con nuevos escenarios, pages o selector updates respetando convenciones detectadas.
tags: [appium, brownfield, workflow, mobile, screenplay, conventions]
---

# Workflow — Extender proyecto Appium brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` identifica una solicitud de automatización mobile Appium y `[[calidad-brownfield-vs-greenfield]]` la clasifica como **brownfield**: el usuario provee archivos de un proyecto Appium existente (Android o iOS) y solicita extenderlo. Para greenfield Android usar `[[generate-appium-screenplay-android]]`; para greenfield iOS, scaffold manual descrito en `references/android-only-scope-rationale.md` del skill `[[appium-screenplay-android]]`.

## Inputs

| Input                 | Obligatorio | Notas                                                                                                |
|-----------------------|-------------|------------------------------------------------------------------------------------------------------|
| `project_root`        | Sí          | Ruta absoluta al proyecto Appium existente (debe contener `build.gradle`/`pom.xml` + features).      |
| `change_type`         | Sí          | Uno de: `new-scenario`, `new-page`, `selector-update`, `refactor`.                                   |
| `change_description`  | Sí          | Qué se quiere agregar/modificar (user story, screenshot, mapa de nuevos selectores).                 |
| `new_apk_path`        | No          | Solo si `change_type` involucra una nueva versión del binario Android.                               |
| `new_selectors`       | No          | Mapa `nombre → selector real`, requerido en `selector-update`.                                       |
| `new_user_story`      | No          | Texto de la historia, requerido en `new-scenario` para tag `@user-story:<ID>`.                       |
| `firma`               | No          | Documento técnico complementario.                                                                    |

Recolectar inputs siguiendo `[[calidad-mandatory-inputs-protocol]]`. Si falta un obligatorio, detente y solicítalo.

## Pasos

### 1. Analizar proyecto existente
Recorrer `project_root`. Detectar `build_system` (Gradle vs Maven), presencia del runner Cucumber, features dir, layers Screenplay presentes. Si el árbol no luce como un proyecto Appium válido, detente y repórtalo.

### 2. Detectar plataforma (Android / iOS)
Leer `serenity.conf`/`android.conf`/`ios.conf` y/o las capabilities embebidas en código. Mapear:
- `automationName = UiAutomator2` → `platform_detected = android`.
- `automationName = XCUITest` → `platform_detected = ios`.
Si no se puede inferir, preguntar al usuario antes de continuar. Esta detección determina qué selectores se usan en pasos posteriores.

### 3. Detectar convenciones
Aplicar `references/convention-detection.md` del skill `[[appium-brownfield]]`. Producir el objeto completo: `base_package`, `cucumber_runner_class`, `runner_filter_tags`, `gherkin_language`, `feature_naming_pattern`, `scenario_tag_conventions`, `existing_pages`, `features_dir`, `step_definitions_dir`. **Output obligatorio antes de generar nada.**

### 4. Si `change_type = selector-update`: aplicar selector-update-strategy
Aplicar `references/selector-update-strategy.md`. Cambiar SOLO las asignaciones `Target.the(...).located(...)` en los `UserInterface` afectados. Mantener nombres de constantes, descripciones, métodos helper, imports, package, orden. NO tocar Tasks ni Questions consumidoras. Para iOS usar `AppiumBy.iOSClassChain`/`iOSNsPredicateString`/`accessibilityId`; para Android `AppiumBy.id`/`xpath`/`accessibilityId`.

### 5. Si `change_type = new-scenario`: generar feature respetando gherkin_language detectado
Emitir `.feature` nuevo (o append al existente si así lo dicta el proyecto) en `features_dir`, con:
- Línea `# language: {gherkin_language}` cuando el proyecto la declara explícitamente.
- Keywords `Feature/Scenario/Given/When/Then` o `Característica/Escenario/Dado/Cuando/Entonces` coherentes con `gherkin_language`.
- Tags = `scenario_tag_conventions` detectados + `@proposed` + `@user-story:<ID>` derivado de `new_user_story`.
- Naming del archivo siguiendo `feature_naming_pattern` detectado.
Cumplir `[[appium-gherkin-syntax-rules]]` y `[[appium-smoke-vs-proposed-scenarios]]`.

### 6. Si `change_type ∈ {new-page, new-scenario}`: preservar package coherence
Cualquier `*.java` nuevo (Task, Question, Interaction, UserInterface, step definition) debe:
- Declarar `package {base_package}.{layer};` exactamente coincidente con el path físico.
- Vivir bajo `src/main/java/{base_package_as_path}/{layer}/` (o `src/test/java/...` para step definitions).
- Importar tipos Appium/Serenity con los mismos alias que usan los archivos existentes.
- Reusar Tasks/Questions/Interactions existentes cuando cubran el flujo; no duplicar lógica.

### 7. Validar Gherkin
Para cada `.feature` nuevo o tocado: parse Gherkin debe pasar (no comentarios `# ...` después de step keyword, no celdas `Examples` vacías, no `Scenario Outline` sin `Examples`). Reglas completas en `[[appium-gherkin-syntax-rules]]`.

### 8. Comando run con tag filter detectado
Construir el comando de ejecución usando `build_system` y `runner_filter_tags` detectados, agregando el tag de la nueva historia:
- Gradle: `./gradlew clean test aggregate -p {project_root} -Dcucumber.filter.tags="@user-story:<ID>"`.
- Maven: `mvn clean verify -f {project_root}/pom.xml -Dcucumber.filter.tags="@user-story:<ID>"`.
Variantes y overrides en `[[appium-run-and-tags]]`.

Entrega los archivos con `[[calidad-streaming-files-protocol]]` y registra trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

## Criterios de finalización

- [ ] Objeto de convenciones extraído y documentado en el reporte de salida.
- [ ] `platform_detected` registrado (`android` o `ios`) y los selectores nuevos usan la API idiomática de esa plataforma.
- [ ] **Ningún** archivo de infraestructura Gradle/Maven/Serenity fue modificado (`build.gradle`, `settings.gradle`, `pom.xml`, `gradlew`, `serenity.conf`, `serenity.properties`, `junit-platform.properties`, `logback-test.xml`, runner Cucumber existente).
- [ ] Convenciones detectadas respetadas al 100%: `base_package`, `gherkin_language`, `scenario_tag_conventions`, `feature_naming_pattern`, `runner_filter_tags`.
- [ ] En `selector-update`: solo cambian las asignaciones `Target.the(...).located(...)`. Métodos, imports, package, nombres y orden preservados. Tasks/Questions consumidoras intactas.
- [ ] Cada `.feature` nuevo o tocado parsea como Gherkin válido.
- [ ] Cada `*.java` nuevo: `package` coincide con path físico bajo `base_package`.
- [ ] Comando de ejecución filtrado por el tag de la nueva historia provisto en la entrega.
- [ ] No se introdujeron dependencias nuevas sin aprobación explícita.
