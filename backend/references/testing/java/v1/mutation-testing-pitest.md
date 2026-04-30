<!-- keywords: mutation testing, pitest, pit, test effectiveness, mutant, test quality, java, gradle -->
# Reference: Mutation Testing with PIT (pitest)

## Purpose

Provide the standard configuration for mutation testing with PIT in Java Gradle projects. PIT verifies test effectiveness by introducing small code changes (mutants) and checking whether tests detect them.

## Scope of Application

- All Java microservices using Gradle.
- MANDATORY for all projects (see decision `013 - Architectural Mutation Testing`).
- Minimum mutation kill threshold: **20%**.

## Step by Step / Guidelines

### 1. Plugin setup

No `libs.versions.toml` entry is needed — the plugin is applied directly in Gradle files.

Root `build.gradle` — apply the aggregator plugin:

```groovy
plugins {
    id 'info.solidsoft.pitest.aggregator' version '1.20.6'
}
```

### 2. Subproject configuration in `main.gradle`

```groovy
apply plugin: 'info.solidsoft.pitest'

pitest {
    targetClasses = ['{base.package}.*']
    pitestVersion = '1.20.6'
    junit5PluginVersion = '1.2.3'
    threads = 8
    outputFormats = ['XML', 'HTML']
    exportLineCoverage = true
    useClasspathFile = true
    timestampedReports = false
    failWhenNoMutations = false
    mutationThreshold = 20
    jvmArgs = ["-XX:+EnableDynamicAgentLoading", "-XX:+AllowRedefinitionToAddDeleteMethods"]
}
```

> Replace `{base.package}` with the actual base package (e.g., `com.company.myservice`).

### 3. Configuration parameters explained

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `targetClasses` | `['{base.package}.*']` | Scope of classes to mutate |
| `pitestVersion` | `1.20.6` | PIT engine version |
| `junit5PluginVersion` | `1.2.3` | JUnit 5 integration plugin |
| `threads` | `8` | Parallel mutation execution |
| `outputFormats` | `['XML', 'HTML']` | Report formats (XML for CI, HTML for humans) |
| `exportLineCoverage` | `true` | Include line coverage in reports |
| `useClasspathFile` | `true` | Avoid command-line length limits on Windows |
| `timestampedReports` | `false` | Overwrite previous reports (no date folders) |
| `failWhenNoMutations` | `false` | Do not fail modules with no mutable code |
| `mutationThreshold` | `20` | Build fails if kill rate < 20% |
| `jvmArgs` | See config | Required for Java 21+ agent compatibility |

### 4. Running mutation tests

Per subproject:

```bash
./gradlew :application:app-service:pitest
```

All subprojects:

```bash
./gradlew pitest
```

### 5. Aggregated report

Generate a combined HTML report across all subprojects:

```bash
./gradlew pitestReportAggregate
```

Output location: `build/reports/pitest/`

### 6. Interpreting results

- **Killed mutant:** A test detected the mutation — test is effective.
- **Survived mutant:** No test detected the mutation — assertion gap exists.
- **No coverage:** The mutated code is not reached by any test.

Focus improvement efforts on survived mutants in business-critical code (domain, use cases).

## Verification Checklist

- [ ] `info.solidsoft.pitest` plugin applied in `main.gradle`
- [ ] `info.solidsoft.pitest.aggregator` applied in root `build.gradle`
- [ ] `targetClasses` matches the project base package
- [ ] `mutationThreshold` is set to at least `20`
- [ ] `./gradlew pitest` runs without errors
- [ ] `./gradlew pitestReportAggregate` generates combined report
- [ ] HTML report is reviewable at `build/reports/pitest/`

## Tools and Resources

- `info.solidsoft.pitest` — Gradle plugin for PIT mutation testing
- `info.solidsoft.pitest.aggregator` — Multi-module report aggregation
- PIT engine `1.20.6` with JUnit 5 plugin `1.2.3`
