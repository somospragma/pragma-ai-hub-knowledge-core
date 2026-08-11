# Step Isolation — Appium (Screenplay)

Implementación del patrón universal `[[calidad-step-isolation-pattern]]` en Appium con Screenplay. El mecanismo nativo: separar Tasks de Setup vs Tasks de Main, y evaluar Questions de dominio (contractuales) SOLO en el step main.

## Mecanismo

- **Setup**: Tasks como `LaunchApp`, `AcceptPermissions`, `NavigateToHome`. Validan estructura, no contrato.
- **Auth**: `LoginAs(actor)` — una Task de setup que deja al Actor autenticado. Si Login falla, el escenario aborta antes del main; pero la Question de contrato del main NO se ejecuta.
- **Main**: Tasks de dominio + Questions que codifican el contrato funcional (ej. `TransactionsList.isShowingExpectedFormat()`).
- **Cleanup**: Tasks de teardown (`LogoutCurrentSession`). Su falla NO invalida el veredicto del main.

## Snippet

```java
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.actors.OnStage;
import io.cucumber.java.en.*;

import static net.serenitybdd.screenplay.GivenWhenThen.*;
import static org.hamcrest.Matchers.*;

public class TransactionsSteps {

  // ---- SETUP: Tasks estructurales, no contractuales ----
  @Given("the actor has launched the app and is logged in")
  public void setup() {
    Actor actor = OnStage.theActorCalled("Alice");
    actor.attemptsTo(
      LaunchApp.now(),
      AcceptPermissions.ifAsked(),
      LoginAs.user("alice", "secret")  // setup auth — NO valida contrato del SUT
    );
  }

  // ---- MAIN: Tasks + Questions que codifican el contrato ----
  @When("the actor opens the transactions list")
  public void mainAction() {
    OnStage.theActorInTheSpotlight().attemptsTo(
      NavigateTo.transactionsList()
    );
  }

  @Then("the list shows the expected page size and money format")
  public void mainAssertion() {
    OnStage.theActorInTheSpotlight().should(
      seeThat("rows per page", TransactionsList.rowCount(), equalTo(20)),
      seeThat("money format", TransactionsList.firstRowAmountFormat(),
              matchesPattern("^\\$[\\d,]+\\.\\d{2}$")),
      seeThat("pagination indicator", TransactionsList.paginationText(),
              matchesPattern("Página \\d+ de \\d+"))
    );
  }

  // ---- CLEANUP: opcional; warning si falla, no falla el veredicto ----
  @After
  public void cleanup() {
    try {
      OnStage.theActorInTheSpotlight().attemptsTo(LogoutCurrentSession.now());
    } catch (Exception e) {
      // Log warning; no falla el escenario.
    }
  }
}
```

## Reglas Appium/Screenplay-específicas

- **Setup en Tasks separadas**: `LaunchApp`, `AcceptPermissions`, `LoginAs` son Tasks etiquetadas mentalmente como "setup". NO incluyen `actor.should(...)` con Questions de dominio.
- **Questions de dominio sólo en main**: el patrón `actor.should(seeThat(...))` con Questions del contrato (formato, cantidad, navegación post-acción) se evalúa SOLO después de las Tasks main. Una Question evaluada en setup contamina el reporte.
- **Tags Gherkin**: en los `.feature`, usar `@auth-step`, `@main-step`, `@cleanup-step` cuando hay múltiples escenarios; el cuerpo del escenario marcado `@main-step` es el que cuenta para `effective_minimum`.
- **Filtrado**: `./gradlew test -Dcucumber.filter.tags=@main-step` corre sólo el flujo principal.
- **El `metadata.json`** debe separar contadores: total escenarios `@main-step` vs total `@auth-step`. Si auth pasó y main pasó pero cleanup falló, el `exit_code` puede ser 0 con `blockers: ["cleanup_failed_warning"]` opcional.
- **Anti-pattern**: Question contractual evaluada dentro de `LoginAs` — si el SUT cambia el contrato del login (campo nuevo), todas las pruebas fallan en setup, ocultando si el flow real funcionaba.

## Cross-links

`[[calidad-step-isolation-pattern]]`, `[screenplay-layers](./screenplay-layers.md)`, `[gherkin-syntax-rules](./gherkin-syntax-rules.md)`, `[metadata-emitter-appium](./metadata-emitter-appium.md)`, `[[calidad-appium-screenplay-android]]`.
