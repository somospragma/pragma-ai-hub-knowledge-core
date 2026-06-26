---
id: calidad-appium-run-and-tags
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [appium]
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

`LoginRunner` filtra `@smoke` por default. Para override:

```bash
# Solo escenarios @smoke (idempotente con el default)
./gradlew clean test aggregate -Dcucumber.filter.tags=@smoke

# Solo aspiracionales
./gradlew clean test aggregate -Dcucumber.filter.tags=@proposed

# Ambos
./gradlew clean test aggregate -Dcucumber.filter.tags='@smoke or @proposed'
```

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
