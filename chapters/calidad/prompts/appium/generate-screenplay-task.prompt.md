---
id: calidad-appium-generate-screenplay-task-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [appium]
description: Prompt para generar una clase Task Screenplay (Serenity) en co.com.pragma.tasks con anotaciones @Step.
tags: [appium, screenplay, task, java, prompt, serenity]
---

# Prompt — Generar Task Screenplay (Appium Android)

## Variables

- `{{task_name}}` — PascalCase, sin el sufijo `Task` (ej. `Login`, `Checkout`).
- `{{steps}}` — lista de descripciones high-level que el actor realiza (ej. `["Abrir la app", "Ingresar credenciales", "Confirmar"]`).
- `{{ui_constants}}` — lista opcional de constantes `Target` ya disponibles en `userinterfaces` (ej. `["LoginPage.USERNAME", "LoginPage.PASSWORD", "LoginPage.LOGIN_BUTTON"]`). Si esta vacia, aplicar el patron deferred.

## Plantilla

```
Eres un generador de codigo del Chapter Calidad de Pragma. Recibes un nombre de Task, una lista de pasos high-level y opcionalmente las constantes Target disponibles. Produce UNA UNICA clase Java en el package `co.com.pragma.tasks` que implemente `net.serenitybdd.screenplay.Task`, con anotaciones `@Step` en factory methods.

task_name: {{task_name}}
steps:
{{steps}}
ui_constants:
{{ui_constants}}

Reglas:

1. Nombre de la clase: `{{task_name}}Task` (PascalCase + sufijo `Task`).
2. Package: `co.com.pragma.tasks`.
3. Implements `net.serenitybdd.screenplay.Task`.
4. Exponer un factory `public static Performable <camelCase_task_name>()` con `@Step("...")` describiendo la intencion.
5. Implementar `performAs(T actor)`:
   - Si `ui_constants` NO esta vacio: orquestar `actor.attemptsTo(...)` con `Interaction`s reales (ej. `TapOn.theElement(LoginPage.LOGIN_BUTTON)`).
   - Si `ui_constants` esta vacio: aplicar el patron deferred — solo `actor.remember("<task_name>Done", true)` y NO invocar gestos UI. Marcar con comentario `// TODO: implementar gestos reales cuando los locators esten listos`.
6. Imports requeridos: `net.serenitybdd.screenplay.Actor`, `net.serenitybdd.screenplay.Performable`, `net.serenitybdd.screenplay.Task`, `net.serenitybdd.screenplay.Tasks`, `net.thucydides.core.annotations.Step`. Si se usan Interactions, agregar imports correspondientes.
7. NO usar `OnStage.setTheStage(OnlineCast.whereEveryoneCan(...))` — ambiguedad en Serenity 4.1.14.
8. Output: solo el archivo Java, sin prosa adicional.

Ejemplo de salida para task_name=Login, steps=["Abrir la app"], ui_constants=[]:

package co.com.pragma.tasks;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Performable;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.Tasks;
import net.thucydides.core.annotations.Step;

public class LoginTask implements Task {
    @Step("Abrir la app movil")
    public static Performable login() {
        return Tasks.instrumented(LoginTask.class, "login");
    }

    @Override
    public <T extends Actor> void performAs(T actor) {
        // TODO: implementar gestos reales cuando los locators esten listos
        actor.remember("loginDone", true);
    }
}
```
