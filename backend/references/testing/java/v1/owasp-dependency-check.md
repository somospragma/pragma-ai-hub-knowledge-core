<!-- keywords: owasp, dependency check, vulnerability scanning, CVE, security, dependency audit, supply chain security -->

# Reference: OWASP Dependency Check — Vulnerability Scanning

## Purpose

Define the standard OWASP Dependency Check configuration for Java Gradle projects. Scans project dependencies for known vulnerabilities (CVEs) from the National Vulnerability Database (NVD).

## Scope of Application

All Java projects. Configured in `build.gradle` (plugin declaration) and `main.gradle` (subproject configuration).

## Step by Step / Guidelines

### Plugin Declaration (build.gradle)

```groovy
plugins {
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
}
```

The version is defined in `gradle.properties`:
```properties
owaspDependencyTrackPluginVersion=12.1.8
```

### Subproject Configuration (main.gradle)

```groovy
subprojects {
    dependencyCheck {
        formats = ['HTML', 'JSON', 'XML']
        failBuildOnCVSS = 11    // Report only, do not fail build (max CVSS is 10)

        scanConfigurations = [
            'runtimeClasspath',
            'compileClasspath'
        ]

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
```

### Configuration Options

| Property | Value | Description |
|----------|-------|-------------|
| `formats` | `['HTML', 'JSON', 'XML']` | Output report formats. XML for SonarQube integration. |
| `failBuildOnCVSS` | `11` | CVSS threshold to fail build. Set to 11 (above max 10) to report without failing. Adjust per client. |
| `scanConfigurations` | `['runtimeClasspath', 'compileClasspath']` | Which Gradle configurations to scan |
| `nvd.apiKey` | env `NVD_API_KEY` | NVD API key for faster downloads. Optional but recommended. |
| `analyzers.assemblyEnabled` | `false` | Disable .NET assembly analysis (Java projects only) |
| `analyzers.nuspecEnabled` | `false` | Disable NuGet analysis (Java projects only) |
| `analyzers.jarEnabled` | `true` | Enable JAR analysis |

### SonarQube Integration

When SonarQube is configured, the OWASP report integrates automatically:

```groovy
sonarqube {
    properties {
        if (project.name == 'app-service') {
            property "sonar.dependencyCheck.reportPath", "build/reports/dependency-check-report.xml"
            property "sonar.dependencyCheck.htmlReportPath", "build/reports/dependency-check-report.html"
            property "sonar.dependencyCheck.summarize", "true"
        }
    }
}
```

### Report Location

Reports are generated in each subproject's `build/reports/` directory:
- `dependency-check-report.html` — Human-readable
- `dependency-check-report.json` — Machine-readable
- `dependency-check-report.xml` — SonarQube integration

### Running the Check

```bash
./gradlew dependencyCheckAnalyze
```

### CVE Fix Enforcement

In addition to scanning, known CVE fixes MUST be enforced via dependency version pinning in `main.gradle`:

```groovy
configurations.configureEach {
    resolutionStrategy.eachDependency { DependencyResolveDetails details ->
        if (details.requested.group == "io.netty") {
            details.useVersion("${libs.versions.netty.get()}")
            details.because("Fix CVE — enforced Netty LTS")
        }
    }
}
```

## Verification Checklist

- [ ] OWASP plugin declared in `build.gradle` with version from `gradle.properties`
- [ ] `dependencyCheck` block configured in `main.gradle` subprojects
- [ ] `formats` includes XML for SonarQube integration
- [ ] `nvd.apiKey` reads from environment variable
- [ ] Known CVE fixes enforced via `resolutionStrategy` in `main.gradle`
- [ ] SonarQube properties include dependency check report paths

## Tools and Resources

_(No additional information required for this section.)_
