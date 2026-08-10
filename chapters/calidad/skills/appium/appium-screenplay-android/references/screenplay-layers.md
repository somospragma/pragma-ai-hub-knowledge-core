
# Capas Screenplay (Appium Android)

## Capas y responsabilidades

| Capa | Carpeta | Responsabilidad | Suffix | Annotation |
|---|---|---|---|---|
| Task | `tasks/` | Lo que el actor quiere lograr (alto nivel) | `Task` | `@Step` en factories |
| Question | `questions/` | Lo que el actor observa (sin side effects) | noun phrase | — |
| Interaction | `interactions/` | Gesto UI low-level (tap, type, swipe) | verb phrase | `@Step` en factories |
| UserInterface | `userinterfaces/` | Locators agrupados como `Target` constantes | `Page` | — |

**Naming:** clases en PascalCase con el suffix correcto (`LoginTask`, `AppIsResponsive`, `TapOn`, `LoginPage`). Constantes `Target` en `UPPER_SNAKE_CASE`. Package base: `co.com.pragma.{tasks|questions|interactions|userinterfaces}`.

`@Step` es **obligatorio** en todo método factory público de Task/Interaction para que aparezca en el reporte Serenity. **Import correcto en Serenity 4.x: `net.serenitybdd.annotations.Step`** — el legacy `net.thucydides.core.annotations.Step` NO existe en 4.1.14 y rompe la compilación (verificado inspeccionando el jar: `serenity-model-4.1.14.jar` → `net/serenitybdd/annotations/Step.class`).

**Frontera Interaction vs Task (regla dura)**: las Interactions son para gestos ATÓMICOS contra el driver (tap, type, swipe, hideKeyboard). Cualquier composición de Performables (`Click.on(...)` + `Enter.theValue(...)` encadenados) va en una **Task**. Anidar Performables dentro de una Interaction puede romper el registro del `StepEventBus` (síntoma observado en campo: `No BaseStepListener has been registered` — nota: ese síntoma también lo produce la ausencia del `SerenityReporter` en `cucumber.plugin`, verificar eso primero).

## Snippets canónicos

### Task

```java
package co.com.pragma.tasks;

import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Performable;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.Tasks;
import net.serenitybdd.annotations.Step;

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
import net.serenitybdd.annotations.Step;

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
    // La estrategia de resolucion la dicta locator-resolution-protocol.md:
    // en apps NATIVAS, AppiumBy.id(resource-id del layout) funciona;
    // en apps FLUTTER, AppiumBy.id NO resuelve Semantics(identifier:) —
    // usar androidUIAutomator/resourceId o XPath descendiendo al nodo capaz.
    public static final Target USERNAME = Target.the("Username field")
            .located(AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"login_username\")"));
    public static final Target PASSWORD = Target.the("Password field")
            .located(AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"login_password\")"));
    public static final Target LOGIN_BUTTON = Target.the("Login button")
            .located(AppiumBy.androidUIAutomator("new UiSelector().resourceId(\"login_submit\")"));
}
```

### Acceso al driver de Appium desde una Interaction

`BrowseTheWeb.as(actor).getDriver()` devuelve un `WebDriverFacade`; para las APIs de Appium (hideKeyboard, pressKey, `mobile: *`) hay que desenvolver:

```java
public final class AppiumDriverOf {
    public static AndroidDriver theActor(Actor actor) {
        WebDriver driver = BrowseTheWeb.as(actor).getDriver();
        if (driver instanceof WebDriverFacade facade) {
            driver = facade.getProxiedDriver();
        }
        if (driver instanceof AndroidDriver android) {
            return android;
        }
        // REGLA DURA: lanzar, JAMAS devolver null con fallback silencioso —
        // un fallback silencioso produce interacciones que "corren" sin ejecutarse.
        throw new IllegalStateException("El driver del actor no es AndroidDriver: " + driver.getClass());
    }
}
```

## Anti-patterns

- `OnlineCast` en cualquiera de sus formas — dispara ChromeDriver junto al driver de Appium (Chrome se abre en cada corrida). Usar `Cast.ofStandardActors()` con `webdriver.driver=provided`.
- Task sin `@Step` en factory: invisible en el reporte.
- Question con side effects (escribe en UI): rompe el contrato Screenplay.
- Locators sueltos fuera de `userinterfaces/`: duplica selectores y dificulta `[[calidad-complete-deferred-locators]]`.
- Import legacy `net.thucydides.core.annotations.Step`: no existe en Serenity 4.x.
- Interaction que compone Performables (`attemptsTo` interno con Click+Enter): eso es una Task.
- Helper de driver que devuelve `null` y cae a un fallback silencioso: la interacción "corre" sin ejecutarse y el triage itera a ciegas.
- `getDomAttribute(...)` sobre elementos Appium: el método correcto es `getAttribute(...)`.

El repertorio completo de interacciones robustas (escritura, OTP, scroll, esperas, recuperación) está en `[mobile-interactions-catalog](mobile-interactions-catalog.md)`.
