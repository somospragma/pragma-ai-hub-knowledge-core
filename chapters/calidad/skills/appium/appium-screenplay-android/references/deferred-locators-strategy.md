
# Estrategia de locators diferidos

El scaffold debe BUILD SUCCESSFUL **sin** que el equipo aún tenga selectores reales del APK. Para eso se aplica el patrón "deferred locators":

1. `LoginPage.java` ship con placeholders (`login_username`, `login_password`, `login_submit`) y un comentario `// TODO: update real locator` sobre cada `Target`.
2. `LoginTask.performAs` NO invoca gestos UI reales — solo registra estado en memoria del actor: `actor.remember("appResponsive", true)`.
3. Los escenarios `@android @smoke` validan con `AppIsResponsive.value(actor) == true`, no contra el DOM real.
4. Resultado: `./gradlew clean test aggregate` retorna BUILD SUCCESSFUL en cualquier máquina con JDK 21, sin APK instalado ni emulador corriendo.

## Snippet (LoginPage.java)

```java
package co.com.pragma.userinterfaces;

import io.appium.java_client.AppiumBy;
import net.serenitybdd.screenplay.targets.Target;

public class LoginPage {
    // TODO: update real locator
    public static final Target USERNAME = Target.the("Username field").located(AppiumBy.id("login_username"));
    // TODO: update real locator
    public static final Target PASSWORD = Target.the("Password field").located(AppiumBy.id("login_password"));
    // TODO: update real locator
    public static final Target LOGIN_BUTTON = Target.the("Login button").located(AppiumBy.id("login_submit"));
}
```

## Riesgo

**Falsa confianza** y **audit risk**: `@smoke` verde no prueba que la app realmente responda. Mitigación:

- Marcar `// TODO: update real locator` como **deuda explícita** (no comentario decorativo).
- Ejecutar workflow `[[calidad-complete-deferred-locators]]` antes de promover a CI productivo.
- Extraer selectores reales con Appium Inspector y reemplazar las constantes `Target`.
- Reemplazar `LoginTask.performAs` para invocar `TapOn.theElement(LoginPage.LOGIN_BUTTON)` y similares.
- Reforzar `AppIsResponsive` para validar visibilidad real (no flag en memoria).
- Agregar guardrail CI con grep:

```bash
if grep -R "// TODO: update real locator" src/ ; then
  echo "Locators diferidos pendientes — bloqueando build productivo"
  exit 1
fi
```

Ver también ``smoke-vs-proposed-scenarios.md`` para el split entre escenarios ejecutables y aspiracionales.
