
# Matriz de versiones (Appium Screenplay Android)

## Versiones inmutables

| Componente | Versión |
|---|---|
| Serenity (core, cucumber, screenplay, screenplay-webdriver, **ensure**) | 4.1.14 |
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

## La matriz NO se degrada: el JDK se descarga

Si el ambiente no tiene JDK 21, **la respuesta no es bajar la versión del proyecto** (ocurrió en campo: se degradó a Java 16 para "que compile", saliéndose de la matriz validada). Gradle lo resuelve descargando el toolchain:

`settings.gradle`:

```groovy
plugins {
    id 'org.gradle.toolchains.foojay-resolver-convention' version '0.8.0'
}
rootProject.name = '{project_name}'
```

`build.gradle` (en vez de `sourceCompatibility` suelto):

```groovy
java {
    toolchain { languageVersion = JavaLanguageVersion.of(21) }
}
```

Con eso, Gradle localiza o **descarga** un JDK 21 sin tocar el `JAVA_HOME` del usuario. Si el proyecto igualmente debe correr con otro JDK, es una decisión del usuario que se declara como riesgo en el STRATEGY.md — nunca un cambio silencioso del agente.

## Tabla de imports Serenity 4.x (cambios respecto de 3.x)

| Clase | 3.x (roto en 4.x) | 4.x correcto |
|---|---|---|
| `@Step` | `net.thucydides.core.annotations.Step` | `net.serenitybdd.annotations.Step` |
| `EnvironmentVariables` | `net.thucydides.core.util.EnvironmentVariables` | `net.thucydides.model.util.EnvironmentVariables` |
| `Ensure` | — | `net.serenitybdd.screenplay.ensure.Ensure` (requiere la dependencia `serenity-ensure`) |

**Antes de concluir que una API "no existe"**, verificarlo contra el jar (`unzip -l ~/.gradle/caches/**/serenity-*.jar | grep <Clase>`) o contra la doc de la versión: en campo se declaró eliminada una clase que solo requería su dependencia, y se reescribió código por esa conclusión falsa.

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
    // serenity-ensure trae net.serenitybdd.screenplay.ensure.Ensure. NO viene con
    // serenity-core: sin esta línea, `Ensure` da "cannot find symbol" y es fácil
    // concluir en falso que "no existe en 4.x" (ocurrió en campo).
    implementation 'net.serenity-bdd:serenity-ensure:4.1.14'
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
