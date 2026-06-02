
# Capas Screenplay (Appium Android)

## Capas y responsabilidades

| Capa | Carpeta | Responsabilidad | Suffix | Annotation |
|---|---|---|---|---|
| Task | `tasks/` | Lo que el actor quiere lograr (alto nivel) | `Task` | `@Step` en factories |
| Question | `questions/` | Lo que el actor observa (sin side effects) | noun phrase | — |
| Interaction | `interactions/` | Gesto UI low-level (tap, type, swipe) | verb phrase | `@Step` en factories |
| UserInterface | `userinterfaces/` | Locators agrupados como `Target` constantes | `Page` | — |

**Naming:** clases en PascalCase con el suffix correcto (`LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage`). Constantes `Target` en `UPPER_SNAKE_CASE`. Package base: `co.com.pragma.{tasks|questions|interactions|userinterfaces}`.

`@Step` es **obligatorio** en todo método factory público de Task/Interaction para que aparezca en el reporte Serenity.

## Snippets canónicos

### Task

```java
package co.com.pragma.tasks;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Performable;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.Tasks;
import net.thucydides.core.annotations.Step;

public class LoginTask implements Task {
    @Step("Abrir la app movil")
    public static Performable openAppDeferred() {
        return Tasks.instrumented(LoginTask.class, "open_app");
    }

    @Override
    public <T extends Actor> void performAs(T actor) {
        actor.remember("appResponsive", true);
    }
}
```

### Question

```java
package co.com.pragma.questions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;

public class AppIsResponsive implements Question<Boolean> {
    public static Boolean value(Actor actor) {
        Boolean flag = actor.recall("appResponsive");
        return flag != null && flag;
    }

    @Override
    public Boolean answeredBy(Actor actor) {
        return value(actor);
    }
}
```

### Interaction

```java
package co.com.pragma.interactions;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.targets.Target;
import net.thucydides.core.annotations.Step;

public class TapOn implements Interaction {
    private final Target target;

    public TapOn(Target target) { this.target = target; }

    @Step("Tap sobre {0}")
    public static TapOn theElement(Target target) { return new TapOn(target); }

    @Override
    public <T extends Actor> void performAs(T actor) {
        target.resolveFor(actor).click();
    }
}
```

### UserInterface (locators)

```java
package co.com.pragma.userinterfaces;

import io.appium.java_client.AppiumBy;
import net.serenitybdd.screenplay.targets.Target;

public class LoginPage {
    public static final Target USERNAME = Target.the("Username field").located(AppiumBy.id("login_username"));
    public static final Target PASSWORD = Target.the("Password field").located(AppiumBy.id("login_password"));
    public static final Target LOGIN_BUTTON = Target.the("Login button").located(AppiumBy.id("login_submit"));
}
```

## Anti-patterns

- `OnStage.setTheStage(OnlineCast.whereEveryoneCan(...))` — ambigüedad de sobrecargas en Serenity 4.1.14. Usar `new OnlineCast()`.
- Task sin `@Step` en factory: invisible en el reporte.
- Question con side effects (escribe en UI): rompe el contrato Screenplay.
- Locators sueltos fuera de `userinterfaces/`: duplica selectores y dificulta `[[complete-deferred-locators]]`.
