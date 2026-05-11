---
id: backend-skill-java-webflux-build-system
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Build System — Java WebFlux (Gradle)

## Propósito

Definir el template completo de `build.gradle` para cada módulo reactivo, `gradle.properties` obligatorio, `libs.versions.toml` (version catalog) con dependencias reactivas y `settings.gradle`.

---

## 1. gradle.properties (Raíz del Proyecto)

```properties
# --- [Main Properties] ---
package=com.pragma.myservice
reactive=true
lombok=true
language=java

# --- [Project Properties] ---
springBootVersion=4.0.3
springDependencyManagementVersion=1.1.7
pitestVersion=1.15.0

# --- [Plugin Versions] ---
sonarqubePluginVersion=6.0.1.5171
jacocoPluginVersion=0.8.12
owaspDependencyTrackPluginVersion=12.1.0

# --- [Gradle Performance Settings] ---
org.gradle.parallel=true
org.gradle.caching=true
org.gradle.daemon=true
org.gradle.jvmargs=-Xmx2g -XX:MaxMetaspaceSize=512m -XX:+HeapDumpOnOutOfMemoryError -Dfile.encoding=UTF-8
systemProp.file.encoding=UTF-8
org.gradle.console=plain

# --- [Corporate Repository Credentials] ---
azuredo_user=$(azuredo_user)
azuredo_pass=$(azuredo_pass)
azuredo_url=$(azuredo_url)
```

### Reglas de gradle.properties

- `reactive=true` indica que es un proyecto WebFlux.
- Versiones de **plugins** van aquí. Versiones de **librerías** van en `libs.versions.toml`.
- Credenciales son placeholders inyectados por CI/CD, **NUNCA** valores reales.
- `org.gradle.parallel=true` y `org.gradle.caching=true` son obligatorios.

---

## 2. gradle/libs.versions.toml (Version Catalog)

```toml
[versions]
spring-boot = "4.0.3"
spring-dependency-management = "1.1.7"
lombok = "1.18.36"
mapstruct = "1.5.5.Final"
archunit = "1.3.0"
springdoc = "2.7.0"
reactor-test = "3.7.6"
blockhound = "1.0.9.RELEASE"
resilience4j = "2.2.0"

[libraries]
# Spring Boot starters (reactivos)
boot-starter-webflux = { module = "org.springframework.boot:spring-boot-starter-webflux" }
boot-starter-r2dbc = { module = "org.springframework.boot:spring-boot-starter-data-r2dbc" }
boot-starter-mongodb-reactive = { module = "org.springframework.boot:spring-boot-starter-data-mongodb-reactive" }
boot-starter-security = { module = "org.springframework.boot:spring-boot-starter-security" }
boot-starter-validation = { module = "org.springframework.boot:spring-boot-starter-validation" }
boot-starter-actuator = { module = "org.springframework.boot:spring-boot-starter-actuator" }
boot-starter-test = { module = "org.springframework.boot:spring-boot-starter-test" }
boot-starter-opentelemetry = { module = "org.springframework.boot:spring-boot-starter-opentelemetry" }

# Reactor
reactor-test = { module = "io.projectreactor:reactor-test", version.ref = "reactor-test" }
blockhound = { module = "io.projectreactor.tools:blockhound", version.ref = "blockhound" }

# R2DBC drivers
r2dbc-postgresql = { module = "org.postgresql:r2dbc-postgresql" }
r2dbc-mssql = { module = "io.r2dbc:r2dbc-mssql" }

# Lombok
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }

# MapStruct
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }

# Validation
jakarta-validation-api = { module = "jakarta.validation:jakarta.validation-api" }

# Documentation
springdoc-webflux = { module = "org.springdoc:springdoc-openapi-starter-webflux-ui", version.ref = "springdoc" }

# Resilience
resilience4j-reactor = { module = "io.github.resilience4j:resilience4j-reactor", version.ref = "resilience4j" }
resilience4j-circuitbreaker = { module = "io.github.resilience4j:resilience4j-circuitbreaker", version.ref = "resilience4j" }
resilience4j-timelimiter = { module = "io.github.resilience4j:resilience4j-timelimiter", version.ref = "resilience4j" }

# Testing
archunit-junit5 = { module = "com.tngtech.archunit:archunit-junit5", version.ref = "archunit" }

# Kafka reactivo
reactor-kafka = { module = "io.projectreactor.kafka:reactor-kafka" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version.ref = "spring-dependency-management" }
```

### Reglas del Version Catalog

- **Todo** proyecto DEBE incluir `gradle/libs.versions.toml`.
- **Nunca** hardcodear versiones en `build.gradle`.
- Plugins se aplican con `alias(libs.plugins.<name>)`.
- Dependencias se referencian con `libs.<alias>`.
- Starters de Spring Boot sin `version.ref` heredan del plugin `spring-dependency-management`.
- Incluir dependencias reactivas: `webflux`, `r2dbc`, `reactor-test`, `blockhound`.

---

## 3. build.gradle (Root)

```groovy
plugins {
    id 'java'
    id 'jacoco'
    alias(libs.plugins.spring.boot) apply false
    alias(libs.plugins.spring.dependency.management) apply false
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
}

allprojects {
    group = "${package}"
    version = '1.0.0'
    repositories { mavenCentral() }
}

subprojects {
    apply plugin: 'java'
    apply from: "${rootDir}/main.gradle"

    java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }

    dependencies {
        compileOnly libs.lombok
        annotationProcessor libs.lombok
        annotationProcessor libs.mapstruct.processor
        testCompileOnly libs.lombok
        testAnnotationProcessor libs.lombok
    }

    test { useJUnitPlatform() }
}

// Reporte unificado JaCoCo
tasks.register('jacocoRootReport', JacocoReport) {
    description = 'Reporte unificado de cobertura JaCoCo'
    group = 'verification'
    dependsOn subprojects*.test

    additionalSourceDirs.from(subprojects.sourceSets.main.allSource.srcDirs)
    sourceDirectories.from(subprojects.sourceSets.main.allSource.srcDirs)
    classDirectories.from(subprojects.sourceSets.main.output)
    executionData.from(subprojects.collect {
        file("${it.layout.buildDirectory.get()}/jacoco/test.exec")
    }.findAll { it.exists() })

    reports {
        xml.required = true
        html.required = true
    }
}
```

---

## 4. main.gradle (Configuración de Calidad Obligatoria)

```groovy
// JaCoCo — Cobertura de Código
apply plugin: 'jacoco'

jacoco { toolVersion = "${jacocoPluginVersion}" }

jacocoTestReport {
    dependsOn test
    reports { xml.required = true; html.required = true }
}

jacocoTestCoverageVerification {
    violationRules {
        rule { limit { minimum = 0.85 } }
    }
}

test.finalizedBy jacocoTestReport

// PIT — Mutation Testing
apply plugin: 'info.solidsoft.pitest'

pitest {
    targetClasses = ["${project.group}.*"]
    threads = 8
    outputFormats = ['XML', 'HTML']
    junit5PluginVersion = '1.2.1'
    mutationThreshold = 20
}

// SonarQube — Análisis Estático
sonar {
    properties {
        property "sonar.host.url", System.getenv("SONAR_HOST_URL") ?: ""
        property "sonar.token", System.getenv("SONAR_TOKEN") ?: ""
        property "sonar.coverage.exclusions", [
            "**/config/**", "**/model/**", "**/dto/**",
            "**/mapper/**", "**/*MapperImpl.class",
            "**/entity/**", "**/MainApplication.java"
        ].join(",")
    }
}

// OWASP — Escaneo de Vulnerabilidades
dependencyCheck {
    formats = ['HTML', 'JSON', 'XML']
    failBuildOnCVSS = 11
    scanConfigurations = ['runtimeClasspath']
}

// MapStruct — Suprimir Timestamps
tasks.withType(JavaCompile).configureEach {
    options.compilerArgs += ['-Amapstruct.suppressGeneratorTimestamp=true']
}
```

---

## 5. settings.gradle

```groovy
rootProject.name = 'my-reactive-service'

include ':domain:model'
include ':domain:ports'
include ':domain:usecases'
include ':infrastructure:driven-adapters:r2dbc-persistence'
include ':infrastructure:driven-adapters:{name}-client-api'
include ':infrastructure:entry-points:reactive-web'
include ':infrastructure:helpers'
include ':application:app-service'

// Mock de librerías corporativas — SIEMPRE incluido
include '{client}-lib-mocks'
project(':{client}-lib-mocks').projectDir = file('{client}-lib-mocks')
```

---

## 6. build.gradle por Módulo

### domain/model

```groovy
// Sin dependencias adicionales (solo Java + Lombok heredado)
```

### domain/ports

```groovy
dependencies {
    implementation project(':domain:model')
    implementation 'io.projectreactor:reactor-core'
}
```

### domain/usecases

```groovy
dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation 'io.projectreactor:reactor-core'
}
```

### infrastructure/entry-points/reactive-web

```groovy
apply plugin: 'java-library'
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:helpers')
    implementation libs.boot.starter.webflux
    implementation libs.boot.starter.validation
    implementation libs.jakarta.validation.api
}
```

### infrastructure/driven-adapters/r2dbc-persistence

```groovy
apply plugin: 'java-library'
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':infrastructure:helpers')
    implementation libs.boot.starter.r2dbc
    implementation libs.mapstruct
    runtimeOnly libs.r2dbc.postgresql
}
```

### infrastructure/driven-adapters/{name}-client-api

```groovy
apply plugin: 'java-library'
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':infrastructure:helpers')
    implementation libs.boot.starter.webflux
    implementation libs.resilience4j.reactor
    implementation libs.resilience4j.circuitbreaker
}
```

### application/app-service

```groovy
apply plugin: libs.plugins.spring.boot.get().pluginId
apply plugin: libs.plugins.spring.dependency.management.get().pluginId

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:driven-adapters:r2dbc-persistence')
    implementation project(':infrastructure:driven-adapters:{name}-client-api')
    implementation project(':infrastructure:entry-points:reactive-web')
    implementation project(':infrastructure:helpers')
    implementation project(':{client}-lib-mocks')

    implementation libs.boot.starter.webflux
    implementation libs.boot.starter.r2dbc
    implementation libs.boot.starter.actuator
    runtimeOnly libs.r2dbc.postgresql

    testImplementation libs.boot.starter.test
    testImplementation libs.reactor.test
    testImplementation libs.blockhound
    testImplementation libs.archunit.junit5
}

tasks.register('architectureTest', Test) {
    useJUnitPlatform()
    include '**/ArchitectureTest.class'
}
```

---

## Checklist de Verificación

- [ ] `gradle.properties` existe con `reactive=true` y todas las versiones de plugins
- [ ] `gradle/libs.versions.toml` existe con dependencias reactivas (webflux, r2dbc, reactor-test, blockhound)
- [ ] `build.gradle` root declara los 5 plugins de calidad
- [ ] `main.gradle` configura JaCoCo (85%), PIT, SonarQube, OWASP, MapStruct
- [ ] `settings.gradle` incluye todos los módulos (reactive-web, r2dbc-persistence)
- [ ] Cada módulo tiene su `build.gradle` con dependencias correctas
- [ ] `domain/ports` y `domain/usecases` dependen de `reactor-core`
- [ ] `app-service` tiene ArchUnit, reactor-test y BlockHound
- [ ] No hay versiones hardcodeadas en ningún `build.gradle`
- [ ] No hay dependencias de `spring-boot-starter-webmvc` ni `spring-boot-starter-data-jpa`
