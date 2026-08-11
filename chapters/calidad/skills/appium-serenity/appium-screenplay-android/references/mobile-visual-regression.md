
# Regresión visual mobile en Appium Screenplay

> Política transversal (cuándo, baselines, dinamismo, anti-patrones): `[[calidad-visual-regression]]`. Esta referencia cubre la implementación **Appium/Screenplay (móvil)**.

Esta referencia cubre cómo integrar regresión visual en una suite Appium del Chapter Calidad. Aplica a Android y iOS (los SDK propietarios soportan ambas).

## Herramientas

| Herramienta                                      | Madurez mobile         | Notas                                                                                                |
|--------------------------------------------------|------------------------|------------------------------------------------------------------------------------------------------|
| **Applitools Eyes Appium** (`com.applitools.eyes.appium`) | Alta (propietaria) | AI-based matching, gestión de baselines en cloud, ignora dinamismo de UI bien afinado.              |
| **Percy** (`io.percy.appium`)                    | Media-alta (propietaria) | Snapshot + diff, integración CI nativa, pricing por snapshot.                                       |
| **AShot** (open-source)                          | Baja (deprecated)      | Captura + comparación local. Patrón usable, pero sin mantenimiento desde 2019. NO recomendado en nuevos proyectos. |

**Decisión del Chapter Calidad:** apuntar a herramientas propietarias (Applitools o Percy) por madurez, gestión de baselines, manejo de dinamismo y soporte multi-device. AShot sirve como referencia conceptual del patrón Screenplay; no es la implementación productiva.

## Patrón Screenplay

Modelar la captura como una `Interaction` (acción con efecto: invocar el SDK y subir el snapshot) y la verificación como una `Question` (consulta el resultado del match contra el baseline).

### Interaction — `CaptureScreenshot`

```java
package co.com.pragma.interactions;

import com.applitools.eyes.appium.Eyes;
import com.applitools.eyes.MatchLevel;
import io.appium.java_client.AppiumDriver;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Interaction;
import net.serenitybdd.screenplay.abilities.BrowseTheWeb;

public class CaptureScreenshot implements Interaction {

  private final String tag;
  private final MatchLevel matchLevel;

  private CaptureScreenshot(String tag, MatchLevel matchLevel) {
    this.tag = tag;
    this.matchLevel = matchLevel;
  }

  public static CaptureScreenshot of(String tag) {
    return new CaptureScreenshot(tag, MatchLevel.STRICT);
  }

  public CaptureScreenshot withMatchLevel(MatchLevel level) {
    return new CaptureScreenshot(this.tag, level);
  }

  @Override
  public <T extends Actor> void performAs(T actor) {
    AppiumDriver driver = actor.abilityTo(BrowseTheWeb.class).getDriver();
    Eyes eyes = EyesHolder.forActor(actor);   // ability/holder gestiona ciclo de vida de Eyes
    eyes.setMatchLevel(matchLevel);
    eyes.checkWindow(tag);
  }
}
```

### Question — `VisualMatchesBaseline`

```java
package co.com.pragma.questions;

import com.applitools.eyes.TestResults;
import net.serenitybdd.screenplay.Actor;
import net.serenitybdd.screenplay.Question;

public class VisualMatchesBaseline implements Question<Boolean> {

  public static VisualMatchesBaseline forCurrentRun() {
    return new VisualMatchesBaseline();
  }

  @Override
  public Boolean answeredBy(Actor actor) {
    TestResults results = EyesHolder.closeAndGetResults(actor);
    return results != null
        && results.getMismatches() == 0
        && results.getMissing() == 0;
  }
}
```

### Uso en step definition

```java
@Then("the {string} screen matches its visual baseline")
public void theScreenMatchesBaseline(String tag) {
  theActorInTheSpotlight().attemptsTo(CaptureScreenshot.of(tag));
  assertThat(theActorInTheSpotlight().asksFor(VisualMatchesBaseline.forCurrentRun()))
      .as("Visual baseline match for '%s'", tag)
      .isTrue();
}
```

## Snippet — integración Applitools en Java (setup)

```java
package co.com.pragma.utils;

import com.applitools.eyes.BatchInfo;
import com.applitools.eyes.appium.Eyes;
import io.appium.java_client.AppiumDriver;

public class ApplitoolsBootstrap {

  public static Eyes init(AppiumDriver driver, String testName) {
    Eyes eyes = new Eyes();
    eyes.setApiKey(System.getenv("APPLITOOLS_API_KEY"));
    eyes.setBatch(new BatchInfo(System.getenv().getOrDefault("APPLITOOLS_BATCH_ID", "Appium Mobile")));
    eyes.open(driver, "MobileApp", testName);
    return eyes;
  }
}
```

`build.gradle` snippet (agregar como dependency **previa aprobación** del usuario en brownfield):

```gradle
implementation 'com.applitools:eyes-appium-java5:5.+'
```

## Baselines y dinamismo de dispositivos

Mobile introduce variabilidad que web no tiene. Estrategia:

- **Baselines por device profile.** Un baseline por combinación `(platform, deviceModel, platformVersion, orientation)`. Applitools maneja esto vía `HostApp`, `HostOS`, `DeviceName`.
- **DPI / densidad.** Capturar siempre desde el mismo emulador/device modelo en CI (ej. `Pixel 6 API 33` portrait). NO mezclar capturas de Pixel 6 con Pixel 7 en el mismo baseline.
- **Orientación.** Definir explícita en capabilities (`orientation=PORTRAIT`); cambios de orientación generan baseline separado.
- **Status bar y notch.** Recortar mediante `eyes.setCutProvider(...)` para excluir hora y batería, que cambian a cada corrida.
- **Match Level:**
  - `STRICT`: default; falla ante cualquier diferencia significativa. Usar en pantallas estáticas.
  - `LAYOUT`: ignora contenido pero valida estructura. Usar en pantallas con datos dinámicos (listas, feeds).
  - `CONTENT`: ignora colores/estilo, valida contenido. Raro en mobile.
  - `EXACT`: pixel-perfect. NO usar; demasiado frágil.

## Cuándo correr

- **NO** en cada test del pipeline (costo de snapshots y baselines + tiempo de captura).
- **SÍ** en un job dedicado del pipeline CI, filtrado por tag, en cada PR a `main` y en cada release candidate.
- Etiquetar los escenarios con `@visual` además de los tags del chapter.
- Comando:
  ```bash
  ./gradlew clean test aggregate -Dcucumber.filter.tags="@visual"
  ```
- Variables de entorno requeridas: `APPLITOOLS_API_KEY` (o equivalente Percy), `APPLITOOLS_BATCH_ID` (opcional, agrupa el batch en el dashboard).

## Anti-patrones

- Captar screenshots locales en disco y compararlos con `assertEquals` byte-a-byte: rompe ante cualquier cambio de DPI/AA.
- Mezclar baselines de simulador y device real en el mismo `HostApp`.
- Ignorar la zona de notch/status bar sin recorte explícito: cada corrida produce diff por la hora.
- Subir el `APPLITOOLS_API_KEY` al repo. Solo via secret del CI.
