<!-- keywords: archunit, architecture validation, hexagonal constraints, structural rules, build-time validation, java -->
# Reference: Architecture Validation with ArchUnit

## Purpose

Provide a standard set of ArchUnit rules to automatically validate that hexagonal architecture constraints are respected in Java projects. These rules run as unit tests and catch structural violations at build time.

## Scope of Application

- All Java microservices using hexagonal architecture (imperative or reactive).
- Runs as part of the test suite — no additional CI/CD configuration needed.
- MANDATORY for all Java projects (see decision `014 - Architectural Validation Testing`).

## Step by Step / Guidelines

### 1. Add ArchUnit dependency

In `gradle/libs.versions.toml`:

```toml
[versions]
archunit = "1.3.0"

[libraries]
archunit-junit5 = { module = "com.tngtech.archunit:archunit-junit5", version.ref = "archunit" }
```

In the module where tests live (typically `application/app-service/build.gradle`):

```groovy
dependencies {
    testImplementation libs.archunit.junit5
}
```

### 2. Basic hexagonal architecture rules

Create a test class in `application/app-service/src/test/java/{package}/architecture/`:

```java
package com.company.myservice.architecture;

import com.tngtech.archunit.core.importer.ImportOption;
import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;
import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.classes;

@AnalyzeClasses(
    packages = "com.company.myservice",
    importOptions = ImportOption.DoNotIncludeTests.class
)
class HexagonalArchitectureTest {

    @ArchTest
    static final ArchRule domain_must_not_depend_on_infrastructure =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..infrastructure..");

    @ArchTest
    static final ArchRule domain_must_not_depend_on_spring =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAnyPackage(
                "org.springframework..",
                "jakarta.persistence..",
                "jakarta.servlet.."
            );

    @ArchTest
    static final ArchRule domain_must_not_depend_on_application =
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
            .resideInAPackage("..application..");

    @ArchTest
    static final ArchRule ports_must_be_interfaces =
        classes()
            .that().resideInAPackage("..domain.ports..")
            .should().beInterfaces();

    @ArchTest
    static final ArchRule usecases_must_not_use_spring_annotations =
        noClasses()
            .that().resideInAPackage("..domain.usecases..")
            .should().beAnnotatedWith("org.springframework.stereotype.Service")
            .orShould().beAnnotatedWith("org.springframework.stereotype.Component");
}
```

### 3. Naming convention rules (MANDATORY)

```java
@ArchTest
static final ArchRule gateways_must_have_I_prefix_and_end_with_gateway =
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
static final ArchRule adapters_must_end_with_adapter =
    classes()
        .that().resideInAnyPackage("..infrastructure.driven-adapters..", "..infrastructure.entry-points..")
        .and().implement(rawType -> rawType.getSimpleName().endsWith("Gateway"))
        .should().haveSimpleNameEndingWith("Adapter");

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

### 4. Client-specific rules

Some clients have additional validation tasks (`validateStructure`, `checkArchitecture`) in their `main.gradle`. ArchUnit complements these by validating at the code level, while Gradle tasks validate at the file/directory level.

## Verification Checklist

- [ ] `archunit-junit5` dependency declared in `libs.versions.toml` and `build.gradle`
- [ ] Architecture test class exists in `app-service` test sources
- [ ] Domain-to-infrastructure dependency rule passes
- [ ] Domain-to-Spring dependency rule passes
- [ ] Domain-to-application dependency rule passes
- [ ] Ports-are-interfaces rule passes
- [ ] Ports naming (`I*Gateway`) rule passes
- [ ] Use cases naming (`*UseCase`) rule passes
- [ ] Use cases no-Spring-annotations rule passes
- [ ] Adapters naming (`*Adapter`) rule passes
- [ ] Entry-points do not depend on driven-adapters rule passes
- [ ] Driven-adapters do not depend on entry-points rule passes
- [ ] Tests run as part of `./gradlew test`

## Tools and Resources

_(No additional information required for this section.)_
