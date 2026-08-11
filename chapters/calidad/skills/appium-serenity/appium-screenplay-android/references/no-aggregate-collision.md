
# No redefinir tareas del plugin Serenity

El plugin `net.serenity-bdd.serenity-gradle-plugin` 4.1.14 **auto-registra** las tareas `aggregate`, `reports` y `clean` durante su `apply()`. Redefinirlas en `build.gradle` rompe el build antes de compilar.

## Prohibido

```groovy
// NO HACER
task aggregate {
    // ...
}

// NO HACER
tasks.register('aggregate') {
    // ...
}

// NO HACER (mismo error para reports/clean)
task reports { ... }
```

## Permitido

```groovy
// OK — configurar la tarea ya registrada
tasks.named('aggregate') {
    // configuración adicional
}

tasks.named('reports') {
    dependsOn 'aggregate'
}
```

## Síntoma de violación

```
* What went wrong:
A problem occurred evaluating root project '{project_name}'.
> Cannot add task 'aggregate' as a task with that name already exists.
```

Si aparece este error, eliminar la redefinición y usar `tasks.named(...)`. La misma regla aplica para `reports` y `clean` (que `java` plugin también registra).

Ver health-check stage `gradle:no-custom-aggregate` y `gradle:no-task-collisions` en ``health-check-pipeline.md``.
