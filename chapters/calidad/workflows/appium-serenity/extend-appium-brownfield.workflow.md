---
id: calidad-extend-appium-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [appium-serenity]
description: Flujo para extender un proyecto Appium existente (Android o iOS) con nuevos escenarios, pages o selector updates respetando convenciones detectadas.
tags: [appium, brownfield, workflow, mobile, screenplay, conventions]
---

# Workflow — Extender proyecto Appium brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` identifica una solicitud de automatización mobile Appium y `[[calidad-brownfield-vs-greenfield]]` la clasifica como **brownfield**: el usuario provee archivos de un proyecto Appium existente (Android o iOS) y solicita extenderlo. Para greenfield Android usar `[[calidad-generate-appium-screenplay-android]]`; para greenfield iOS, scaffold manual descrito en `references/android-only-scope-rationale.md` del skill `[[calidad-appium-screenplay-android]]`.

### Pre-flight (OBLIGATORIO)

Antes de cualquier acción, ejecutar [[calidad-appium-screenplay-android]] (consultar `references/preflight.md` en su subfolder) del stack. En brownfield aplica los mismos checks de versión/tooling. Si falla → degradar a `scaffold-only` con razón documentada.

Cumplir el protocolo `[[calidad-pre-generation-protocol]]` incluso en brownfield: confirmar inputs (incluido `modo`), declarar coverage de los archivos NUEVOS (no de los preexistentes), esperar confirmación del usuario.

### Regla brownfield específica — Auto-corrección

La auto-corrección y self-healing aplican EXCLUSIVAMENTE a los archivos NUEVOS que este workflow genera. Los archivos preexistentes del cliente (tests, Page Objects, fixtures, configs) son INTOCABLES bajo ningún concepto, aunque fallen. Si tests preexistentes fallan en la ejecución:

1. Reportar el fallo al usuario con triage (deterministic vs flaky).
2. NUNCA modificar el test preexistente.
3. NUNCA modificar fixtures, data o configs preexistentes para hacer pasar tests.
4. Escalar a humano con el contexto completo del fallo.

Esta regla es non-negotiable y es enforcement obligatorio del `[[calidad-test-self-correction-loop]]` y sus `references/anti-cheating-guardrails.md`.

Refuerzos adicionales:
- **Step isolation** (ver `[[calidad-step-isolation-pattern]]`) aplica a las Tasks/Questions/Interactions y `.feature` NUEVOS. Los archivos preexistentes mantienen su estructura aunque no cumplan el patrón; no se les aplica refactor.
- **Validación contractual no superficial** según [[calidad-appium-screenplay-android]] (consultar [[calidad-mobile-interactions]] (`references/contractual-assertions.md`)) aplica solo a Questions/scenarios nuevos. NO re-escribir aserciones de Questions preexistentes.
- **Auto-discovery APK**: si el proyecto preexistente ya tiene Page Objects (UserInterfaces) con selectores reales, NO re-correr auto-discovery sobre el APK ni reemplazar selectores existentes. Auto-discovery aplica únicamente a los UserInterfaces NUEVOS generados en esta sesión.

### Paso previo — Análisis condicional con STRATEGY.md

Si el alcance del brownfield es **grande** (≥3 escenarios/HUs/pages nuevos, o `selector-update` masivo cross-cutting): generar `STRATEGY.md` según el template [[calidad-appium-screenplay-android]] (template en ``references/templates.md` (sección `STRATEGY.md`)`) y el skill `[[calidad-pre-design-strategy-document]]`. Esperar aprobación del usuario antes de continuar.

Si el alcance es **pequeño** (1-2 cambios puntuales, p. ej. un selector-update aislado o un único `new-page`): omitir STRATEGY.md y proceder directo a generación, documentando la decisión en `.evidence/scope-decision.md`.

Respetar convenciones del proyecto cliente: el STRATEGY del brownfield documenta lo NUEVO, no rediseña lo existente. Respetar `platform_detected` (Android/iOS) y la API idiomática de selectores correspondiente.

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

### Paso 0 — Leer la traza del pipeline (SIEMPRE)

Aplica `[[calidad-pipeline-state-tracking]]` antes de tocar nada: si el `project_root`/`output_path` ya tiene `.evidence/pipeline-state.json`, leerlo y abrir el turno reportando fase actual, pendientes, bloqueos y `open_corrections`. Si no existe, crearlo con las fases de la ruta brownfield en `pending`. Actualizarlo al cerrar cada fase, con evidencia.

En brownfield el riesgo de perder el hilo es MAYOR que en greenfield: son sesiones largas sobre proyectos grandes del cliente, que es justo donde el contexto se llena y el proceso se fragmenta.


### 1. Analizar proyecto existente
Recorrer `project_root`. Detectar `build_system` (Gradle vs Maven), presencia del runner Cucumber, features dir, layers Screenplay presentes. Si el árbol no luce como un proyecto Appium válido, detente y repórtalo.

### 2. Detectar plataforma (Android / iOS)
Leer `serenity.conf`/`android.conf`/`ios.conf` y/o las capabilities embebidas en código. Mapear:
- `automationName = UiAutomator2` → `platform_detected = android`.
- `automationName = XCUITest` → `platform_detected = ios`.
Si no se puede inferir, preguntar al usuario antes de continuar. Esta detección determina qué selectores se usan en pasos posteriores.

### 3. Detectar convenciones
Aplicar `references/convention-detection.md` del skill `[[calidad-appium-brownfield]]`. Producir el objeto completo: `base_package`, `cucumber_runner_class`, `runner_filter_tags`, `gherkin_language`, `feature_naming_pattern`, `scenario_tag_conventions`, `existing_pages`, `features_dir`, `step_definitions_dir`. **Output obligatorio antes de generar nada.**

### 4. Si `change_type = selector-update`: aplicar selector-update-strategy
Aplicar `references/selector-update-strategy.md`. Cambiar SOLO las asignaciones `Target.the(...).located(...)` en los `UserInterface` afectados. Mantener nombres de constantes, descripciones, métodos helper, imports, package, orden. NO tocar Tasks ni Questions consumidoras. Para iOS usar `AppiumBy.iOSClassChain`/`iOSNsPredicateString`/`accessibilityId`; para Android `AppiumBy.id`/`xpath`/`accessibilityId`.

### 5. Si `change_type = new-scenario`: generar feature respetando gherkin_language detectado
Emitir `.feature` nuevo (o append al existente si así lo dicta el proyecto) en `features_dir`, con:
- Línea `# language: {gherkin_language}` cuando el proyecto la declara explícitamente.
- Keywords `Feature/Scenario/Given/When/Then` o `Característica/Escenario/Dado/Cuando/Entonces` coherentes con `gherkin_language`.
- Tags = `scenario_tag_conventions` detectados + `@proposed` + `@user-story:<ID>` derivado de `new_user_story`.
- Naming del archivo siguiendo `feature_naming_pattern` detectado.
Cumplir `[[calidad-appium-screenplay-android]] (consultar `references/gherkin-syntax-rules.md` en su subfolder)` y `[[calidad-appium-screenplay-android]] (consultar `references/smoke-vs-proposed-scenarios.md` en su subfolder)`.

### 6. Si `change_type ∈ {new-page, new-scenario}`: preservar package coherence
Cualquier `*.java` nuevo (Task, Question, Interaction, UserInterface, step definition) debe:
- Declarar `package {base_package}.{layer};` exactamente coincidente con el path físico.
- Vivir bajo `src/main/java/{base_package_as_path}/{layer}/` (o `src/test/java/...` para step definitions).
- Importar tipos Appium/Serenity con los mismos alias que usan los archivos existentes.
- Reusar Tasks/Questions/Interactions existentes cuando cubran el flujo; no duplicar lógica.

### 7. Validar Gherkin
Para cada `.feature` nuevo o tocado: parse Gherkin debe pasar (no comentarios `# ...` después de step keyword, no celdas `Examples` vacías, no `Scenario Outline` sin `Examples`). Reglas completas en `[[calidad-appium-screenplay-android]] (consultar `references/gherkin-syntax-rules.md` en su subfolder)`.

### 8. Comando run con tag filter detectado
Construir el comando de ejecución usando `build_system` y `runner_filter_tags` detectados, agregando el tag de la nueva historia:
- Gradle: `./gradlew clean test aggregate -p {project_root} -Dcucumber.filter.tags="@user-story:<ID>"`.
- Maven: `mvn clean verify -f {project_root}/pom.xml -Dcucumber.filter.tags="@user-story:<ID>"`.
Variantes y overrides en `[[calidad-appium-run-and-tags]]`.

Entrega los archivos con `[[calidad-streaming-files-protocol]]` y registra trazabilidad por `[[calidad-test-evidence-and-traceability]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Brownfield: la auto-corrección aplica **EXCLUSIVAMENTE** a los `.feature`, `UserInterface`, `Task`/`Question`/`Interaction`, step definitions y locators recién generados/modificados por este workflow; NUNCA a los archivos preexistentes del cliente, aunque fallen (ver `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

**Cadencia de corrección (aplica a los tests nuevos de esta corrida)**: gate de un escenario → suite de los tests nuevos como inventario → **corrección aislada, re-ejecutando SOLO el test que se corrige** → regresión de los nuevos. Nunca relanzar la suite en cada iteración. Detalle en `[[calidad-test-self-correction-loop]]`. La suite preexistente del cliente no entra en este ciclo.


1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `scaffold-only` por defecto, porque típicamente el agente no tiene device/emulador (Android) ni real device farm (iOS) disponibles. Subir a `full` sólo si el usuario confirma device/emulador o cloud provider + Appium server + binario válido. Clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) defaultean a `dry-run`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` filtrado por el tag de la nueva historia: Gradle (`./gradlew clean test aggregate -p {project_root} -Dcucumber.filter.tags="@user-story:<ID>"`) o Maven (`mvn clean verify -f {project_root}/pom.xml -Dcucumber.filter.tags="@user-story:<ID>"`). Capturar `target/site/serenity/`.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar como deterministic / flaky. Causas típicas iOS/Android: locator stale, capability mal alineada con `platform_detected`, drift del DOM entre versiones del binario, step definition mal reutilizada. Fallos de tests preexistentes del cliente por daño colateral del cambio: detenerse y reportar, NO auto-corregir el legado.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` (multi-locator fallback respetando la API idiomática de `platform_detected`: Android `id`/`xpath`/`accessibilityId`; iOS `iOSClassChain`/`iOSNsPredicateString`/`accessibilityId`). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca cambiar el `package` de un `*.java`, nunca debilitar `Question`s de aserción de negocio, nunca eliminar tags `scenario_tag_conventions` para esquivar filtros del cliente.
5. Reportar estado final: `success` | `partial` (entregado scaffold, no se ejecutó por falta de device) | `failed` (escalado a humano con scenario, stage, logcat/idb log, screenshot Serenity, hipótesis).
6. Archivar evidencia + audit log según `[[calidad-test-evidence-and-traceability]]`. Si la corrección involucró locators, recordar al usuario el patrón documentado en `[[calidad-complete-deferred-locators]]` para los casos donde se requiere Appium Inspector con el binario real.
7. **Invocar `[[calidad-post-generation-protocol]]`** para coherence checks post-emisión (find `scripts/preflight.sh` ejecutable, `test -x gradlew` wrapper ejecutable, `./gradlew compileJava` si modo=full) antes de cerrar.
8. **Smoke gate universal (scenarios nuevos)**: antes de declarar `success`, ejecutar el smoke gate del stack según [[calidad-smoke-gate-policy]]. En brownfield Appium, el gate ejecuta **únicamente los scenarios nuevos** filtrados por tag combinado: filtrando por el **tag de la historia de esta corrida** (ej. `-Dcucumber.filter.tags="@user-story:HUT-123"`) o por el path del feature recién generado. **UN solo escenario**: el más end-to-end de los nuevos; verificar el conteo antes de correr (si el filtro matchea más de uno, acotarlo). NO inventar tags que el proyecto no usa (`@new` no existe en el proyecto del cliente): las convenciones de tags detectadas mandan. Los scenarios preexistentes NO se ejecutan en el gate para no inflar tiempo ni contaminar resultados. Si fallan tests preexistentes al correr la suite completa después, eso NO bloquea la entrega — se reporta como issue separado. Si no hay device/emulador disponible, el gate degrada a `partial` con razón documentada.
9. **Evidencia de bloqueo de ambiente**: si la ejecución sufre bloqueo de ambiente (no device, Appium server no disponible, APK inválido, capabilities no negociables, network al backend), emitir `.evidence/execution-status.json` según [[calidad-environment-blocker-evidence]]. El estado pasa a `partial` con razón.
10. **Metadata por corrida**: emitir `results/appium/{date}/{ISO}-metadata.json` según el schema universal [[calidad-execution-metadata-schema]]. En brownfield, el campo `workload_or_scope` debe distinguir "N scenarios/pages nuevos sobre M preexistentes" e incluir `platform_detected` y device/emulator usado.
11. **Reporte ejecutivo**: invocar `[[calidad-generate-executive-report]]` para producir reporte consolidado en `.evidence/report-{ISO}.{html|pptx|docx|md}`, usando `appium-report-template.md`. El reporte debe segregar explícitamente "scenarios/pages/UserInterfaces nuevos (en scope de esta sesión)" de "scenarios preexistentes (referencia, no ejecutados en el gate)".
12. **Emitir el bloque `delivery_gate` yaml** según `[[calidad-delivery-gate-contract]]` — **precondición: leer `.evidence/pipeline-state.json` y verificar cero fases obligatorias pendientes; con pendientes NO se emite el gate, se emite reporte de estado y el trabajo continúa** — con: status declarado coherente con execution, manifest de archivos nuevos/modificados, evidencia (`.evidence/session-config.json`, `.evidence/generation-manifest.json`, `target/site/serenity/` si modo=full, `.evidence/execution-status.json` si hubo bloqueo de ambiente, metadata por corrida, reporte ejecutivo, audit log si hubo correcciones), blockers (fallos en tests preexistentes del cliente reportados como blocker con status `partial`, jamás auto-corregidos; ausencia de device/emulador reportada como blocker con status `partial`).

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
- [ ] Tests nuevos/modificados ejecutados al menos una vez (cuando hay device/Appium server). Estado: `success` / `partial` / `failed` reportado. `partial` aceptable si no hay device disponible.
- [ ] Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada. Fallos de tests preexistentes del cliente reportados al humano, NO auto-corregidos.
- [ ] Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Auto-corrección sólo tocó archivos generados/modificados por este workflow, respetó `platform_detected` y `scenario_tag_conventions`.
- [ ] Si el modo es `dry-run` o `scaffold-only`: scaffold + comando de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
- [ ] Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory`, `@accessibility` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra).
