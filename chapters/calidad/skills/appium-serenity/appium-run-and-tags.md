---
id: calidad-appium-run-and-tags
version: 1.1.0
scope: stack
type: skill
chapter: calidad
stack: [appium-serenity]
description: Comandos Gradle para ejecutar proyectos Appium Screenplay Android con filtros de tags y override de env.
tags: [appium, gradle, run, tags, cucumber, serenity-report]
---

# Ejecución y filtros de tags (Appium Screenplay Android)

## Comandos base

```bash
# Primera corrida (macOS/Linux) — auto-descarga Gradle 8.10
sh ./gradlew clean test aggregate

# Desde otro directorio
./gradlew clean test aggregate -p <project_path>

# Windows
gradlew.bat clean test aggregate
```

## Filtros por tag

`SuiteRunner` NO lleva tags: el filtro llega siempre por CLI.

```bash
# Solo escenarios @smoke (idempotente con el default)
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke

# Solo aspiracionales
./gradlew clean test aggregate -Dcucumber.filter.tags=@proposed

# Ambos
./gradlew clean test aggregate -Dcucumber.filter.tags='@smoke or @proposed'
```

## Un solo runner, tags por CLI

Regla dura del chapter: **un runner por proyecto, sin tags hardcodeados** (`SuiteRunner`). Si el conteo ejecutado no coincide con el filtro pedido, revisar en este orden: (1) tag hardcodeado en el runner, (2) runner duplicado, (3) default de `cucumber.filter.tags` en `build.gradle`. Las tres causas se verificaron en campo y las tres hacen que `-Dcucumber.filter.tags=@smoke-gate` ejecute otra cosa.

```bash
# GATE 1:1 (siempre primero, exactamente 1 escenario)
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke-gate
```

## Selección de runner (proyectos heredados con más de uno)

Cada `@Suite` lleva su propio filtro de tags: invocar `test` a secas corre TODOS los runners (y sus filtros se suman — en campo esto ejecutó 40 escenarios donde se esperaban 2). Reglas:

- **`--tests` es incompatible con `aggregate` en la misma invocación** (Gradle lo rechaza). Para seleccionar un runner con reporte: property propia en `build.gradle` (`test { if (project.hasProperty('runner')) { filter.includeTestsMatching(project.property('runner')) } }`) e invocar `./gradlew clean test aggregate -Prunner='co.com.pragma.runners.SuiteRunner'`.
- Alternativa: mantener UN runner por suite lógica y filtrar solo por `-Dcucumber.filter.tags`.
- Tras cualquier cambio de runners/filtros, verificar el CONTEO de escenarios ejecutados contra los diseñados (checklist de reportería en [[calidad-appium-screenplay-android]], consultar `references/mobile-evidence-and-triage.md`).

## Override de env

```bash
./gradlew clean test aggregate -Denv=staging
```

`serenity.conf` puede leer `-Denv` con HOCON substitutions para alternar `appium.appium_server_url`/`appium.device_name`.

## Tareas Gradle relevantes

| Tarea | Para qué |
|---|---|
| `clean` | Limpia `build/` y `target/`. NO redefinir (`[[calidad-appium-screenplay-android]] (consultar `references/no-aggregate-collision.md` en su subfolder)`). |
| `compileJava` | Compila `src/main` — usa Serenity/Appium del scope `implementation`. |
| `compileTestJava` | Compila `src/test` — runners y step definitions. |
| `testClasses` | Asegura que los tests compilan sin ejecutarlos. |
| `test` | Ejecuta los runners JUnit Platform → Cucumber. |
| `aggregate` | Genera el reporte HTML Serenity (registrada por el plugin). |
| `reports` | Alias para correr reportes adicionales. |

## Salida del reporte

- HTML: `target/site/serenity/index.html`
- JUnit XML: `build/test-results/test/`
- Cucumber JSON/HTML: según `junit-platform.properties`

## Primera corrida — `gradlew` ejecutable

Si en macOS/Linux el wrapper no tiene permiso:

```bash
chmod +x gradlew
./gradlew clean test aggregate
```

Alternativa sin chmod:

```bash
sh ./gradlew clean test aggregate
```

El health-check stage `gradlew:executable-flag-instruction` exige que el README documente este paso (`[[calidad-appium-screenplay-android]] (consultar `references/health-check-pipeline.md` en su subfolder)`).
