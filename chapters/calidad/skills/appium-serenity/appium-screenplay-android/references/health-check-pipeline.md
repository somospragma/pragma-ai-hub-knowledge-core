
# Health-check + pipeline + acceptance criteria

## 14 stages estáticas (en orden)

| # | Stage | Check | Mensaje de fallo |
|---|---|---|---|
| 1 | `required:build.gradle` | Existe `build.gradle` en el root. | "build.gradle no encontrado." |
| 2 | `required:gradlew` | Existe `gradlew` ejecutable en el root. | "gradlew no encontrado." |
| 3 | `gradle:no-custom-aggregate` | `build.gradle` no contiene `task aggregate` ni `tasks.register('aggregate'`. | "Redefinicion de task 'aggregate' colisiona con serenity-gradle-plugin." |
| 4 | `gradle:no-task-collisions` | Tampoco redefine `reports` ni `clean` con `task ...` / `tasks.register(...)`. | "Colision con task reservada del plugin." |
| 5 | `gradle:no-serenity-appium` | No existe el plugin imaginario `id 'net.serenity-bdd.appium'`. | "Plugin inexistente declarado." |
| 6 | `gradle:single-buildscript` | Un solo bloque `buildscript {}`. | "Bloque buildscript duplicado." |
| 7 | `gradle:scope-implementation-required` | Serenity y Appium en `implementation`, no `testImplementation`. | "Serenity/Appium en testImplementation rompe compileJava." |
| 8 | `gradle:cucumber-test-scope` | Cucumber/JUnit en `testImplementation`. | "Cucumber fuera de testImplementation." |
| 9 | `gradle:wrapper-contains-version` | `gradle-wrapper.properties` contiene `gradle-8.10`. | "Wrapper no apunta a Gradle 8.10." |
| 10 | `gradlew:has-shebang` | `gradlew` empieza con `#!/usr/bin/env sh`. | "gradlew sin shebang." |
| 11 | `gradlew:has-minimum-body` | `gradlew` no es stub vacío. | "gradlew minimo no valido." |
| 12 | `gradlew:executable-flag-instruction` | README o post-step indica `chmod +x gradlew`. | "Falta instruccion chmod +x gradlew." |
| 13 | `feature:gherkin-syntax-valid` | Cada `*.feature` parsea (encoding, tags ASCII, no inline `#`, etc.). | "Feature invalido — ver ``gherkin-syntax-rules.md``." |
| 14 | `java:package-path-coherence` | `package co.com.pragma.X;` coincide con `src/main/java/co/com/pragma/X/`. | "Package declaration no coincide con path." |

## Pipeline de compilación Gradle

| Fase | Tareas | Obligatorio | Timeout |
|---|---|---|---|
| compile | `clean`, `compileJava`, `testClasses` | Sí | 300s por tarea |
| full | `+ test`, `+ aggregate` | Opcional | 300s por tarea |

Comportamiento:

- Parar en la primera tarea que falle.
- Guardar las últimas 25 líneas de stdout/stderr como `note` adjunta al stage.
- Si el host no puede ejecutar Gradle (no hay JDK 21, no hay red para descargar el wrapper), marcar `partial`.

## Generation status

| Estado | Condición |
|---|---|
| `success` | Todos los 14 checks estáticos OK + pipeline compile (y full si está disponible) exit 0. |
| `partial` | Checks estáticos OK pero pipeline no se pudo ejecutar (sin JDK 21, sin red, etc.). |
| `failed` | Cualquier check estático o tarea Gradle falla. |

Solo entregar al usuario si `generation_status = success`. Si `partial`, comunicar limitación y pedir validación manual.

## 5 acceptance criteria (no negociables)

1. `./gradlew clean test aggregate -p .` exit 0 sin cambios manuales.
2. Cero colisiones de tareas con `serenity-gradle-plugin` (`aggregate`, `reports`, `clean`).
3. Cero errores en `compileJava` + `compileTestJava`.
4. Todos los `*.feature` parsean como Gherkin válido.
5. `gradlew` ejecutable de primera (mode 0755 — `chmod +x gradlew`).

Si cualquiera falla → status `failed` → no entregar.
