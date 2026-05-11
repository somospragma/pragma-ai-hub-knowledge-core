---
id: backend-skill-java-webflux-tooling
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Tooling — Java WebFlux

## Propósito

Documentar la configuración obligatoria de Lombok (`lombok.config`) y las reglas ArchUnit para validar la arquitectura hexagonal reactiva en tiempo de compilación.

---

## 1. Configuración de Lombok

### Archivo `lombok.config` (Raíz del Proyecto)

Todo proyecto Java WebFlux DEBE incluir este archivo en la raíz:

```properties
config.stopBubbling = true
lombok.addLombokGeneratedAnnotation = true
```

- `config.stopBubbling = true` — evita que Lombok busque configuración en directorios padre.
- `lombok.addLombokGeneratedAnnotation = true` — agrega `@Generated` al código generado por Lombok. Crítico para que JaCoCo y SonarQube excluyan correctamente el código generado de los reportes de cobertura.

### Versión en Version Catalog

```toml
# gradle/libs.versions.toml
[versions]
lombok = "1.18.36"

[libraries]
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
```

### Dependencia Transversal en Root build.gradle

```groovy
subprojects {
    apply plugin: 'java'

    dependencies {
        compileOnly libs.lombok
        annotationProcessor libs.lombok
        testCompileOnly libs.lombok
        testAnnotationProcessor libs.lombok
    }
}
```

### Reglas de Lombok

- **NO** declarar Lombok en `build.gradle` de módulos individuales (se hereda del root).
- Usar `@Data` solo en entidades de infraestructura (R2DBC entities).
- Usar `@Builder` para construcción de objetos complejos.
- Usar `@RequiredArgsConstructor` para inyección de dependencias.
- DTOs deben ser Java Records, **NO** clases con `@Data`.

---

## 2. Validación de Arquitectura con ArchUnit

### Dependencia

```toml
# gradle/libs.versions.toml
[versions]
archunit = "1.3.0"

[libraries]
archunit-junit5 = { module = "com.tngtech.archunit:archunit-junit5", version.ref = "archunit" }
```

En `application/app-service/build.gradle`:

```groovy
dependencies {
    testImplementation libs.archunit.junit5
}

tasks.register('architectureTest', Test) {
    useJUnitPlatform()
    include '**/ArchitectureTest.class'
}
```

### Reglas de Arquitectura Hexagonal (Reactiva)

```java
package com.pragma.myservice.architecture;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;

@AnalyzeClasses(
    packages = "com.pragma.myservice",
    importOptions = ImportOption.DoNotIncludeTests.class
)
class HexagonalArchitectureTest {

    // El dominio NO debe depender de infraestructura
    @ArchTest
    static final ArchRule domain_must_not_depend_on_infrastructure =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..infrastructure..");

    // El dominio NO debe depender de Spring
    @ArchTest
    static final ArchRule domain_must_not_depend_on_spring =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAnyPackage(
                "org.springframework..",
                "jakarta.persistence..",
                "io.r2dbc.."
            );

    // El dominio NO debe depender de la capa de aplicación
    @ArchTest
    static final ArchRule domain_must_not_depend_on_application =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..application..");

    // Los ports DEBEN ser interfaces
    @ArchTest
    static final ArchRule ports_must_be_interfaces =
        classes()
            .that().resideInAPackage("..domain.ports..")
            .should().beInterfaces();

    // Los use cases NO deben tener anotaciones de Spring
    @ArchTest
    static final ArchRule usecases_must_not_use_spring_annotations =
        noClasses()
            .that().resideInAPackage("..domain.usecases..")
            .should().beAnnotatedWith("org.springframework.stereotype.Service")
            .orShould().beAnnotatedWith("org.springframework.stereotype.Component");

    // NO debe haber @RestController en el proyecto
    @ArchTest
    static final ArchRule no_rest_controllers_allowed =
        noClasses()
            .that().resideInAnyPackage("com.pragma.myservice..")
            .should().beAnnotatedWith("org.springframework.web.bind.annotation.RestController");
}
```

### Reglas de Naming (Obligatorias)

```java
@ArchTest
static final ArchRule gateways_must_have_I_prefix =
    classes()
        .that().resideInAPackage("..domain.ports..")
        .should().haveSimpleNameStartingWith("I")
        .andShould().haveSimpleNameEndingWith("Gateway");

@ArchTest
static final ArchRule usecases_must_end_with_usecase =
    classes()
        .that().resideInAPackage("..domain.usecases..")
        .should().haveSimpleNameEndingWith("UseCase");

@ArchTest
static final ArchRule handlers_must_end_with_handler =
    classes()
        .that().resideInAPackage("..infrastructure.entry-points..")
        .and().haveSimpleNameEndingWith("Handler")
        .should().beAnnotatedWith("org.springframework.stereotype.Component");

@ArchTest
static final ArchRule routers_must_end_with_router =
    classes()
        .that().resideInAPackage("..infrastructure.entry-points..")
        .and().haveSimpleNameEndingWith("Router")
        .should().beAnnotatedWith("org.springframework.context.annotation.Configuration");

@ArchTest
static final ArchRule entry_points_must_not_depend_on_driven_adapters =
    noClasses()
        .that().resideInAPackage("..infrastructure.entry-points..")
        .should().dependOnClassesThat()
        .resideInAPackage("..infrastructure.driven-adapters..");

@ArchTest
static final ArchRule driven_adapters_must_not_depend_on_entry_points =
    noClasses()
        .that().resideInAPackage("..infrastructure.driven-adapters..")
        .should().dependOnClassesThat()
        .resideInAPackage("..infrastructure.entry-points..");
```

### Ejecución

```bash
# Ejecutar solo tests de arquitectura
./gradlew :application:app-service:architectureTest

# Ejecutar todos los tests (incluye arquitectura)
./gradlew test
```

---

## Checklist de Verificación

- [ ] `lombok.config` existe en la raíz del proyecto
- [ ] `lombok.config` contiene `config.stopBubbling = true`
- [ ] `lombok.config` contiene `lombok.addLombokGeneratedAnnotation = true`
- [ ] `libs.versions.toml` declara versión de Lombok y ArchUnit
- [ ] Root `build.gradle` declara Lombok en bloque `subprojects`
- [ ] Ningún módulo individual redeclara Lombok
- [ ] Clase de test de arquitectura existe en `app-service`
- [ ] Regla dominio→infraestructura pasa
- [ ] Regla dominio→Spring pasa
- [ ] Regla ports-son-interfaces pasa
- [ ] Regla naming `I*Gateway` pasa
- [ ] Regla naming `*UseCase` pasa
- [ ] Regla no-@RestController pasa
- [ ] Tests corren como parte de `./gradlew test`
