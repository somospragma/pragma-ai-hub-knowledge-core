<!-- keywords: hexagonal structure, module structure, Gradle modules, settings.gradle, project structure, quick reference, mandatory modules, anti-patterns, folder structure, multi-module, mock module, client-lib-mocks, driven-adapters, entry-points, helpers, app-service, domain model ports usecases, architecture checklist, module checklist -->

# Quick Reference: Hexagonal Multi-Module Structure

## Purpose

Compact, single-chunk reference of the mandatory Gradle module structure for hexagonal microservices. This is the authoritative checklist for module layout. For full details, see the hexagonal-layers architecture reference.

## Mandatory Gradle Modules

Every hexagonal Java microservice MUST have these Gradle modules declared in `settings.gradle`:

```
project-root/
├── domain/
│   ├── model/              ← Pure entities, value objects, enums. NO interfaces.
│   ├── ports/              ← ALL I*Gateway interfaces. Flat package, NO in/out sub-packages.
│   └── usecases/           ← Business logic. Each class is a *UseCase.
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── {system}-client-api/   ← One module PER external system (REST, SOAP, wrapper)
│   │   ├── {db}-repository/       ← Database adapter (if applicable)
│   │   └── .../                   ← Additional adapters as needed
│   ├── entry-points/
│   │   └── reactive-web/          ← Router + Handler (WebFlux) OR rest/ (Spring MVC)
│   └── helpers/                   ← Cross-cutting infra utilities (shared by adapters)
├── application/
│   └── app-service/               ← MainApplication + UseCasesConfig + application.yml
└── /            ← Mock of client corporate libraries. ALWAYS included.
```

## settings.gradle Template

```groovy
rootProject.name = '{micro-name}'

// Domain
include 'model'
project(':model').projectDir = file('domain/model')
include 'ports'
project(':ports').projectDir = file('domain/ports')
include 'use-case'
project(':use-case').projectDir = file('domain/usecases')

// Infrastructure
include 'reactive-web'
project(':reactive-web').projectDir = file('infrastructure/entry-points/reactive-web')
include '{system}-client-api'
project(':{system}-client-api').projectDir = file('infrastructure/driven-adapters/{system}-client-api')
include 'helpers'
project(':helpers').projectDir = file('infrastructure/helpers')

// Application
include 'app-service'
project(':app-service').projectDir = file('application/app-service')

// Client library mocks — ALWAYS included
include ''
project(':').projectDir = file('')
```

## Mock Module Rule

The `` module (e.g., ``, ``) is MANDATORY for every microservice. It:
- Replicates the public API of client corporate libraries with working implementations
- Uses the EXACT same package names as the real libraries
- Is a Gradle module at the project root, NOT inside `infrastructure/`
- Is referenced as `implementation project(':')` by modules that need it
- The README documents how to replace it with real dependencies

## Critical Anti-Patterns (NEVER do these)

| Anti-Pattern | Correct Structure |
|---|---|
| Single `infrastructure/` module with all adapters in one package | Each adapter is its own Gradle module inside `driven-adapters/` |
| `domain/ports/in/` and `domain/ports/out/` sub-packages | `domain/ports/` is FLAT. No `in/` or `out/` sub-packages. |
| Use cases inside `application/` | Use cases MUST be in `domain/usecases/` |
| `app-service/` inside `domain/` | `application/app-service/` is at project root level |
| Mocks inside `infrastructure/src/main/java/` | Mocks are a separate Gradle module: `/` |
| Missing `helpers/` module | `infrastructure/helpers/` MUST exist as its own Gradle module |
| `entry-points/` at project root | Entry-points are inside `infrastructure/entry-points/` |
| Only 3 Gradle modules (domain, infrastructure, app-service) | Minimum 7+ modules: model, ports, use-case, reactive-web, {adapter}, helpers, app-service,  |
| Interfaces without `I` prefix (`AccountGateway`) | ALL interfaces MUST have `I` prefix: `IAccountGateway` |
| Manual/static mappers (`SomeMapper.toModel()`) | ALL mappers MUST be MapStruct `@Mapper(componentModel = "spring")` interfaces |
| DTOs as `@Data` classes | ALL DTOs MUST be Java Records |
| `UseCasesConfig` with `@Bean` methods | `UseCasesConfig` body is ALWAYS empty (regex scan). Or not needed if client annotation handles it |
| Empty `main.gradle` | `main.gradle` MUST configure JaCoCo, PIT, SonarQube, OWASP, MapStruct |

## Dependency Rule

```
model           → nothing
ports           → model
usecases        → model + ports
helpers         → model + ports + framework
driven-adapters → model + ports + helpers
entry-points    → model + ports + usecases + helpers
app-service     → ALL modules
 → nothing (standalone)
```

## Mandatory Root Files

| File | All clients | {client} only |
|------|------------|-------------|
| `build.gradle` | ✅ | ✅ |
| `settings.gradle` | ✅ | ✅ |
| `main.gradle` | ✅ | ✅ |
| `gradle.properties` | ✅ | ✅ |
| `gradle/libs.versions.toml` | ✅ | ✅ |
| `Dockerfile` | ✅ | ✅ |
| `README.md` | ✅ | ✅ |
| `.gitignore` | ✅ | ✅ |
| `lombok.config` | ✅ | ✅ |
| `banner.txt` | ❌ | ✅ |
| `azure-pipelines.yml` | ❌ | ✅ |
| `k8s/cm.yaml` | ❌ | ✅ |
| `.env` | ❌ | ✅ |

## Mandatory Quality Tools (configured in main.gradle + build.gradle)

Every Java project MUST include these quality tools. They are configured in `main.gradle` (subproject config) and `build.gradle` (plugin declarations). The versions come from `gradle.properties`.

| Tool | Plugin in build.gradle | Config in main.gradle | Purpose |
|------|----------------------|----------------------|---------|
| JaCoCo | `id 'jacoco'` | `jacocoTestReport`, `jacocoTestCoverageVerification`, `jacocoRootReport` | Code coverage. Minimum 85% line coverage. Unified report across all modules. |
| PIT (Pitest) | `id 'info.solidsoft.pitest'` | `pitest { targetClasses, threads, outputFormats }` | Mutation testing. Minimum 20% mutation score. |
| SonarQube | `id "org.sonarqube"` | `sonar { properties { host.url, token, coverage.exclusions } }` | Static analysis. Coverage exclusions MUST match JaCoCo. |
| OWASP Dependency Check | `id 'org.owasp.dependencycheck'` | `dependencyCheck { formats, failBuildOnCVSS, scanConfigurations }` | Vulnerability scanning. Report-only mode (failBuildOnCVSS=11). |
| ArchUnit | _(test dependency)_ | `checkArchitecture` task in build.gradle | Architecture validation. Runs as part of `check`. |

If `main.gradle` is empty or missing these tools, the project is NOT compliant.

## Verification Checklist

- [ ] `settings.gradle` declares 7+ modules (model, ports, use-case, reactive-web, at least one adapter, helpers, app-service, )
- [ ] Each driven-adapter is its own Gradle module with its own `build.gradle`
- [ ] `domain/ports/` has NO `in/` or `out/` sub-packages
- [ ] ALL interfaces have `I` prefix (e.g., `IAccountGateway`, NOT `AccountGateway`)
- [ ] ALL mappers are MapStruct `@Mapper(componentModel = "spring")` interfaces — NO static/manual mappers
- [ ] ALL DTOs (request/response) are Java Records — NO `@Data` classes
- [ ] `/` exists as a root-level Gradle module
- [ ] No business logic in `application/app-service/`
- [ ] `UseCasesConfig` has empty body (regex scan only, NO `@Bean` methods). If client annotation handles scan, `UseCasesConfig` is not needed
- [ ] `infrastructure/helpers/` exists as its own module
- [ ] `gradle.properties` AND `gradle/libs.versions.toml` both exist
- [ ] `main.gradle` contains JaCoCo (85%), PIT, SonarQube, OWASP, and MapStruct configuration (NOT empty)
- [ ] `build.gradle` declares plugins: `jacoco`, `info.solidsoft.pitest`, `org.sonarqube`, `org.owasp.dependencycheck`
- [ ] ArchUnit test dependency in `app-service/build.gradle` with `architectureTest` task

## Enforced Constraints (Limits and Decisions)

These constraints are embedded in the architecture and MUST be enforced in every generated project:

| Constraint | Violation = Rejected Output |
|-----------|----------------------------|
| `I` prefix on ALL interfaces | ✅ |
| MapStruct for ALL mappers (no static/manual) | ✅ |
| DTOs as Java Records (no `@Data` classes) | ✅ |
| `main.gradle` complete with JaCoCo 85%, PIT, SonarQube, OWASP, MapStruct (not empty) | ✅ |
| `UseCasesConfig` empty body (no `@Bean` methods) | ✅ |
| `` module ALWAYS included | ✅ |
| Post-generation verification: compileJava → test → jacocoTestReport → dependencyCheckAnalyze | ✅ |

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
