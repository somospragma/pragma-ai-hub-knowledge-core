
# Estrategia de actualización de selectores — Appium brownfield

## Regla central

Cuando la UI de la app cambia (nuevo label, nuevo id de Android, nuevo `accessibility id` de iOS, reorganización de la jerarquía), se actualiza ÚNICAMENTE la asignación `Target.the(...).located(...)` dentro del `UserInterface`. Todo lo demás permanece literal:

- Imports (`io.appium.java_client.AppiumBy`, `net.serenitybdd.screenplay.targets.Target`).
- Package declaration.
- Modificadores (`public static final`).
- Nombre del `Target` (constante).
- Descripción dentro de `Target.the("...")` (a menos que el control haya cambiado de significado).
- Métodos auxiliares de la Page, comentarios, orden de propiedades.
- **NO se tocan Tasks, Questions ni Interactions** que consumen esa Page. Si el contrato de la constante (nombre y tipo) se mantiene, los consumidores no requieren cambios.

## Casos típicos

| Caso                            | Cambio permitido                                                                                  |
|---------------------------------|---------------------------------------------------------------------------------------------------|
| Cambio de label de un control   | Actualizar el texto dentro del selector. Si era `accessibilityId`, mover a `id` si el id es estable. |
| Cambio de id de Android         | Actualizar el string dentro de `AppiumBy.id("...")`.                                              |
| Cambio de `accessibility id` iOS| Actualizar el string dentro de `AppiumBy.accessibilityId("...")`.                                 |
| Cambio de jerarquía             | Reescribir el XPath o el `iOSClassChain` para reflejar la nueva jerarquía. Mantener tipo `Target`.|

## Validación previa al cambio

Antes de aplicar el reemplazo:

- Confirmar que el nuevo selector existe en la nueva versión de la app (idealmente via Appium Inspector o `uiautomatorviewer`/`xcrun simctl ui`).
- Preferir selectores estables: `accessibilityId` > `id` (Android) > `iOSClassChain` predecible > XPath.
- En iOS, **evitar XPath**; preferir `iOSClassChain` y `iOSNsPredicateString` por performance.
- Si el control desaparece o cambia de tipo (button → link, input → dropdown), eso ya **no es** un selector update: se escala como `refactor` o `new-page`.

## Snippet — antes / después (Android)

```java
// src/main/java/co/com/pragma/userinterfaces/LoginPage.java — antes
package co.com.pragma.userinterfaces;

import io.appium.java_client.AppiumBy;
import net.serenitybdd.screenplay.targets.Target;

public class LoginPage {

  public static final Target EMAIL_INPUT =
      Target.the("email input")
            .located(AppiumBy.id("com.example.app:id/etEmail"));

  public static final Target PASSWORD_INPUT =
      Target.the("password input")
            .located(AppiumBy.id("com.example.app:id/etPassword"));

  public static final Target LOGIN_BUTTON =
      Target.the("login button")
            .located(AppiumBy.accessibilityId("login_btn"));

  // Helper preservado tal cual
  public static Target errorMessage(String key) {
    return Target.the("error " + key)
                 .locatedBy(AppiumBy.xpath("//android.widget.TextView[@text='" + key + "']").toString());
  }
}
```

```java
// src/main/java/co/com/pragma/userinterfaces/LoginPage.java — después
// (la app renombró los resource-id y movió el botón a accessibility id "btnSignIn")
package co.com.pragma.userinterfaces;

import io.appium.java_client.AppiumBy;
import net.serenitybdd.screenplay.targets.Target;

public class LoginPage {

  public static final Target EMAIL_INPUT =
      Target.the("email input")
            .located(AppiumBy.id("com.example.app:id/inputEmail"));

  public static final Target PASSWORD_INPUT =
      Target.the("password input")
            .located(AppiumBy.id("com.example.app:id/inputPassword"));

  public static final Target LOGIN_BUTTON =
      Target.the("login button")
            .located(AppiumBy.accessibilityId("btnSignIn"));

  // Helper preservado tal cual
  public static Target errorMessage(String key) {
    return Target.the("error " + key)
                 .locatedBy(AppiumBy.xpath("//android.widget.TextView[@text='" + key + "']").toString());
  }
}
```

Único cambio: las cadenas dentro de `AppiumBy.id(...)` y `AppiumBy.accessibilityId(...)`. Package, imports, nombres de constantes, descripciones, helper y orden permanecen idénticos. Las Tasks que invocan `LoginPage.EMAIL_INPUT` no requieren cambios.

## Snippet — iOS

```java
// Antes
public static final Target LOGIN_BUTTON =
    Target.the("login button")
          .located(AppiumBy.accessibilityId("loginButton"));

// Después (la app cambió el accessibility id)
public static final Target LOGIN_BUTTON =
    Target.the("login button")
          .located(AppiumBy.accessibilityId("btnLogin"));
```

Para cambios de jerarquía en iOS, preferir `iOSClassChain`:

```java
public static final Target FIRST_TRANSACTION_ROW =
    Target.the("first transaction row")
          .located(AppiumBy.iOSClassChain("**/XCUIElementTypeTable/XCUIElementTypeCell[1]"));
```

## Anti-patrones

- Cambiar el nombre de la constante (`EMAIL_INPUT` → `EMAIL_FIELD`) durante un selector update: rompe todos los consumidores sin razón.
- Cambiar la estrategia de selector si la nueva versión sigue exponiendo la original (no migrar de `id` a `xpath` "porque es más corto").
- Tocar Tasks o Questions en el mismo commit que el selector update: si hay que tocarlos, escalar a `refactor`.
