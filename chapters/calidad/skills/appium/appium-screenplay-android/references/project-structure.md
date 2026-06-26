
# Estructura del proyecto (Appium Screenplay Android)

## Árbol

```
{project_name}/
├── build.gradle                    # Versiones inmutables (ver `gradle-version-matrix.md`)
├── settings.gradle                 # rootProject.name = '{project_name}'
├── gradlew                         # wrapper Unix (mode 0755)
├── gradlew.bat                     # wrapper Windows
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties  # distributionUrl ...gradle-8.10-bin.zip
├── serenity.properties             # webdriver.driver=appium
├── android.conf                    # capabilities por defecto
├── README.md                       # Spanish: install, run, chmod +x gradlew
└── src/
    ├── main/java/co/com/pragma/
    │   ├── tasks/
    │   │   ├── LoginTask.java      # implements Task, @Step
    │   │   └── example/.gitkeep
    │   ├── questions/
    │   │   └── AppIsResponsive.java  # static value(Actor)
    │   ├── interactions/
    │   │   ├── TapOn.java          # implements Interaction, @Step
    │   │   └── .gitkeep
    │   ├── userinterfaces/
    │   │   ├── LoginPage.java      # Target constants + // TODO markers
    │   │   └── example/.gitkeep
    │   ├── models/.gitkeep
    │   └── utils/.gitkeep
    └── test/
        ├── java/co/com/pragma/
        │   ├── runners/
        │   │   └── LoginRunner.java     # @Suite, FILTER_TAGS_PROPERTY_NAME=@smoke
        │   └── stepdefinitions/
        │       └── LoginStepDefinitions.java
        └── resources/
            ├── serenity.conf       # HOCON: webdriver.driver, appium {}
            ├── logback-test.xml
            ├── junit-platform.properties
            └── features/
                └── login.feature
```

## Contenido canónico por archivo

- **`build.gradle`**: plugins, scopes, dependencies con versiones fijas. NO redefinir `aggregate`/`reports`/`clean` (``no-aggregate-collision.md``).
- **`settings.gradle`**: una sola línea `rootProject.name = '{project_name}'`.
- **`gradlew` / `gradlew.bat`**: wrappers oficiales Gradle 8.10. Unix con shebang `#!/usr/bin/env sh` y mode 0755.
- **`gradle/wrapper/gradle-wrapper.properties`**: `distributionUrl=https\://services.gradle.org/distributions/gradle-8.10-bin.zip`.
- **`serenity.properties`**: `webdriver.driver=appium` y referencia a `serenity.conf`.
- **`android.conf`**: capabilities por defecto (HOCON) usando los valores normalizados de ``mandatory-inputs-validation.md``.
- **`README.md`**: instrucciones en español: instalar JDK 21, `chmod +x gradlew`, comandos de `[[calidad-appium-run-and-tags]]`, TODO de `app_package`/`app_activity` si se usaron defaults.
- **`tasks/LoginTask.java`**: implementa `Task`, factory anotada `@Step`, `performAs` registra `appResponsive=true` (deferred).
- **`questions/AppIsResponsive.java`**: `static value(Actor)` retorna `Boolean`.
- **`interactions/TapOn.java`**: implementa `Interaction`, factory `theElement(Target)` con `@Step`.
- **`userinterfaces/LoginPage.java`**: 3 constantes `Target` (`USERNAME`, `PASSWORD`, `LOGIN_BUTTON`) con `// TODO: update real locator`.
- **`runners/LoginRunner.java`**: `@Suite` + `@IncludeEngines("cucumber")` + `@ConfigurationParameter(key = FILTER_TAGS_PROPERTY_NAME, value = "@smoke")`.
- **`stepdefinitions/LoginStepDefinitions.java`**: glue para los steps de `login.feature` usando `OnStage`, `new OnlineCast()` (NO `OnlineCast.whereEveryoneCan(...)`).
- **`resources/serenity.conf`**: HOCON con `webdriver.driver` y bloque `appium { ... }` con las capabilities.
- **`resources/logback-test.xml`**: log al console nivel INFO, package `co.com.pragma` en DEBUG.
- **`resources/junit-platform.properties`**: `cucumber.plugin=pretty,html:target/cucumber-report.html,json:target/cucumber.json` + `cucumber.glue=co.com.pragma.stepdefinitions`.
- **`resources/features/login.feature`**: 2 escenarios `@android @smoke` (siempre) + `@android @proposed` opcionales (ver ``smoke-vs-proposed-scenarios.md``).
- **`.gitkeep`** en directorios vacíos para no perderlos en git.

Detalle de versiones en ``gradle-version-matrix.md``; ejecución en `[[calidad-appium-run-and-tags]]`.
