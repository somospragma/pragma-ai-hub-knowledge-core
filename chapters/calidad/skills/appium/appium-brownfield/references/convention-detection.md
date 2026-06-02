
# Detección de convenciones — Appium brownfield

## Qué detectar

| Campo                       | Fuente / cómo se infiere                                                                                          | Ejemplo                                                          |
|-----------------------------|-------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `build_system`              | Presencia de `build.gradle` + `gradlew` (Gradle) vs. `pom.xml` (Maven)                                            | `gradle` \| `maven`                                              |
| `base_package`              | `package` declarado en el runner Cucumber y en cualquier `*.java` de Screenplay                                   | `co.com.pragma`, `com.client.tests`, `com.empresa.qa.mobile`     |
| `screenplay_layers_present` | Subdirectorios presentes bajo `src/main/java/{base_package}/`                                                     | `[tasks, questions, interactions, userinterfaces]`               |
| `cucumber_runner_class`     | Clase con `@RunWith(CucumberWithSerenity.class)` o `@Suite + @SelectClasspathResource`                            | `CucumberTestRunner`, `RunCucumberTest`                          |
| `runner_filter_tags`        | Valor de `@CucumberOptions(tags = "...")` o de `cucumber.filter.tags` en `junit-platform.properties`              | `@smoke`, `@android and not @wip`, `@regression`                 |
| `gherkin_language`          | Línea `# language: en` o `# language: es` al inicio de los `.feature`, o default observado en las palabras clave  | `en` \| `es`                                                     |
| `feature_naming_pattern`    | Naming de los `.feature` existentes                                                                               | `login.feature`, `HUT-123-login.feature`, `Login_Mobile.feature` |
| `scenario_tag_conventions`  | Set de tags observados en los `Scenario:` y `Scenario Outline:`                                                   | `@smoke @regression @mobile`, `@happyPath @negative`             |
| `platform_detected`         | `automationName` en `serenity.conf`/`*.conf` o capabilities en código (`UiAutomator2` → android, `XCUITest` → ios) | `android` \| `ios`                                               |
| `existing_pages`            | Listado de `UserInterface` bajo `src/main/java/{base_package}/userinterfaces/` con sus selectores reales o TODO   | `[LoginPage, HomePage]` con selectores `// TODO` aún pendientes  |
| `features_dir`              | Path resuelto donde viven los `.feature`                                                                          | `src/test/resources/features/`                                   |
| `step_definitions_dir`      | Path resuelto donde viven los step definitions                                                                    | `src/test/java/{base_package}/stepdefinitions/`                  |

## Algoritmo

1. **Leer `build.gradle` (o `pom.xml`)**: confirmar `build_system`. Anotar dependencias declaradas para no duplicarlas si el cambio requiere agregar una nueva.
2. **Leer `serenity.conf` / `android.conf` / `ios.conf`**: extraer `automationName`, `platformName`, `deviceName`, `app`/`bundleId`, `appPackage`/`appActivity`. Esto determina `platform_detected`.
3. **Leer el runner Cucumber** (un solo archivo, p. ej. `src/test/java/.../runners/CucumberTestRunner.java`): extraer `base_package`, `cucumber_runner_class`, `runner_filter_tags`, glue paths y feature paths.
4. **Listar un `.feature` representativo** (preferir uno por módulo si hay varios):
   - Leer la primera línea para `gherkin_language`.
   - Listar tags presentes en `Feature:` y `Scenario:` para `scenario_tag_conventions`.
   - Anotar el naming del archivo para `feature_naming_pattern`.
5. **Listar un `UserInterface` representativo** (`src/main/java/.../userinterfaces/*.java`):
   - Detectar si usa `AppiumBy.id`/`xpath`/`accessibilityId` (Android-typical) o `AppiumBy.iOSClassChain`/`iOSNsPredicateString` (iOS).
   - Verificar coherencia con `platform_detected`. Si no hay coherencia, reportar al usuario antes de continuar.
6. **Consolidar el objeto de convenciones** y usarlo como contrato para los archivos nuevos.

## Salida sugerida

```json
{
  "build_system": "gradle",
  "base_package": "co.com.pragma",
  "screenplay_layers_present": ["tasks", "questions", "interactions", "userinterfaces"],
  "cucumber_runner_class": "co.com.pragma.runners.CucumberTestRunner",
  "runner_filter_tags": "@android and not @wip",
  "gherkin_language": "en",
  "feature_naming_pattern": "{snake_case}.feature",
  "scenario_tag_conventions": ["@android", "@smoke", "@regression", "@mobile"],
  "platform_detected": "android",
  "existing_pages": ["LoginPage", "HomePage"],
  "features_dir": "src/test/resources/features/",
  "step_definitions_dir": "src/test/java/co/com/pragma/stepdefinitions/"
}
```

## Regla de prioridad

Si el proyecto declara `gherkin_language: es` y el chapter usualmente usa `en`, el proyecto manda. Lo mismo aplica a `base_package`, tags, naming. El brownfield **respeta** el proyecto; no lo realinea al estándar del chapter.
