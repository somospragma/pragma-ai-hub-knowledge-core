<!-- keywords: gradle.properties, build properties, plugin versions, spring boot version, gradle configuration, jvm args, corporate repository credentials, build system -->

# Reference: gradle.properties — Build System Configuration

## Purpose

Define the mandatory `gradle.properties` file that every Java hexagonal microservice MUST include at the project root. This file centralizes build system properties: plugin versions, framework versions, Gradle performance settings, and corporate repository credentials.

## Scope of Application

All Java projects (Spring Boot, WebFlux, Gradle). This file is ALWAYS included alongside `gradle/libs.versions.toml`.

## Relationship with libs.versions.toml

These two files are complementary and MUST ALWAYS coexist. They do NOT overlap:

| File | Responsibility | Referenced by | Example |
|------|---------------|---------------|---------|
| `gradle.properties` | Plugin versions, build system config, credentials | `${propertyName}` in `build.gradle` and `main.gradle` | `springBootVersion=3.5.9` |
| `gradle/libs.versions.toml` | Library/dependency versions | `libs.{alias}` in `dependencies {}` blocks | `{client} = "2.4.2-SNAPSHOT"` |

Gradle resolves `gradle.properties` first (settings phase), then the version catalog (dependency resolution phase). There is no conflict.

**Rule:** Plugin versions go in `gradle.properties`. Library versions go in `libs.versions.toml`. Never mix them.

## Step by Step / Guidelines

### Mandatory Structure

```properties
# --- [Main Properties] ---
package={base.package}
reactive=true
lombok=true
language=java

# --- [Project Properties] ---
springBootVersion={spring.boot.version}
springDependencyManagementVersion=1.1.7
springCloudVersion={spring.cloud.version}
lombokVersion={lombok.version}
pitestVersion={pitest.version}

# --- [Plugin Versions] ---
sonarqubePluginVersion={sonarqube.plugin.version}
jacocoPluginVersion={jacoco.plugin.version}
owaspDependencyTrackPluginVersion={owasp.plugin.version}

# --- [Gradle Performance Settings] ---
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.daemon=true
org.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
systemProp.file.encoding=UTF-8
org.gradle.console=plain

# --- [Corporate Repository Credentials] ---
# These are injected by the CI/CD pipeline. Placeholders only.
azuredo_user=$(azuredo_user)
azuredo_pass=$(azuredo_pass)
azuredo_url=$(azuredo_url)
```

### Property Categories

| Category | Properties | Description |
|----------|-----------|-------------|
| Main | `package`, `reactive`, `lombok`, `language` | Project metadata |
| Project | `springBootVersion`, `springCloudVersion`, `lombokVersion`, `pitestVersion` | Framework versions used in `build.gradle` via `${name}` |
| Plugins | `sonarqubePluginVersion`, `jacocoPluginVersion`, `owaspDependencyTrackPluginVersion` | Plugin versions for `plugins {}` block in `build.gradle` |
| Performance | `org.gradle.parallel`, `org.gradle.caching`, `org.gradle.daemon`, `org.gradle.jvmargs` | Gradle build performance tuning |
| Credentials | `azuredo_user`, `azuredo_pass`, `azuredo_url` | Corporate artifact repository credentials (CI/CD injected) |

### How Properties Are Consumed

```groovy
// build.gradle — uses gradle.properties for PLUGINS
plugins {
    id 'org.springframework.boot' version "${springBootVersion}"
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
    id 'jacoco'
}

// main.gradle — uses gradle.properties for Spring BOM
implementation platform("org.springframework.boot:spring-boot-dependencies:${springBootVersion}")

// main.gradle — uses gradle.properties for corporate repo
maven {
    url = "${azuredo_url}"
    credentials {
        username = "${azuredo_user}"
        password = "${azuredo_pass}"
    }
}
```

### Important Rules

- Credentials MUST NEVER be hardcoded. They are placeholders injected by CI/CD.
- `org.gradle.jvmargs` MUST include `-Dfile.encoding=UTF-8` for consistent builds.
- `org.gradle.parallel=true` and `org.gradle.caching=true` are mandatory for build performance.
- Plugin versions in `gradle.properties` MUST match the versions used in `build.gradle` `plugins {}` block.
- Library versions MUST NOT go in `gradle.properties` — they belong in `libs.versions.toml`.

## Verification Checklist

- [ ] `gradle.properties` exists at project root
- [ ] `springBootVersion` matches the Spring Boot plugin version in `build.gradle`
- [ ] `jacocoPluginVersion` matches JaCoCo toolVersion
- [ ] Corporate credentials are placeholders, not real values
- [ ] `org.gradle.parallel=true` and `org.gradle.caching=true` are set
- [ ] No library versions in this file (those go in `libs.versions.toml`)

## Tools and Resources

_(No additional information required for this section.)_
