<!-- keywords: hexagonal architecture, multi-module, project structure, folder structure, module layout, domain model ports usecases, driven-adapters, entry-points, helpers, app-service, Gradle modules, settings.gradle, dependency rule, clean architecture, layer structure, infrastructure, application assembler, hexagonal layers, hexagonal architecture -->
# Hexagonal Multi-Module Architecture for Microservices

## Purpose

Define the standard hexagonal multi-module architecture that the standard for microservices. This is the canonical, language-agnostic definition. It is the **single source of truth** for layer and module structure. For language-specific implementations, see the corresponding folders (`java/`, `typescript/`, `python/`).

## Scope of Application

- When creating a new microservice with hexagonal architecture.
- To validate the structure of existing projects.
- During architecture reviews.
- When defining where new components should live.
- When onboarding teams on the standard structure.

## General structure

Hexagonal architecture organizes a microservice into three concentric layers. The domain is at the center, completely isolated from technologies. Infrastructure is on the outside, connecting the domain to the real world. The application layer assembles everything.

```
┌─────────────────────────────────────────────────┐
│                 INFRASTRUCTURE                  │
│                                                 │
│   Entry Points          Driven Adapters         │
│   (inbound              (outbound               │
│    adapters)             adapters)               │
│                                                 │
│         ┌───────────────────────┐               │
│         │        DOMAIN         │               │
│         │                       │               │
│         │  model  ports usecases│               │
│         │                       │               │
│         └───────────────────────┘               │
│                                                 │
│              ┌──────────────┐                   │
│              │  APPLICATION │                   │
│              │  (assembler) │                   │
│              └──────────────┘                   │
└─────────────────────────────────────────────────┘
```

## Ports and Adapters

Communication between layers happens through ports (interfaces) and adapters (implementations):

- **Inbound ports:** the use cases. They define what operations the domain offers.
- **Outbound ports:** `I*Gateway` interfaces in `domain/ports`. They define what the domain needs from the outside world (persist data, send messages, call another service). The naming convention is **always `I*Gateway`** (e.g., `IAccountGateway`, `ITransactionGateway`, `INotificationGateway`). This is **NON-NEGOTIABLE**.
- **Inbound adapters (entry-points):** receive stimuli from the outside (HTTP, events, queues) and call use cases.
- **Outbound adapters (driven-adapters):** implement `I*Gateway` interfaces from `domain/ports` with concrete technology (JPA, REST client, SQS, etc.). The naming convention for implementation classes is **always `*Adapter`** (e.g., `AccountJpaAdapter`, `TransactionRestAdapter`, `NotificationSqsAdapter`).

## Folder structure

```
project/
├── domain/
│   ├── model/
│   ├── ports/
│   └── usecases/
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── outbound-adapter-a/
│   │   ├── outbound-adapter-b/
│   │   └── .../
│   ├── entry-points/
│   │   ├── inbound-adapter-a/
│   │   ├── inbound-adapter-b/
│   │   └── .../
│   └── helpers/                    ← Cross utilities for the infrastructure layer
├── application/
│   └── app-service/
└── /             ← Mock of client corporate libraries. ALWAYS included.
```

Each folder inside `driven-adapters/` and `entry-points/` is an independent module. To add a new adapter (e.g., a Kafka consumer, a REST client to another service, a GraphQL endpoint), create a new module without touching existing ones. `helpers/` is also an independent module shared across the infrastructure layer. The `/` module is MANDATORY — it replicates the public API of client corporate libraries so the project compiles without access to private repositories.

## Layer: Domain

The heart of the microservice. It depends on no framework or technology. Pure language code only. It is divided into **three modules**:

### domain/model

Contains pure business entities, value objects, and enums. **Does not contain interfaces.** Interfaces live in the `ports` module.

```
model/src/main/{language}/{package}/model/
├── MyEntity               → Domain entity. Pure POJO/dataclass, no framework annotations.
├── AnotherEntity          → Another domain entity.
├── MyValueObject          → Domain value object.
└── MyEnum                 → Domain enumeration.
```

Entities are pure objects with getters, setters, builder. They have no framework annotations. The `model` module depends on nothing: it is pure language code.

**Note:** Lombok annotations (`@Data`, `@Builder`, `@Getter`, `@AllArgsConstructor`, etc.) are permitted in domain model entities. Lombok is a compile-time annotation processor — it generates no runtime dependency and does not violate domain purity.

### domain/ports

Contains **all interfaces (contracts)** that define what the domain needs from the outside world. It is a separate module that depends only on `model`.

```
ports/src/main/{language}/{package}/ports/
├── IAccountGateway             → Interface. Defines persistence operations for accounts.
├── INotificationGateway        → Interface. Defines notification sending.
├── IPaymentGateway             → Interface. Defines communication with payment services.
└── ITransactionGateway         → Interface. Defines operations on transactions.
```

Rules:
- Interfaces only define contracts (what is needed), never how. The domain doesn't know if data is persisted in SQL, NoSQL, file, or memory.
- The naming convention is **always `I*Gateway`**. Do not use `*Port`, do not use `*Repository` for domain interfaces. This is **NON-NEGOTIABLE**.
- All Java interfaces MUST use the `I` prefix (e.g., `IAccountGateway`, not `AccountGateway`). This applies to all interfaces: ports, services, and any contract defined in the domain.
- Depends only on `model`. No framework or infrastructure dependencies.

### domain/usecases

Contains business logic. Each class is a use case.

```
usecases/src/main/{language}/{package}/usecases/
├── CreateEntityUseCase
├── GetEntityUseCase
└── AnotherUseCaseUseCase
```

Rules:
- No framework annotations. They are plain language classes.
- Receive outbound ports (`I*Gateway` interfaces from `ports` module) via constructor.
- Registered as beans/components from the application layer (not from here).
- Depend only on `model` and `ports`. Never on infrastructure.

## Layer: Infrastructure

Connects the domain to the outside world. Divided into inbound adapters, outbound adapters, and shared helpers. Each adapter is an independent module.

### infrastructure/driven-adapters (outbound adapters)

Implement `I*Gateway` interfaces defined in `domain/ports` using concrete technology. Each implementation class follows the `*Adapter` convention. Each adapter has this internal structure:

```
my-adapter/src/main/{language}/{package}/my-adapter/
├── entities/                       → Framework-specific entities (e.g., @Entity JPA, Mongo documents)
│   └── MyEntityEntity                 Internal to the adapter. The domain never sees them.
├── repository/                     → Framework interfaces or clients (e.g., JpaRepository, WebClient)
│   └── MyEntityFrameworkRepo
├── MyEntityMapper                  → Mapper: MapStruct @Mapper(componentModel="spring") interface. NEVER manual/static mappers in Java.
└── AccountJpaAdapter               → THE main class. Implements I*Gateway interface from domain/ports.
```

**Mapper rule (Java):** All mappers in Java projects MUST be MapStruct `@Mapper(componentModel = "spring")` interfaces. Manual mappers with static methods are FORBIDDEN. MapStruct is mandatory for all Java mappers.

Examples of outbound adapters:
- `persistence/` → database with JPA/Hibernate
- `r2dbc-persistence/` → reactive database with R2DBC
- `rest-consumer/` → HTTP client to another microservice
- `sqs-publisher/` → message publisher to a queue
- `redis-cache/` → cache with Redis
- `s3-storage/` → file storage

#### Module naming convention for external API adapters

When a driven adapter consumes an external REST API, the module MUST be named `{external_system_name}-client-api`. The name should be descriptive and immediately identify the external system:



For non-REST adapters, use descriptive names that reflect the technology and purpose:
- `oracle-repository` — Oracle stored procedures via JDBC/R2DBC
- `{system}-soap-api` — SOAP service consumer
- `kafka-publisher` — Kafka message producer
- `dynamodb-persistence` — DynamoDB persistence

Do NOT use generic prefixes like `rest-consumer-*` or `adapter-*`. The module name must be self-explanatory.

### infrastructure/entry-points (inbound adapters)

Receive stimuli from the outside and call use cases. Each adapter has this internal structure:

```
my-entry-point/src/main/{language}/{package}/my-entry-point/
├── dto/
│   ├── MyRequest
│   └── MyResponse
├── exception/
│   ├── GlobalExceptionHandler
│   └── MyCustomException
├── MyRestMapper                    → Mapper: MapStruct @Mapper(componentModel="spring") interface. NEVER manual/static mappers in Java.
└── MyController                    → THE main class.
```

Examples of inbound adapters:
- `rest/` → REST API with HTTP controllers (imperative/Spring MVC)
- `reactive-web/` → REST API with Router + Handler (reactive/WebFlux)
- `graphql/` → GraphQL endpoint
- `event-listener/` → event consumer (Kafka, SQS, RabbitMQ)
- `scheduled-tasks/` → scheduled tasks

### infrastructure/helpers (cross-cutting utilities)

A shared Gradle module within the infrastructure layer that contains utilities used by both `driven-adapters` and `entry-points`. This is NOT a dumping ground — only truly cross-cutting infrastructure concerns belong here.

```
helpers/src/main/{language}/{package}/helpers/
├── RequestParameterValidator    → Abstract class for validating query params, path variables, and request bodies.
├── DateFormatHelper             → Date parsing/formatting utilities specific to the infrastructure layer.
└── ...                          → Other cross-cutting infrastructure utilities.
```

For the canonical implementation pattern of `RequestParameterValidator`, see `09-patterns/java/request-parameter-validator.java.md`.

Rules:
- `helpers/` is a Gradle module with its own `build.gradle`.
- It depends on `model` and `ports` (+ framework dependencies as needed).
- Both `driven-adapters/*` and `entry-points/*` can depend on `helpers/`.
- Business logic NEVER goes here — only infrastructure-level utilities.
- Domain-level utilities belong in `domain/model/`, not here.
- Each adapter's internal utilities (mappers, converters) live directly in the adapter's own package, not in this shared module.

## Layer: Application (app-service)

The assembler. Joins all modules, boots the framework, and configures beans/components. Depends on all modules. Contains NO business logic and NO use cases.

```
app-service/src/main/{language}/{package}/
├── MainApplication             → Main class. Boots the framework.
└── config/
    └── UseCasesConfig          → Registers use cases via @ComponentScan regex.

app-service/src/main/resources/
├── application.yml             → ALL centralized microservice configuration.
│                                  Nothing is hardcoded. Everything configurable goes here.
├── schema.sql                  → Table DDL (optional, for in-memory DB)
└── data.sql                    → Initial data (optional)
```

### UseCasesConfig — Mandatory for every Java project

Every Java project MUST include a `UseCasesConfig` class in `application/app-service/src/main/java/{package}/config/`. This class uses `@ComponentScan` with a regex filter to auto-detect all classes ending in `UseCase` from the `domain/usecases` module:

```java
@Configuration
@ComponentScan(
    basePackages = "{base.package}.usecase",
    includeFilters = {
        @ComponentScan.Filter(type = FilterType.REGEX, pattern = "^.+UseCase$")
    },
    useDefaultFilters = false
)
public class UseCasesConfig {
}
```

Rules:
- The `basePackages` points to the usecases package in the domain module.
- The regex `^.+UseCase$` auto-registers any class whose name ends in `UseCase` as a Spring component.
- Use cases do NOT need `@Component`, `@Service`, or any Spring annotation — the regex scan handles registration.
- The class body is ALWAYS empty. No `@Bean` methods. All use cases are auto-wired by the scan.
- Use cases MUST NOT depend on other use cases. If shared logic is needed across multiple use cases, create a Domain Service in `domain/usecases/` (Use cases MUST NOT depend on other use cases. If shared logic is needed, create a Domain Service.).

The framework automatically injects the concrete `I*Gateway` implementation (the `*Adapter` in driven-adapters) into use cases via constructor injection.

## Dependency rules

```
model              → nothing (pure language code)
ports              → model only
usecases           → model + ports
helpers            → model + ports (+ framework dependencies)
driven-adapters    → model + ports + helpers
entry-points       → model + ports + usecases + helpers
app-service        → all modules
 → nothing (standalone)
```

Dependencies always point toward the domain. Infrastructure depends on the domain, never the other way around. The domain doesn't know any framework, protocol, or concrete technology exists.

## Sub-package summary

| Sub-package / Module | Where it appears | Purpose |
|----------------------|-----------------|---------|
| `model` | `domain/model` | Pure business entities, value objects, enums. No interfaces, no framework |
| `ports` | `domain/ports` | All `I*Gateway` interfaces defining what the domain needs from the outside |
| `usecases` | `domain/usecases` | Business logic. Each class is a use case. Depends on model + ports |
| `helpers/` (infra) | `infrastructure/helpers` | cross-cutting infrastructure utilities (e.g., `RequestParameterValidator`). Shared by driven-adapters and entry-points |
| `entities/` | `driven-adapters` | Framework-specific entities (JPA, Mongo, etc.). Internal to the adapter |
| `repository/` | `driven-adapters` | Framework interfaces or clients (JpaRepository, WebClient, etc.) |
| `dto/` | `entry-points` | Protocol input/output objects. Never expose domain directly |
| `exception/` | `entry-points` | Error handling and exception translation to protocol |
| `config/` | `app-service` | Bean configuration and framework properties |

## Naming conventions

| Component | Suffix / Convention | Example | Location |
|-----------|-------------------|---------|----------|
| Domain entity | POJO (no suffix required) | `Account`, `Transaction` | `domain/model/` |
| Value object | POJO (no suffix required) | `Money`, `AccountNumber` | `domain/model/` |
| Domain enum | Enum (no suffix required) | `OrderStatus`, `Currency` | `domain/model/` |
| Output port (interface) | `I*Gateway` | `IAccountGateway`, `INotificationGateway` | `domain/ports/` |
| Use case | `*UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` | `domain/usecases/` |
| Driven adapter (class) | `*Adapter` | `AccountJpaAdapter`, `TransactionRestAdapter` | `infrastructure/driven-adapters/*/` |
| Framework entity (SQL/JPA) | `*Entity` | `AccountEntity`, `TransactionEntity` | `driven-adapters/*/entities/` |
| Framework entity (MongoDB) | `*Document` | `AccountDocument`, `TransactionDocument` | `driven-adapters/*/entities/` |
| Framework entity (DynamoDB) | `*Item` | `AccountItem`, `TransactionItem` | `driven-adapters/*/entities/` |
| Framework repository | `*Repository` | `AccountJpaRepository`, `AccountR2dbcRepository` | `driven-adapters/*/repository/` |
| Persistence mapper | `*EntityMapper` | `AccountEntityMapper` | `driven-adapters/*/` |
| Router (WebFlux reactive) | `*Router` | `AccountRouter`, `OrderRouter` | `entry-points/reactive-web/` |
| Handler (WebFlux reactive) | `*Handler` | `AccountHandler`, `OrderHandler` | `entry-points/reactive-web/` |
| Controller (Spring MVC imperative) | `*Controller` | `AccountController` | `entry-points/rest/` |
| DTO request | `*Request` (Java Record) | `AccountRequest`, `CreateOrderRequest` | `entry-points/*/dto/` |
| DTO response | `*Response` (Java Record) | `AccountResponse`, `OrderResponse` | `entry-points/*/dto/` |
| REST mapper | `*RestMapper` | `AccountRestMapper` | `entry-points/*/` |

The `I*Gateway` convention for interfaces and `*Adapter` for implementations is **NON-NEGOTIABLE** across all projects. The `*UseCase` suffix for use cases is equally mandatory.

### Naming conventions by language (detailed)

For complete naming conventions including file naming, module naming, mapper rules, and import patterns, see the language-specific references:

- **Java:** the naming conventions reference for the corresponding language
- **Python:** the corresponding reference
- **TypeScript:** the corresponding reference

### Mapper implementation by language

| Language | Mapper technology | Implementation | Decision |
|----------|------------------|----------------|----------|
| **Java** | MapStruct (compile-time) | `@Mapper(componentModel = "spring")` interface | the MapStruct mandatory decision — MANDATORY, no manual mappers |
| **Python** | Manual mapper class | Plain class with `to_entity()` / `to_model()` methods | No framework — pure Python |
| **TypeScript** | Manual mapper function | Pure functions or static class methods | No framework — pure TypeScript |

### Correct vs incorrect naming

**Ports (`I*Gateway`):**

| Correct | Incorrect |
|---------|-----------|
| `IAccountGateway` | `AccountGateway` (missing I prefix) |
| `ITransactionGateway` | `TransactionRepository` (wrong suffix) |
| `INotificationGateway` | `NotificationService` (wrong suffix) |

Structure: `I{ConceptName}Gateway` — PascalCase with `I` prefix.

**Adapters (`*Adapter`):**

| Gateway | Adapter | Technology |
|---------|---------|------------|
| `IAccountGateway` | `AccountJpaAdapter` | JPA/Hibernate |
| `IAccountGateway` | `AccountR2dbcAdapter` | R2DBC (reactive) |
| `IAccountGateway` | `AccountDynamoAdapter` | DynamoDB |
| `ITransactionGateway` | `TransactionRestAdapter` | REST client |
| `INotificationGateway` | `NotificationSqsAdapter` | Amazon SQS |

Structure: `{ConceptName}{Technology}Adapter`

**Use cases (`*UseCase`):**

| Correct | Incorrect |
|---------|-----------|
| `CreateAccountUseCase` | `AccountService` |
| `GetAccountUseCase` | `AccountUseCase` (too generic) |
| `TransferFundsUseCase` | `TransferService` |

Structure: `{Action}{Concept}UseCase`

## Important rules

> **⚠️ Every microservice MUST follow this structure EXACTLY. Deviations from this structure (e.g., placing use cases in application/, using port/in and port/out instead of ports/, or putting entry-points at root level) are NOT acceptable and will require remediation.**

- Dependencies always flow toward the domain (inward).
- The domain NEVER knows about infrastructure.
- Use cases are the inbound ports of the domain.
- `I*Gateway` interfaces in `domain/ports` are the outbound ports of the domain.
- `domain/model` is pure code: entities, value objects, enums. **Does not contain interfaces.**
- `domain/ports` contains **all** interfaces. Depends only on `model`.
- `domain/usecases` contains business logic. Depends on `model` and `ports`.
- Each adapter is an independent module with its own internal structure.
- DTOs live inside each entry-point, not in a shared layer.
- Mappers live inside each adapter's package, not in a shared layer.
- Framework entities live inside each driven-adapter; the domain never sees them.
- Implementations in driven-adapters are named `*Adapter` and implement `I*Gateway` interfaces from `domain/ports`.
- `infrastructure/helpers/` is a shared module for cross-cutting infrastructure utilities. Both driven-adapters and entry-points can depend on it. It is NOT for business logic.

## Anti-patterns — What NOT to do

These are recurring structural mistakes that developers produce. Each one violates the hexagonal multi-module architecture defined in this document. If you generate any of these, the output is non-compliant.

| Anti-pattern | Why it's wrong | Correct structure |
|---|---|---|
| Use cases in `application/` (e.g., `application/usecase/`, `application/service/`) | `application/app-service/` is ONLY the assembler: `MainApplication` + `UseCaseConfig`. It must NEVER contain business logic or use cases. | Use cases MUST be in `domain/usecases/`. Each class is a `*UseCase` that depends only on `model` and `ports`. |
| `domain/port/in/` and `domain/port/out/` sub-packages | The standard does not use `in/out` separation for ports. The `port` (singular) naming is also wrong. | Ports MUST be in `domain/ports/` (plural, flat). Only `I*Gateway` interfaces. No `in/` or `out/` sub-packages. |
| `entry-points/` at root level (e.g., `project/entry-points/`) | Entry-points are inbound adapters and belong inside the infrastructure layer, not at the project root. | Entry-points MUST be inside `infrastructure/entry-points/{adapter-name}/` (e.g., `infrastructure/entry-points/reactive-web/`). |
| Flat `infrastructure/` module with all adapters in one package (e.g., `infrastructure/adapter/out/`) | Infrastructure MUST be organized into independent Gradle modules per adapter, not a single flat module. | Infrastructure MUST have `driven-adapters/` with individual Gradle modules per adapter (e.g., `driven-adapters/external-client-api/`, `driven-adapters/external-two-client-api/`). |
| `MainApplication` in entry-points (e.g., `entry-points/Application.java`) | The main class boots the framework and assembles all modules. It belongs in the application layer, not in an inbound adapter. | `MainApplication` MUST be in `application/app-service/`. |
| Missing `infrastructure/helpers/` module | The `helpers/` module is mandatory for cross infrastructure utilities (e.g., `RequestParameterValidator`). Without it, shared utilities end up duplicated or misplaced. | `infrastructure/helpers/` MUST exist as its own Gradle module with its own `build.gradle`. |
| All adapters in one flat module (e.g., a single `infrastructure/` with `core/`, `config/`, `dto/`, `mapper/` sub-packages) | Each driven adapter must be independently deployable and testable. A flat module couples all adapters together and violates module isolation. | Each driven adapter MUST be its own Gradle module inside `infrastructure/driven-adapters/` with its own `build.gradle`, `entities/`, `repository/`. |
| Manual/static mappers in Java (e.g., `AccountMapper.toEntity()` as static method, or manual mapper classes) | Manual mappers are error-prone, verbose, and have no compile-time field coverage validation. They also have runtime overhead vs compile-time generated code. | ALL mappers in Java projects MUST be MapStruct `@Mapper(componentModel = "spring")` interfaces. MapStruct is mandatory for all Java mappers. |
| Importing client libraries as real dependencies (e.g., adding Artifactory/Nexus URLs to `build.gradle`) | Client libraries are hosted in private repositories not accessible during generation. Importing them directly causes build failures. | Client libraries MUST ALWAYS be mocked. see the corresponding decision. The mock replicates the public API with the exact same packages. |
| `application/app-service/` inside `domain/` (e.g., `domain/app-service/`) | The application layer is the assembler — it depends on ALL modules. Placing it inside domain creates a circular dependency and breaks the Dockerfile and settings.gradle. | `application/app-service/` MUST be at the project root level, as a sibling of `domain/` and `infrastructure/`. |
| DTOs as classes with getters/setters (e.g., `AccountRequest` as a `@Data` class) | DTOs should be immutable data carriers. Classes with mutable state and Lombok `@Data` add unnecessary complexity and risk unintended mutation. | DTOs MUST be Java Records (Java 16+). Use `public record AccountRequest(@NotBlank String name) {}`. |
| Missing `GlobalErrorWebExceptionHandler` in WebFlux projects | Without a global error handler, unhandled exceptions return raw stack traces or generic 500 errors. WebFlux requires `AbstractErrorWebExceptionHandler`, not `@RestControllerAdvice`. | Every WebFlux project MUST include a `GlobalErrorWebExceptionHandler extends AbstractErrorWebExceptionHandler` in `infrastructure/entry-points/reactive-web/exception/`. |
| Interfaces without `I` prefix in Java (e.g., `AccountGateway` instead of `IAccountGateway`) | Java convention requires `I` prefix on all interfaces for immediate visual identification. | All Java interfaces MUST have `I` prefix: `IAccountGateway`, `INotificationGateway`, etc. |
| DTOs with `*DTO` suffix (e.g., `CreateUserRequestDTO`, `AccountResponseDTO`) | The `DTO` suffix is redundant when the class lives in a `dto/` package. It adds noise to class names. | Use `*Request` / `*Response` directly: `CreateUserRequest`, `AccountResponse`. No `DTO` suffix. |
| Mock module with generic names (e.g., `stubs/`, `mock-libs/`) | Generic names don't identify which client library is being mocked. | The mock module for client libraries MUST be named `` (e.g., ``, ``). Do NOT use generic names like `stubs/` or `mock-libs/`. |

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
