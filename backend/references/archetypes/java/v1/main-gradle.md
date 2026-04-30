<!-- keywords: gradle, main.gradle, static analysis, test coverage, code quality, jacoco, sonarqube, archunit, java -->
# Centralized main.gradle Script

## Purpose

Define a centralized Gradle script (`main.gradle`) that orchestrates cross-cutting tasks applicable to all project modules: static code analysis, test coverage, package structure validation, and corporate repositories.

## Scope of Application

- When the client requires a centralized Gradle script for cross-cutting tasks.
- To configure SonarQube, JaCoCo, PIT Testing, or other quality tools from a single point.
- When the project's package structure needs to be validated automatically.
- To define corporate repositories (Azure DevOps Artifacts, Nexus, etc.) centrally.

## Main Content

### What is main.gradle

It is a Gradle file (`main.gradle`) located at the project root that is applied from the root `build.gradle`. It centralizes configurations that would otherwise be repeated in each module's `build.gradle`.

### When It Applies

`main.gradle` is **MANDATORY for all Java hexagonal microservices**. It centralizes quality tools configuration. It applies when:

- The project follows the hexagonal archetype (always).
- The client has corporate artifact repositories (Azure DevOps Artifacts, private Nexus).
- Integration with corporate SonarQube is required.
- Mandatory code coverage is needed (JaCoCo with minimum threshold).
- Automated package structure validations are desired.
- PIT Testing (mutation testing) is used.
- OWASP Dependency Check for vulnerability scanning is needed.
- ArchUnit architecture validation is configured.

### Typical Structure

```groovy
// main.gradle — Centralized cross-cutting task script

// ─── 1. Corporate repositories ──────────────────────────────
allprojects {
    repositories {
        mavenCentral()
        // Corporate repository (Azure DevOps Artifacts, Nexus, etc.)
        maven {
            name = "corporate-artifacts"
            url = uri("https://pkgs.dev.azure.com/{org}/{project}/_packaging/{feed}/maven/v1")
            credentials {
                username = findProperty("corporateUser") ?: System.getenv("CORPORATE_USER")
                password = findProperty("corporateToken") ?: System.getenv("CORPORATE_TOKEN")
            }
        }
    }
}

// ─── 2. JaCoCo — Code coverage ─────────────────────────────
subprojects {
    apply plugin: 'jacoco'

    jacoco {
        toolVersion = "0.8.12"
    }

    jacocoTestReport {
        dependsOn test
        reports {
            xml.required = true
            html.required = true
        }
    }

    jacocoTestCoverageVerification {
        dependsOn jacocoTestReport
        violationRules {
            rule {
                limit {
                    minimum = 0.80 // Minimum threshold of 80%
                }
            }
        }
    }

    test.finalizedBy jacocoTestReport
}

// ─── 3. SonarQube — Static analysis ────────────────────────
plugins {
    id "org.sonarqube" version "5.1.0.4882"
}

sonar {
    properties {
        property "sonar.projectKey", findProperty("sonar.projectKey") ?: project.name
        property "sonar.projectName", findProperty("sonar.projectName") ?: project.name
        property "sonar.host.url", findProperty("sonar.host.url") ?: System.getenv("SONAR_HOST_URL")
        property "sonar.token", findProperty("sonar.token") ?: System.getenv("SONAR_TOKEN")
        property "sonar.coverage.jacoco.xmlReportPaths",
            "${project.buildDir}/reports/jacoco/test/jacocoTestReport.xml"
        property "sonar.coverage.exclusions", [
            "**/config/**", "**/configuration/**", "**/MainApplication.java",
            "**/*Config.class", "**/models/**", "**/dto/**", "**/mapper/**",
            "**/*MapperImpl.class", "**/entity/**", "**/*\$Builder.java"
        ].join(",")
    }
}

// ─── 4. Package structure validation ────────────────────────
task validatePackageStructure {
    description = "Validates that the package structure complies with the hexagonal archetype"
    group = "verification"

    doLast {
        def requiredModules = ['domain/model', 'domain/ports', 'domain/usecases', 'application/app-service']
        requiredModules.each { module ->
            def moduleDir = file(module)
            if (!moduleDir.exists()) {
                throw new GradleException("Required module not found: ${module}")
            }
        }
        println "✓ Package structure validated successfully"
    }
}

check.dependsOn validatePackageStructure

// ─── 5. PIT Testing — Mutation testing ─────────────────────
subprojects {
    apply plugin: 'info.solidsoft.pitest'

    pitest {
        junit5PluginVersion = '1.2.1'
        targetClasses = ["{base.package}.*"]
        threads = 4
        outputFormats = ['HTML', 'XML']
        mutationThreshold = 60
    }
}

// ─── 6. OWASP Dependency Check — Vulnerability scanning ────
subprojects {
    dependencyCheck {
        formats = ['HTML', 'JSON', 'XML']
        failBuildOnCVSS = 11
        scanConfigurations = ['runtimeClasspath', 'compileClasspath']
        nvd {
            apiKey = System.getenv('NVD_API_KEY') ?: project.findProperty('nvdApiKey')
        }
        analyzers {
            assemblyEnabled = false
            nuspecEnabled = false
            jarEnabled = true
        }
    }
}

// ─── 7. ArchUnit — Architecture validation ──────────────────
tasks.register('checkArchitecture') {
    group = 'verification'
    description = 'Runs architecture tests across the project'
    dependsOn ':app-service:architectureTest'
}

subprojects {
    afterEvaluate {
        if (tasks.findByName('check')) {
            tasks.check.dependsOn rootProject.tasks.checkArchitecture
        }
    }
}

// ─── 8. MapStruct — Suppress timestamp in generated code ────
tasks.withType(JavaCompile).configureEach {
    options.compilerArgs = ['-Amapstruct.suppressGeneratorTimestamp=true']
}

// ─── 9. CVE Fix Enforcement ─────────────────────────────────
subprojects {
    configurations.configureEach {
        resolutionStrategy.eachDependency { DependencyResolveDetails details ->
            // Pin vulnerable transitive dependencies to fixed versions
            // Add entries here as CVEs are discovered
        }
    }
}
```

### How to Apply main.gradle from the Root build.gradle

```groovy
// build.gradle (root)
apply from: 'main.gradle'

plugins {
    id 'java'
    id 'org.springframework.boot' version libs.versions.springBoot
    id 'io.spring.dependency-management' version libs.versions.springDependencyManagement
}

// ... rest of the configuration
```

### Relationship with Version Catalog (libs.versions.toml)

`main.gradle` complements the version catalog. The TOML centralizes dependency versions; `main.gradle` centralizes cross-cutting tasks. They do not replace each other.

```
gradle/
└── libs.versions.toml    ← Dependency versions (mandatory)
main.gradle               ← cross-cutting tasks (mandatory)
build.gradle              ← Root configuration (applies main.gradle)
settings.gradle           ← Module declarations
```

## Important Rules

- `main.gradle` is **MANDATORY**. It **MUST** be generated for every Java project.
- Corporate repository credentials MUST NEVER be hardcoded. They are read from properties or environment variables.
- The coverage threshold (JaCoCo) is defined by the client. The default is 80%.
- Structure validation must be adapted to the project's actual modules.
- SonarQube, PIT, JaCoCo, and OWASP Dependency Check are all **mandatory quality tools**.

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
