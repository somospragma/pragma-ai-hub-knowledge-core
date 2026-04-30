<!-- keywords: lombok, lombok.config, code generation, annotations, getter, setter, builder, java, gradle -->
# Reference: Lombok Configuration for Java Projects

## Purpose

Ensure every Java project included in every project includes proper Lombok configuration: the `lombok.config` file at the project root and the transversal Lombok dependency declared once in the root `build.gradle`.

## Scope of Application

- All Java microservices regardless of client, architecture, or framework.
- Applies to both hexagonal (imperative and reactive) and simple pattern projects.
- Mandatory for Gradle multi-module projects.

## Step by Step / Guidelines

### 1. `lombok.config` file at project root

Every Java project MUST include a `lombok.config` file in the project root directory (same level as `build.gradle`):

```
proyecto/
├── lombok.config          ← MANDATORY
├── build.gradle
├── settings.gradle
├── gradle/
│   └── libs.versions.toml
└── ...
```

Content:

```properties
config.stopBubbling = true
lombok.addLombokGeneratedAnnotation = true
```

- `config.stopBubbling = true` — prevents Lombok from searching parent directories for additional config files. Ensures consistent behavior regardless of where the project is cloned.
- `lombok.addLombokGeneratedAnnotation = true` — adds `@Generated` annotation to Lombok-generated code. This is critical for JaCoCo and SonarQube to correctly exclude generated code from coverage reports.

### 2. Lombok version in Version Catalog

Declare the Lombok version in `gradle/libs.versions.toml`:

```toml
[versions]
lombok = "1.18.36"

[libraries]
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
```

### 3. Transversal dependency in root `build.gradle`

Declare Lombok once in the `subprojects` block of the root `build.gradle` so every module inherits it:

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

This ensures:
- `compileOnly` — Lombok is available at compile time but not bundled in the JAR.
- `annotationProcessor` — Lombok's annotation processor runs during compilation.
- `testCompileOnly` + `testAnnotationProcessor` — Lombok works in test classes too.

### 4. Do NOT declare Lombok in individual module `build.gradle` files

Since Lombok is inherited from `subprojects`, individual modules should NOT redeclare it. This avoids version drift and duplication.

## Verification Checklist

- [ ] `lombok.config` exists at project root
- [ ] `lombok.config` contains `config.stopBubbling = true`
- [ ] `lombok.config` contains `lombok.addLombokGeneratedAnnotation = true`
- [ ] `gradle/libs.versions.toml` declares `lombok` version
- [ ] Root `build.gradle` declares Lombok in `subprojects` block (compileOnly + annotationProcessor + test variants)
- [ ] No individual module `build.gradle` redeclares Lombok

## Tools and Resources

- JaCoCo + Lombok integration: the `@Generated` annotation ensures JaCoCo excludes Lombok-generated methods from coverage
