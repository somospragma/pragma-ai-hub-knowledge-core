<!-- keywords: jacoco, code coverage, coverage report, unified report, coverage threshold, sonarqube -->
# Reference: JaCoCo Code Coverage — Java Multi-Module

## Purpose

Provide the standard JaCoCo configuration for multi-module Java Gradle projects. Includes per-subproject reports, unified root report, coverage threshold enforcement, and SonarQube-compatible XML output.

## Scope of Application

All Java microservices using Gradle multi-module. MANDATORY.

## Step by Step / Guidelines

### 1. Root `build.gradle` — JaCoCo plugin + unified report

```groovy
buildscript {
    ext {
        jacocoVersion = '0.8.14'
    }
}

plugins {
    id 'jacoco'
}

jacoco {
    toolVersion = "${jacocoVersion}"
}

// Unified report aggregating all subprojects
tasks.register('jacocoRootReport', JacocoReport) {
    description = 'Generates unified JaCoCo coverage report for all subprojects'
    group = 'verification'
    dependsOn subprojects.test, subprojects.jacocoTestReport

    executionData.setFrom(subprojects.collect { project ->
        project.fileTree(dir: project.layout.buildDirectory, includes: ['**/jacoco/test.exec'])
    }.flatten())

    sourceDirectories.setFrom(subprojects.collect {
        it.sourceSets.main.allSource.srcDirs
    }.flatten())

    classDirectories.setFrom(subprojects.collect { project ->
        project.sourceSets.main.output
    })

    // Exclude non-business code from coverage
    classDirectories.setFrom(files(classDirectories.files.collect {
        fileTree(dir: it, exclude: [
            '**/MainApplication.class',
            '**/*$Builder.class',
            '**/config/**',
            '**/dto/**',
            '**/model/**',
            '**/entities/**',
            '**/generated/**',
            '**/mock-libs/**',
            '**/com/{client}/lib/**',
            '**/com/{client}/libs/**'
        ])
    }))

    reports {
        xml.required = true
        html.required = true
    }
}

// Coverage threshold enforcement
tasks.register('jacocoCoverageVerification', JacocoCoverageVerification) {
    description = 'Verifies minimum coverage threshold across all subprojects'
    group = 'verification'
    dependsOn jacocoRootReport

    executionData.setFrom(tasks.jacocoRootReport.executionData)
    sourceDirectories.setFrom(tasks.jacocoRootReport.sourceDirectories)
    classDirectories.setFrom(tasks.jacocoRootReport.classDirectories)

    violationRules {
        rule {
            limit {
                minimum = 0.85  // 85% minimum line coverage
            }
        }
    }
}

// Wire coverage check into the build
subprojects {
    afterEvaluate {
        if (tasks.findByName('check')) {
            tasks.check.dependsOn rootProject.tasks.jacocoRootReport
        }
    }
}
```

### 2. `main.gradle` — Per-subproject JaCoCo config

```groovy
subprojects {
    apply plugin: 'jacoco'

    jacoco {
        toolVersion = "${jacocoVersion}"
    }

    test.finalizedBy(project.tasks.jacocoTestReport)

    jacocoTestReport {
        dependsOn test
        reports {
            xml.required = true
            xml.outputLocation = layout.buildDirectory.file("reports/jacoco.xml")
            csv.required = false
            html.outputLocation = layout.buildDirectory.dir("reports/jacocoHtml")
        }
    }
}
```

### 3. `lombok.config` — Exclude Lombok-generated code

JaCoCo 0.8.2+ automatically excludes classes annotated with `@Generated`. Lombok adds this annotation when configured:

```properties
config.stopBubbling = true
lombok.addLombokGeneratedAnnotation = true
```

This ensures Lombok-generated getters, setters, builders, constructors, etc. are NOT counted in coverage metrics.

### 4. Exclusions explained

| Exclusion | Why |
|-----------|-----|
| `**/MainApplication.class` | Bootstrap class — no business logic |
| `**/*$Builder.class` | Lombok/MapStruct generated builders |
| `**/config/**` | Spring configuration classes — wiring only |
| `**/dto/**` | DTOs (Java Records) — no logic |
| `**/model/**` | Domain entities — POJOs with Lombok |
| `**/entities/**` | Framework entities (JPA/R2DBC) — internal to adapters |
| `**/generated/**` | MapStruct generated mapper implementations |
| `**/mock-libs/**` | Client library mocks — not production code |
| `**/com/{client}/lib/**` | {client} corporate library mocks |
| `**/com/{client}/libs/**` | {client} corporate library mocks |

### 5. Running coverage

```bash
# Per-subproject report
./gradlew test jacocoTestReport

# Unified root report (all subprojects)
./gradlew jacocoRootReport

# Verify 85% threshold
./gradlew jacocoCoverageVerification
```

Report locations:
- Per-subproject HTML: `{module}/build/reports/jacocoHtml/index.html`
- Per-subproject XML: `{module}/build/reports/jacoco.xml`
- Unified HTML: `build/reports/jacoco/jacocoRootReport/html/index.html`
- Unified XML: `build/reports/jacoco/jacocoRootReport/jacocoRootReport.xml`

### 6. SonarQube integration

SonarQube reads the XML report. Configure in `sonar-project.properties` or Gradle:

```groovy
sonar {
    properties {
        property "sonar.coverage.jacoco.xmlReportPaths",
            "${project.layout.buildDirectory.get()}/reports/jacoco/jacocoRootReport/jacocoRootReport.xml"
    }
}
```

## Verification Checklist

- [ ] `jacoco` plugin applied in root `build.gradle`
- [ ] `toolVersion` uses the `jacocoVersion` variable (not hardcoded)
- [ ] `jacocoRootReport` task exists and aggregates all subprojects
- [ ] `jacocoCoverageVerification` task exists with 85% minimum threshold
- [ ] Per-subproject `jacocoTestReport` generates XML + HTML
- [ ] `lombok.config` has `lombok.addLombokGeneratedAnnotation = true`
- [ ] Exclusions cover: MainApplication, builders, config, DTOs, models, entities, generated, mock-libs
- [ ] Uses `layout.buildDirectory` (not deprecated `buildDir`)
- [ ] `./gradlew jacocoRootReport` generates unified report
- [ ] `./gradlew jacocoCoverageVerification` passes with ≥85% coverage

## Tools and Resources

- JaCoCo `0.8.14`
- Gradle 8.14.3+
- SonarQube (reads XML report)
