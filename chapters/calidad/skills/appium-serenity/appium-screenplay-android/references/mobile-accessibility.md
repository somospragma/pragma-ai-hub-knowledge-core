
# Accesibilidad mobile en Appium Screenplay

> Política transversal (cuándo, dimensiones, severidad, evidencia): `[[calidad-accessibility-testing]]`. Esta referencia cubre la implementación **Appium/Screenplay (móvil)**.

Esta referencia cubre cómo integrar checks de accesibilidad en una suite Appium Screenplay del Chapter Calidad. Aplica principalmente a Android (donde el tooling es más maduro); la lógica Screenplay es portable a iOS sustituyendo la integración por XCUITest accessibility audit.

## Herramientas

| Herramienta                                  | Uso                                                                                                   |
|----------------------------------------------|-------------------------------------------------------------------------------------------------------|
| **Accessibility Scanner** (Android)          | App oficial de Google. Escanea la UI activa y reporta hallazgos. Invocable vía ADB en CI.             |
| **Espresso a11y assertions**                 | `AccessibilityChecks.enable()` con integración Appium para correr checks en cada interacción.         |
| **Google's accessibility-test-framework**    | Librería base (`com.google.android.apps.common.testing.accessibility.framework`). Permite checks programáticos. |
| **XCUITest accessibility audit** (iOS)       | `XCUIApplication().performAccessibilityAudit()` desde Xcode 15+. Reportable como JSON.                |

Para suites estables del chapter, preferir Espresso a11y + accessibility-test-framework (integración Java directa) y reservar Accessibility Scanner para auditorías manuales o pipelines secundarios.

## Patrón Screenplay

Modelar las verificaciones como una Question (consulta sin efecto secundario) que invoca ADB o la librería embebida, y una Task que falla el escenario cuando hay hallazgos.

### Question — `AccessibilityIssuesFound`

```java
package co.com.pragma.questions;

import co.com.pragma.utils.AccessibilityScannerAdb;
import co.com.pragma.utils.AccessibilityIssue;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;

import java.util.List;

public class AccessibilityIssuesFound implements Question<List<AccessibilityIssue>> {

  private final String screenLabel;

  private AccessibilityIssuesFound(String screenLabel) {
    this.screenLabel = screenLabel;
  }

  public static AccessibilityIssuesFound onScreen(String screenLabel) {
    return new AccessibilityIssuesFound(screenLabel);
  }

  @Override
  public List<AccessibilityIssue> answeredBy(Actor actor) {
    // Lanza Accessibility Scanner via ADB, espera y parsea el report XML/JSON.
    return AccessibilityScannerAdb.runAndParse(screenLabel);
  }
}
```

### Task — `AssertAccessibilityCompliance`

```java
package co.com.pragma.tasks;

import co.com.pragma.questions.AccessibilityIssuesFound;
import co.com.pragma.utils.AccessibilityIssue;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Task;
import net.serenitybdd.screenplay.actions.Switch;

import java.util.List;
import java.util.stream.Collectors;

import static org.assertj.core.api.Assertions.assertThat;

public class AssertAccessibilityCompliance implements Task {

  private final String screenLabel;

  private AssertAccessibilityCompliance(String screenLabel) {
    this.screenLabel = screenLabel;
  }

  public static AssertAccessibilityCompliance onScreen(String screenLabel) {
    return new AssertAccessibilityCompliance(screenLabel);
  }

  @Override
  public <T extends Actor> void performAs(T actor) {
    List<AccessibilityIssue> issues =
        actor.asksFor(AccessibilityIssuesFound.onScreen(screenLabel));

    List<AccessibilityIssue> blocking = issues.stream()
        .filter(i -> i.severity().isAtLeast("ERROR"))
        .collect(Collectors.toList());

    assertThat(blocking)
        .as("Accessibility issues on screen '%s'", screenLabel)
        .isEmpty();
  }
}
```

### Uso en step definition

```java
@Then("the {string} screen meets accessibility standards")
public void theScreenMeetsA11y(String screen) {
  theActorInTheSpotlight().attemptsTo(
      AssertAccessibilityCompliance.onScreen(screen)
  );
}
```

## Criterios mínimos

Verificar en cada pantalla priorizada (`CRITICAL`, `HIGH`):

- **Contraste de color:** texto vs fondo cumple WCAG 2.1 AA (4.5:1 texto normal, 3:1 texto grande / iconos significativos).
- **Touch target size:** controles interactivos ≥ 48dp × 48dp (Android Material) / 44pt × 44pt (iOS HIG).
- **Content descriptions presentes:** todo `ImageView`/`ImageButton` decorativo marcado `importantForAccessibility=no`; los significativos tienen `contentDescription` no vacío.
- **Labels asociados a inputs:** cada `EditText` tiene `labelFor` apuntando a un `TextView` visible o tiene `hint` descriptivo y no decorativo.
- **Orden de foco coherente:** tab order sigue el flujo visual; no hay trampas de foco.

## Mapping WCAG 2.1 AA para mobile

| WCAG criterion                          | Equivalente mobile                                                                                |
|-----------------------------------------|---------------------------------------------------------------------------------------------------|
| 1.1.1 Non-text Content                  | `contentDescription` (Android) / `accessibilityLabel` (iOS) en imágenes informativas.             |
| 1.3.1 Info and Relationships            | Roles correctos (Button, Header, Link); `labelFor`/`accessibilityElement` agrupando label+input. |
| 1.4.3 Contrast (Minimum)                | Ratio ≥ 4.5:1 texto normal, 3:1 texto grande.                                                     |
| 1.4.11 Non-text Contrast                | Iconos significativos y bordes de input ≥ 3:1 vs fondo.                                           |
| 2.4.7 Focus Visible                     | Indicador de foco visible al navegar con teclado externo o switch control.                        |
| 2.5.5 Target Size                       | ≥ 44pt iOS / 48dp Android.                                                                        |
| 3.3.2 Labels or Instructions            | Cada input expone label o hint significativo.                                                     |
| 4.1.2 Name, Role, Value                 | Cada control expone name (label), role y state correctos al servicio de accesibilidad.            |

## Tags y ejecución

- Etiquetar los escenarios de accesibilidad con `@accessibility @a11y @mobile` además de los tags del chapter.
- Ejecutar en pipeline:
  ```bash
  ./gradlew clean test aggregate -Dcucumber.filter.tags="@accessibility"
  ```
- Reportar findings en el aggregate Serenity (cada `AccessibilityIssue` se anexa como step evidence).
- Recomendado correr en cada PR sobre las pantallas priorizadas, no en cada test.
