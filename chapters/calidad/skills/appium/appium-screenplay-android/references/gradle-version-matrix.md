
# Matriz de versiones (Appium Screenplay Android)

## Versiones inmutables

| Componente | Versión |
|---|---|
| Serenity | 4.1.14 |
| Appium Java Client | 8.6.0 |
| Cucumber JUnit Platform | 7.14.0 |
| JUnit Platform Suite | 1.10.2 |
| JUnit Jupiter | 5.10.2 |
| Java sourceCompatibility | 21 |
| Gradle wrapper | 8.10 |

Estas versiones se han validado juntas. Cambiar una sola rompe la cadena (en particular Serenity 4.1.14 ↔ JUnit Platform 1.10.2 ↔ Cucumber 7.14.0).

## Reglas de scope de dependencias

| Scope | Librerías | Por qué |
|---|---|---|
| `implementation` | Serenity Core, Serenity Cucumber, Serenity Screenplay, Serenity Screenplay-WebDriver, Appium Java Client, SLF4J, Logback | La capa Screenplay (`src/main/java/co/com/pragma/...`) las necesita en `compileJava`. Moverlas a `testImplementation` rompe la compilación. |
| `testImplementation` | Cucumber JUnit Platform engine, JUnit Platform Suite, JUnit Jupiter, JUnit Vintage, AssertJ | Solo se usan en `src/test`. |
| `compileOnly` + `annotationProcessor` | Lombok | Procesado en compile-time, sin runtime overhead. |

**JUnit Vintage NO es prescindible aunque suene a legacy**: Serenity/Cucumber lo necesitan para ejecutar los ejemplos de `Scenario Outline`. Sin él, cada ejemplo muere con `NoClassDefFoundError: org/junit/runners/ParentRunner` y los escenarios data-driven desaparecen del conteo **en silencio** (verificado en campo: 9 de 20 escenarios perdidos, justo los BVA). Al revisar dependencias, jamás eliminarlo "por limpieza".

**Precedencia**: esta matriz es la fuente de verdad sobre `templates.md`. Si difieren, gana la matriz y el template se corrige.

## Snippet `build.gradle` (parcial)

```groovy
plugins {
    id 'java'
    id 'net.serenity-bdd.serenity-gradle-plugin' version '4.1.14'
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

repositories { mavenCentral() }

dependencies {
    implementation 'net.serenity-bdd:serenity-core:4.1.14'
    implementation 'net.serenity-bdd:serenity-cucumber:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay-webdriver:4.1.14'
    implementation 'io.appium:java-client:8.6.0'
    implementation 'org.slf4j:slf4j-api:2.0.13'
    implementation 'ch.qos.logback:logback-classic:1.5.6'

    testImplementation 'io.cucumber:cucumber-junit-platform-engine:7.14.0'
    testImplementation 'org.junit.platform:junit-platform-suite:1.10.2'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testImplementation 'org.junit.vintage:junit-vintage-engine:5.10.2'
    testImplementation 'org.assertj:assertj-core:3.25.3'

    compileOnly 'org.projectlombok:lombok:1.18.34'
    annotationProcessor 'org.projectlombok:lombok:1.18.34'
}

test {
    useJUnitPlatform()
    systemProperties System.getProperties()
}
```

`settings.gradle`:

```groovy
rootProject.name = '{project_name}'
```

`gradle/wrapper/gradle-wrapper.properties`:

```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.10-bin.zip
```

Ver también ``no-aggregate-collision.md`` para las tareas que NO se deben redefinir.
