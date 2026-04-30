<!-- keywords: main.gradle, quality tools, jacoco, pitest, sonarqube, owasp, mapstruct, archunit, subproject configuration, mandatory quality, gradle template, code coverage, mutation testing, static analysis, vulnerability scan -->

# Reference: main.gradle — Mandatory Quality Configuration

## Purpose

Provide the complete, literal `main.gradle` template that MUST be generated for every Java microservice. This file is applied to all subprojects and configures the mandatory quality tools. An empty or incomplete `main.gradle` is NOT compliant.

## Scope of Application

- When generating a new Java microservice (any client, any archetype).
- When validating an existing project's quality tool configuration.
- When `main.gradle` is missing tools or has incomplete configuration.

## Complete main.gradle Template

```groovy
// ═══════════════════════════════════════════════════════════════════
// main.gradle — Mandatory quality configuration for all subprojects
// Applied via: apply from: "${rootDir}/main.gradle" in root build.gradle
// ═══════════════════════════════════════════════════════════════════

// ── JaCoCo — Code Coverage ──────────────────────────────────────
apply plugin: 'jacoco'

jacoco {
    toolVersion = "${jacocoPluginVersion}"
}

jacocoTestReport {
    dependsOn test
    reports {
        xml.required = true
        html.required = true
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = 0.85
            }
        }
    }
}

test.finalizedBy jacocoTestReport

// ── PIT — Mutation Testing ──────────────────────────────────────
apply plugin: 'info.solidsoft.pitest'

pitest {
    targetClasses = ["${project.group}.*"]
    threads = 8
    outputFormats = ['XML', 'HTML']
    junit5PluginVersion = '1.2.1'
    mutationThreshold = 20
}

// ── SonarQube — Static Analysis ─────────────────────────────────
sonar {
    properties {
        property "sonar.host.url", System.getenv("SONAR_HOST_URL") ?: ""
        property "sonar.token", System.getenv("SONAR_TOKEN") ?: ""
        property "sonar.organization", System.getenv("SONAR_ORGANIZATION") ?: ""
        property "sonar.projectKey", System.getenv("SONAR_PROJECT_KEY") ?: ""
        property "sonar.coverage.exclusions", [
            "**/config/**",
            "**/configuration/**",
            "**/MainApplication.java",
            "**/*Config.class",
            "**/model/**",
            "**/dto/**",
            "**/mapper/**",
            "**/*MapperImpl.class",
            "**/entity/**",
            "**/*\$Builder.java"
        ].join(",")
    }
}

// ── OWASP Dependency Check — Vulnerability Scanning ─────────────
dependencyCheck {
    formats = ['HTML', 'JSON', 'XML']
    failBuildOnCVSS = 11  // Report only, do not fail build
    scanConfigurations = ['runtimeClasspath']
}

// ── MapStruct — Suppress Timestamps ─────────────────────────────
tasks.withType(JavaCompile).configureEach {
    options.compilerArgs += ['-Amapstruct.suppressGeneratorTimestamp=true']
}
```

## Root build.gradle Plugin Declarations

The root `build.gradle` MUST declare these plugins for `main.gradle` to work:

```groovy
plugins {
    id 'java'
    id 'jacoco'
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'org.springframework.boot' version "${springBootVersion}" apply false
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
}
```

Plugin versions come from `gradle.properties` (NOT from `libs.versions.toml`).

## Root build.gradle — JaCoCo Unified Report

The root `build.gradle` MUST also include a `jacocoRootReport` task that aggregates coverage from ALL subprojects into a single report. Without this, each module has its own report but there is no project-wide coverage view.

```groovy
// After the subprojects {} block:
tasks.register('jacocoRootReport', JacocoReport) {
    description = 'Unified JaCoCo coverage report across all subprojects'
    group = 'verification'
    dependsOn subprojects*.test

    additionalSourceDirs.from(subprojects.sourceSets.main.allSource.srcDirs)
    sourceDirectories.from(subprojects.sourceSets.main.allSource.srcDirs)
    classDirectories.from(subprojects.sourceSets.main.output)
    executionData.from(subprojects.collect {
        file("${it.layout.buildDirectory.get()}/jacoco/test.exec")
    }.findAll { it.exists() })

    reports {
        xml.required = true      // Used by SonarQube
        html.required = true     // Human-readable
    }
}
```

Run with: `./gradlew jacocoRootReport`

Report output:
- HTML: `build/reports/jacoco/jacocoRootReport/html/index.html`
- XML: `build/reports/jacoco/jacocoRootReport/jacocoRootReport.xml`

The XML report path should be configured in SonarQube properties:
```groovy
property "sonar.coverage.jacoco.xmlReportPaths",
    "${rootProject.layout.buildDirectory.get()}/reports/jacoco/jacocoRootReport/jacocoRootReport.xml"
```

## app-service/build.gradle — ArchUnit

ArchUnit is configured as a test dependency in `app-service/build.gradle`, not in `main.gradle`:

```groovy
dependencies {
    testImplementation libs.archunit
}

tasks.register('architectureTest', Test) {
    useJUnitPlatform()
    include '**/ArchitectureTest.class'
}
```

## gradle.properties — Plugin Versions

```properties
springBootVersion=3.4.5
springDependencyManagementVersion=1.1.7
sonarqubePluginVersion=6.0.1.5171
owaspDependencyTrackPluginVersion=12.1.0
pitestVersion=1.15.0
jacocoPluginVersion=0.8.12
```

## Verification Checklist

- [ ] `main.gradle` exists at project root
- [ ] JaCoCo configured with 85% minimum coverage
- [ ] PIT configured with mutation threshold 20
- [ ] SonarQube configured with env-var properties and coverage exclusions
- [ ] OWASP configured with `failBuildOnCVSS=11` and report formats
- [ ] MapStruct timestamp suppression configured
- [ ] Root `build.gradle` declares all 5 quality plugins
- [ ] `gradle.properties` has all plugin versions
- [ ] `app-service/build.gradle` has ArchUnit test dependency + `architectureTest` task

## Tools and Resources

- Architecture reference (hexagonal-layers) has the Mandatory Quality Tools section
- Architecture quickref (hexagonal-structure-quickref) has the quality tools checklist
- OWASP decision (023) documents vulnerability scanning requirements
- SonarQube decision (025) documents static analysis requirements
- Post-generation verification decision (024) documents the verification sequence

## Step by Step / Guidelines

_(No additional information required for this section.)_
