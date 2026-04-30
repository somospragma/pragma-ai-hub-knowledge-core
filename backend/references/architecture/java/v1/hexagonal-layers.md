<!-- keywords: hexagonal architecture, multi-module, ports and adapters, layers, modules, java, spring boot, gradle, domain model ports usecases, driven-adapters, entry-points, helpers, app-service, dependency rule, clean architecture, layer structure, infrastructure, application assembler, hexagonal layers, hexagonal architecture, mapstruct, gateway interface, use case registration, quality tools, jacoco, pitest, sonarqube, owasp, archunit, settings.gradle, main.gradle, gradle.properties, client-lib-mocks, anti-patterns -->
# Hexagonal Multi-Module Architecture — Java Implementation

## Purpose

Define the Java-specific implementation of hexagonal multi-module architecture.

## Scope of Application

- When creating a new Java microservice with hexagonal architecture.
- To validate the structure of an existing Java project.
- During code reviews of Java microservices.
- When refactoring a legacy Java service toward hexagonal.

## Mandatory tech stack

- **Java:** 21 (minimum and current standard)
- **Framework:** Spring Boot 4.x (based on Spring Framework 7)
- **Build:** Gradle multi-module with version catalog (`libs.versions.toml`). Maven is NOT used.
- **Jakarta EE:** 11 (stack baseline)
- **Lombok:** boilerplate reduction for entities and use cases
- **MapStruct:** compile-time mapping for ALL mappers

## Complete folder structure

```
project/
├── domain/
│   ├── model/
│   │   └── src/main/java/{package}/model/
│   │       ├── Account.java
│   │       ├── AccountStatus.java
│   │       └── Transaction.java
│   ├── ports/
│   │   └── src/main/java/{package}/ports/
│   │       ├── IAccountGateway.java
│   │       └── ITransactionGateway.java
│   └── usecases/
│       └── src/main/java/{package}/usecases/
│           ├── CreateAccountUseCase.java
│           └── GetAccountUseCase.java
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── persistence/
│   │   │   └── src/main/java/{package}/persistence/
│   │   │       ├── entities/
│   │   │       │   └── AccountEntity.java
│   │   │       ├── repository/
│   │   │       │   └── AccountJpaRepository.java
│   │   │       ├── AccountEntityMapper.java        ← MapStruct @Mapper interface
│   │   │       └── AccountJpaAdapter.java
│   │   └── {system}-client-api/
│   │       └── src/main/java/{package}/{system}clientapi/
│   │           ├── dto/
│   │           │   └── TransactionRestResponse.java
│   │           ├── TransactionAdapterMapper.java    ← MapStruct @Mapper interface
│   │           └── TransactionRestAdapter.java
│   ├── entry-points/
│   │   └── rest/
│   │       └── src/main/java/{package}/rest/
│   │           ├── dto/
│   │           │   ├── AccountRequest.java          ← Java Record
│   │           │   └── AccountResponse.java         ← Java Record
│   │           ├── exception/
│   │           │   └── GlobalExceptionHandler.java
│   │           ├── AccountRestMapper.java           ← MapStruct @Mapper interface
│   │           └── AccountController.java
│   └── helpers/
│       └── src/main/java/{package}/helpers/
│           └── RequestParameterValidator.java
├── application/
│   └── app-service/
│       ├── src/main/java/{package}/
│       │   ├── MainApplication.java
│       │   └── config/
│       │       └── UseCasesConfig.java
│       └── src/main/resources/
│           └── application.yml
├── /
│   └── src/main/java/...                           ← Replicates client library public API
├── gradle/
│   └── libs.versions.toml
├── build.gradle
├── settings.gradle
├── main.gradle
├── gradle.properties
├── lombok.config
├── Dockerfile
├── README.md
└── .gitignore
```


## Layer: Domain

The domain is divided into **3 independent Gradle modules**: `model`, `ports`, and `usecases`. None have framework dependencies. Pure Java and Lombok only.

### domain/model

Pure domain entities as POJOs with Lombok. No `@Entity`, `@Table`, `@Column`, or any framework annotations. Contains entities, value objects, and enums.

**Interfaces are NOT defined here.** Interfaces (outbound ports) live in `domain/ports`.

```java
package com.company.accounts.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Account {
    private String id;
    private String holderName;
    private String accountNumber;
    private BigDecimal balance;
    private AccountStatus status;
    private LocalDateTime createdAt;
}
```

```java
package com.company.accounts.model;

public enum AccountStatus {
    ACTIVE,
    INACTIVE,
    BLOCKED
}
```

```java
package com.company.accounts.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Transaction {
    private String id;
    private String accountId;
    private BigDecimal amount;
    private String description;
    private LocalDateTime executedAt;
}
```

### domain/ports

**Separate Gradle module.** Contains ALL interfaces (outbound ports) that the domain needs from the outside world. Every interface uses the `I` prefix and `*Gateway` suffix. Depends only on `model`.

The `I` prefix on all interfaces is **NON-NEGOTIABLE**. Do not use `AccountGateway` — it MUST be `IAccountGateway`.

```java
package com.company.accounts.ports;

import com.company.accounts.model.Account;

import java.util.List;
import java.util.Optional;

public interface IAccountGateway {
    Account save(Account account);
    Optional<Account> findById(String id);
    Optional<Account> findByAccountNumber(String accountNumber);
    List<Account> findAll();
    void deleteById(String id);
}
```

```java
package com.company.accounts.ports;

import com.company.accounts.model.Transaction;

import java.util.List;

public interface ITransactionGateway {
    Transaction register(Transaction transaction);
    List<Transaction> findByAccountId(String accountId);
}
```

Rules:
- Interfaces define contracts (what is needed), never how. The domain does not know if data is persisted in SQL, NoSQL, file, or memory.
- Naming convention is **always `I*Gateway`**. Do not use `*Port`, `*Repository`, or `*Service` for domain interfaces.
- `domain/ports/` is FLAT. No `in/` or `out/` sub-packages.
- Depends only on `model`. No framework or infrastructure dependencies.

### domain/usecases

Plain Java classes with business logic. Use `@RequiredArgsConstructor` from Lombok for constructor injection. No `@Service`, `@Component`, or any Spring annotation. They are registered as beans from `UseCasesConfig` in the application layer via regex scan. Depend on `model` and `ports`.

```java
package com.company.accounts.usecases;

import com.company.accounts.model.Account;
import com.company.accounts.model.AccountStatus;
import com.company.accounts.ports.IAccountGateway;
import lombok.RequiredArgsConstructor;

import java.time.LocalDateTime;

@RequiredArgsConstructor
public class CreateAccountUseCase {

    private final IAccountGateway accountGateway;

    public Account execute(Account account) {
        account.setStatus(AccountStatus.ACTIVE);
        account.setCreatedAt(LocalDateTime.now());
        return accountGateway.save(account);
    }
}
```

```java
package com.company.accounts.usecases;

import com.company.accounts.model.Account;
import com.company.accounts.ports.IAccountGateway;
import lombok.RequiredArgsConstructor;

@RequiredArgsConstructor
public class GetAccountUseCase {

    private final IAccountGateway accountGateway;

    public Account execute(String id) {
        return accountGateway.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Account not found: " + id));
    }
}
```


## Layer: Infrastructure

Connects the domain to the outside world. Divided into driven-adapters (outbound), entry-points (inbound), and helpers (cross-cutting). Each adapter is an independent Gradle module.

### driven-adapters/persistence (JPA example)

Implements `IAccountGateway` using JPA. The main adapter class always ends in `*Adapter`.

**Framework entity** (internal to the adapter — the domain never sees it):

```java
package com.company.accounts.persistence.entities;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "accounts")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AccountEntity {
    @Id
    private String id;

    @Column(name = "holder_name")
    private String holderName;

    @Column(name = "account_number", unique = true)
    private String accountNumber;

    @Column(name = "balance")
    private BigDecimal balance;

    @Column(name = "status")
    @Enumerated(EnumType.STRING)
    private String status;

    @Column(name = "created_at")
    private LocalDateTime createdAt;
}
```

**Framework repository interface** (internal to the adapter):

```java
package com.company.accounts.persistence.repository;

import com.company.accounts.persistence.entities.AccountEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface AccountJpaRepository extends JpaRepository<AccountEntity, String> {
    Optional<AccountEntity> findByAccountNumber(String accountNumber);
}
```

**MapStruct mapper** (mandatory):

```java
package com.company.accounts.persistence;

import com.company.accounts.model.Account;
import com.company.accounts.persistence.entities.AccountEntity;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

**Adapter class** (implements the domain gateway):

```java
package com.company.accounts.persistence;

import com.company.accounts.model.Account;
import com.company.accounts.persistence.entities.AccountEntity;
import com.company.accounts.persistence.repository.AccountJpaRepository;
import com.company.accounts.ports.IAccountGateway;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
@RequiredArgsConstructor
public class AccountJpaAdapter implements IAccountGateway {

    private final AccountJpaRepository jpaRepository;
    private final AccountEntityMapper mapper;

    @Override
    public Account save(Account account) {
        if (account.getId() == null) {
            account.setId(UUID.randomUUID().toString());
        }
        AccountEntity entity = mapper.toEntity(account);
        AccountEntity saved = jpaRepository.save(entity);
        return mapper.toModel(saved);
    }

    @Override
    public Optional<Account> findById(String id) {
        return jpaRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public Optional<Account> findByAccountNumber(String accountNumber) {
        return jpaRepository.findByAccountNumber(accountNumber).map(mapper::toModel);
    }

    @Override
    public List<Account> findAll() {
        return jpaRepository.findAll().stream().map(mapper::toModel).toList();
    }

    @Override
    public void deleteById(String id) {
        jpaRepository.deleteById(id);
    }
}
```

### driven-adapters/{system}-client-api (REST client)

Implements `ITransactionGateway` by consuming an external REST service. The module name MUST follow the `{system}-client-api` convention — do NOT use `rest-consumer`.

**DTO for external API response:**

```java
package com.company.accounts.transactionsclientapi.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record TransactionRestResponse(
    String id,
    String accountId,
    BigDecimal amount,
    String description,
    LocalDateTime executedAt
) {}
```

**MapStruct mapper:**

```java
package com.company.accounts.transactionsclientapi;

import com.company.accounts.model.Transaction;
import com.company.accounts.transactionsclientapi.dto.TransactionRestResponse;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface TransactionAdapterMapper {
    Transaction toModel(TransactionRestResponse response);
}
```

**Adapter class:**

```java
package com.company.accounts.transactionsclientapi;

import com.company.accounts.model.Transaction;
import com.company.accounts.ports.ITransactionGateway;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;

@Component
public class TransactionRestAdapter implements ITransactionGateway {

    private final RestClient restClient;
    private final TransactionAdapterMapper mapper;

    public TransactionRestAdapter(
            @Value("${transactions-service.base-url}") String baseUrl,
            TransactionAdapterMapper mapper) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
        this.mapper = mapper;
    }

    @Override
    public Transaction register(Transaction transaction) {
        TransactionRestResponse response = restClient.post()
            .uri("/api/v1/transactions")
            .body(transaction)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError,
                (request, resp) -> {
                    throw new IllegalStateException("Transaction registration failed");
                })
            .body(TransactionRestResponse.class);
        return mapper.toModel(response);
    }

    @Override
    public List<Transaction> findByAccountId(String accountId) {
        List<TransactionRestResponse> responses = restClient.get()
            .uri("/api/v1/transactions?accountId={accountId}", accountId)
            .retrieve()
            .body(new ParameterizedTypeReference<>() {});
        return responses.stream().map(mapper::toModel).toList();
    }
}
```


### entry-points/rest (Spring MVC — imperative)

Imperative pattern with `@RestController` and `@RequestMapping`. For the reactive variant (WebFlux with Router/Handler), see the corresponding archetype reference.

**DTOs as Java Records:**

```java
package com.company.accounts.rest.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.math.BigDecimal;

public record AccountRequest(
    @NotBlank String holderName,
    @NotBlank String accountNumber,
    @NotNull BigDecimal initialBalance
) {}
```

```java
package com.company.accounts.rest.dto;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public record AccountResponse(
    String id,
    String holderName,
    String accountNumber,
    BigDecimal balance,
    String status,
    LocalDateTime createdAt
) {}
```

**MapStruct mapper for the entry-point:**

```java
package com.company.accounts.rest;

import com.company.accounts.model.Account;
import com.company.accounts.rest.dto.AccountRequest;
import com.company.accounts.rest.dto.AccountResponse;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface AccountRestMapper {
    @Mapping(target = "id", ignore = true)
    @Mapping(target = "status", ignore = true)
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(source = "initialBalance", target = "balance")
    Account toModel(AccountRequest request);

    @Mapping(source = "status", target = "status")
    AccountResponse toResponse(Account account);
}
```

**Controller:**

```java
package com.company.accounts.rest;

import com.company.accounts.model.Account;
import com.company.accounts.rest.dto.AccountRequest;
import com.company.accounts.rest.dto.AccountResponse;
import com.company.accounts.usecases.CreateAccountUseCase;
import com.company.accounts.usecases.GetAccountUseCase;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {

    private final CreateAccountUseCase createAccountUseCase;
    private final GetAccountUseCase getAccountUseCase;
    private final AccountRestMapper mapper;

    @PostMapping
    public ResponseEntity<AccountResponse> create(@Valid @RequestBody AccountRequest request) {
        Account model = mapper.toModel(request);
        Account result = createAccountUseCase.execute(model);
        return ResponseEntity.status(HttpStatus.CREATED)
            .body(mapper.toResponse(result));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AccountResponse> getById(@PathVariable String id) {
        Account result = getAccountUseCase.execute(id);
        return ResponseEntity.ok(mapper.toResponse(result));
    }
}
```

**Global error handler:**

```java
package com.company.accounts.rest.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ProblemDetail> handleNotFound(IllegalArgumentException ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(problem);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetail> handleGeneral(Exception ex) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(
            HttpStatus.INTERNAL_SERVER_ERROR, "Internal server error");
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(problem);
    }
}
```

### infrastructure/helpers

A shared Gradle module within the infrastructure layer for cross-cutting utilities used by both `driven-adapters` and `entry-points`. This is NOT a dumping ground — only truly cross-cutting infrastructure concerns belong here.

```
helpers/src/main/java/{package}/helpers/
├── RequestParameterValidator.java    → Abstract class for validating query params, path variables, and request bodies.
├── DateFormatHelper.java             → Date parsing/formatting utilities specific to the infrastructure layer.
└── ...                               → Other cross-cutting infrastructure utilities.
```

Rules:
- `helpers/` is a Gradle module with its own `build.gradle`.
- It depends on `model` and `ports` (+ framework dependencies as needed).
- Both `driven-adapters/*` and `entry-points/*` can depend on `helpers/`.
- Business logic NEVER goes here — only infrastructure-level utilities.
- Domain-level utilities belong in `domain/model/`, not here.
- Each adapter's internal mappers live directly in the adapter's own package, not in this shared module.


## Layer: Application (app-service)

The assembler. Joins all modules, boots Spring Boot, and registers use cases via regex scan. Depends on all modules. Contains NO business logic and NO use cases.

**Main class:**

```java
package com.company.accounts;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.company.accounts")
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}
```

> **Note:** `@SpringBootApplication` is the default standard. Some clients may require a custom meta-annotation that extends `@SpringBootApplication` with additional configuration. In that case, replace `@SpringBootApplication` with the client annotation while maintaining the same semantics.

**UseCasesConfig — Mandatory regex scan (empty body, NO @Bean methods):**

```java
package com.company.accounts.config;

import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.FilterType;

@Configuration
@ComponentScan(
    basePackages = "com.company.accounts.usecases",
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
- The framework automatically injects the concrete `I*Gateway` implementation (the `*Adapter` in driven-adapters) into use cases via constructor injection.

**application.yml:**

```yaml
spring:
  application:
    name: accounts-service
  datasource:
    url: jdbc:postgresql://localhost:5432/accountsdb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
server:
  port: 8080
transactions-service:
  base-url: ${TRANSACTIONS_SERVICE_URL:https://api.transactions.internal}
```

##  module

The `` module (e.g., ``, ``) is **MANDATORY** for every microservice. It:

- Replicates the public API of client corporate libraries with working implementations.
- Uses the EXACT same package names as the real libraries.
- Is a Gradle module at the project root, NOT inside `infrastructure/`.
- Is referenced as `implementation project(':')` by modules that need it.
- The README documents how to replace it with real dependencies.

Client libraries are hosted in private repositories not accessible during generation. Importing them directly causes build failures.


## Dependency rules

```
model              → nothing (pure Java + Lombok)
ports              → model only
usecases           → model + ports
helpers            → model + ports + framework dependencies
driven-adapters    → model + ports + helpers
entry-points       → model + ports + usecases + helpers
app-service        → ALL modules
 → nothing (standalone)
```

Dependencies always point toward the domain. Infrastructure depends on the domain, never the other way around. The domain does not know that any framework, protocol, or concrete technology exists.

## Gradle configuration

### settings.gradle

Uses flat module names with `projectDir` mappings. This is the mandatory template:

```groovy
rootProject.name = 'accounts-service'

// Domain
include 'model'
project(':model').projectDir = file('domain/model')
include 'ports'
project(':ports').projectDir = file('domain/ports')
include 'use-case'
project(':use-case').projectDir = file('domain/usecases')

// Infrastructure — Driven Adapters
include 'persistence'
project(':persistence').projectDir = file('infrastructure/driven-adapters/persistence')
include 'transactions-client-api'
project(':transactions-client-api').projectDir = file('infrastructure/driven-adapters/transactions-client-api')

// Infrastructure — Entry Points
include 'rest'
project(':rest').projectDir = file('infrastructure/entry-points/rest')

// Infrastructure — Helpers
include 'helpers'
project(':helpers').projectDir = file('infrastructure/helpers')

// Application
include 'app-service'
project(':app-service').projectDir = file('application/app-service')

// Client library mocks — ALWAYS included
include ''
project(':').projectDir = file('')
```

### gradle.properties

Plugin versions are declared here (NOT in `libs.versions.toml`):

```properties
springBootVersion=4.0.3
springDependencyManagementVersion=1.1.7
sonarqubePluginVersion=6.0.1.5171
owaspDependencyTrackPluginVersion=12.1.0
pitestVersion=1.15.0
jacocoVersion=0.8.12
```

### gradle/libs.versions.toml

Library versions and dependency aliases:

```toml
[versions]
spring-boot = "4.0.3"
spring-dependency-management = "1.1.7"
lombok = "1.18.36"
mapstruct = "1.6.3"
archunit = "1.3.0"

[libraries]
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }
lombok-mapstruct-binding = { module = "org.projectlombok:lombok-mapstruct-binding", version = "0.2.0" }
spring-boot-starter-web = { module = "org.springframework.boot:spring-boot-starter-web" }
spring-boot-starter-data-jpa = { module = "org.springframework.boot:spring-boot-starter-data-jpa" }
spring-boot-starter-test = { module = "org.springframework.boot:spring-boot-starter-test" }
spring-boot-starter-validation = { module = "org.springframework.boot:spring-boot-starter-validation" }
jakarta-validation-api = { module = "jakarta.validation:jakarta.validation-api" }
archunit = { module = "com.tngtech.archunit:archunit-junit5", version.ref = "archunit" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version.ref = "spring-dependency-management" }
```

### build.gradle (root)

```groovy
plugins {
    id 'java'
    id 'jacoco'
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'org.springframework.boot' version "${springBootVersion}" apply false
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
}

allprojects {
    group = 'com.company.accounts'
    version = '1.0.0'
    repositories { mavenCentral() }
}

subprojects {
    apply plugin: 'java'
    apply from: "${rootDir}/main.gradle"

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(21)
        }
    }

    dependencies {
        compileOnly libs.lombok
        annotationProcessor libs.lombok
        implementation libs.mapstruct
        annotationProcessor libs.mapstruct.processor
        annotationProcessor libs.lombok.mapstruct.binding
        testCompileOnly libs.lombok
        testAnnotationProcessor libs.lombok
    }

    test { useJUnitPlatform() }
}
```

### main.gradle — Subproject quality configuration

`main.gradle` MUST configure ALL mandatory quality tools. An empty `main.gradle` is NOT compliant.

```groovy
// JaCoCo — Code coverage
apply plugin: 'jacoco'

jacoco {
    toolVersion = "${jacocoVersion}"
}

jacocoTestReport {
    reports {
        html.required = true
        xml.required = true
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

// PIT — Mutation testing
apply plugin: 'info.solidsoft.pitest'

pitest {
    targetClasses = ["com.company.accounts.*"]
    threads = 8
    outputFormats = ['XML', 'HTML']
    junit5PluginVersion = '1.2.1'
    mutationThreshold = 20
}

// MapStruct — Suppress timestamp in generated code
tasks.withType(JavaCompile).configureEach {
    options.compilerArgs += ['-Amapstruct.suppressGeneratorTimestamp=true']
}
```

### Module build.gradle examples

**domain/model/build.gradle:**

```groovy
dependencies {
    // No module dependencies. Pure Java + Lombok only.
}
```

**domain/ports/build.gradle:**

```groovy
dependencies {
    implementation project(':model')
}
```

**domain/usecases/build.gradle:**

```groovy
dependencies {
    implementation project(':model')
    implementation project(':ports')
}
```

**infrastructure/helpers/build.gradle:**

```groovy
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':model')
    implementation project(':ports')
    implementation libs.spring.boot.starter.web
}
```

**infrastructure/driven-adapters/persistence/build.gradle:**

```groovy
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':model')
    implementation project(':ports')
    implementation project(':helpers')
    implementation project(':')
    implementation libs.spring.boot.starter.data.jpa
}
```

**infrastructure/driven-adapters/{system}-client-api/build.gradle:**

```groovy
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':model')
    implementation project(':ports')
    implementation project(':helpers')
    implementation project(':')
    implementation libs.spring.boot.starter.web
}
```

**infrastructure/entry-points/rest/build.gradle:**

```groovy
apply plugin: libs.plugins.spring.dependency.management.get().pluginId
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':model')
    implementation project(':ports')
    implementation project(':use-case')
    implementation project(':helpers')
    implementation project(':')
    implementation libs.spring.boot.starter.web
    implementation libs.spring.boot.starter.validation
    implementation libs.jakarta.validation.api
}
```

**application/app-service/build.gradle:**

```groovy
apply plugin: libs.plugins.spring.boot.get().pluginId
apply plugin: libs.plugins.spring.dependency.management.get().pluginId

dependencies {
    implementation project(':model')
    implementation project(':ports')
    implementation project(':use-case')
    implementation project(':persistence')
    implementation project(':transactions-client-api')
    implementation project(':rest')
    implementation project(':helpers')
    implementation project(':')

    implementation libs.spring.boot.starter.web
    implementation libs.spring.boot.starter.data.jpa
    testImplementation libs.spring.boot.starter.test
    testImplementation libs.archunit
}

tasks.register('architectureTest', Test) {
    useJUnitPlatform()
    include '**/ArchitectureTest.class'
}
```


## Mandatory Quality Tools

Every Java project MUST include these quality tools. They are configured in `main.gradle` (subproject config) and `build.gradle` (plugin declarations). Versions come from `gradle.properties`.

| Tool | Plugin in build.gradle | Config in main.gradle | Purpose |
|------|----------------------|----------------------|---------|
| JaCoCo | `id 'jacoco'` | `jacocoTestReport`, `jacocoTestCoverageVerification` (85% minimum), `jacocoRootReport` (unified) | Code coverage. Minimum 85% line coverage. Unified report across all modules. |
| PIT (Pitest) | `id 'info.solidsoft.pitest'` | `pitest { targetClasses, threads=8, outputFormats=['XML','HTML'], mutationThreshold=20 }` | Mutation testing. Minimum 20% mutation score. |
| SonarQube | `id "org.sonarqube"` | `sonar { properties { host.url, token, coverage.exclusions } }` | Static analysis. Coverage exclusions MUST match JaCoCo. |
| OWASP Dependency Check | `id 'org.owasp.dependencycheck'` | `dependencyCheck { formats=['HTML','JSON','XML'], failBuildOnCVSS=11, scanConfigurations }` | Vulnerability scanning. Report-only mode (failBuildOnCVSS=11). |
| ArchUnit | _(test dependency in app-service)_ | `architectureTest` task in `app-service/build.gradle` | Architecture validation. Runs as part of `check`. |
| MapStruct | _(annotation processor in subprojects)_ | `options.compilerArgs = ['-Amapstruct.suppressGeneratorTimestamp=true']` | Compile-time mapper generation. Suppress timestamps in generated code. |

If `main.gradle` is empty or missing these tools, the project is NOT compliant.

## Naming conventions

| Component | Convention | Example | Location |
|-----------|-----------|---------|----------|
| Domain entity | POJO (no suffix required) | `Account`, `Transaction` | `domain/model/` |
| Value object | POJO (no suffix required) | `Money`, `AccountNumber` | `domain/model/` |
| Domain enum | Enum (no suffix required) | `AccountStatus`, `Currency` | `domain/model/` |
| Outbound port (interface) | `I*Gateway` | `IAccountGateway`, `ITransactionGateway` | `domain/ports/` |
| Use case | `*UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` | `domain/usecases/` |
| Driven adapter (class) | `*Adapter` | `AccountJpaAdapter`, `TransactionRestAdapter` | `infrastructure/driven-adapters/*/` |
| Framework entity (SQL/JPA) | `*Entity` | `AccountEntity` | `driven-adapters/*/entities/` |
| Framework entity (MongoDB) | `*Document` | `AccountDocument` | `driven-adapters/*/entities/` |
| Framework entity (DynamoDB) | `*Item` | `AccountItem` | `driven-adapters/*/entities/` |
| Framework repository | `*Repository` | `AccountJpaRepository` | `driven-adapters/*/repository/` |
| Persistence mapper | `*EntityMapper` | `AccountEntityMapper` | `driven-adapters/*/` |
| External API mapper | `*AdapterMapper` | `TransactionAdapterMapper` | `driven-adapters/*-client-api/` |
| Controller (Spring MVC) | `*Controller` | `AccountController` | `entry-points/rest/` |
| Router (WebFlux) | `*Router` | `AccountRouter` | `entry-points/reactive-web/` |
| Handler (WebFlux) | `*Handler` | `AccountHandler` | `entry-points/reactive-web/` |
| REST mapper | `*RestMapper` | `AccountRestMapper` | `entry-points/*/` |
| DTO request | `*Request` (Java Record) | `AccountRequest` | `entry-points/*/dto/` |
| DTO response | `*Response` (Java Record) | `AccountResponse` | `entry-points/*/dto/` |
| Driven adapter module (REST) | `{system}-client-api` | `transactions-client-api` | `infrastructure/driven-adapters/` |
| Driven adapter module (DB) | `{db}-repository` or `persistence` | `oracle-repository`, `persistence` | `infrastructure/driven-adapters/` |

The `I*Gateway` convention for interfaces and `*Adapter` for implementations is **NON-NEGOTIABLE** across all projects. The `*UseCase` suffix for use cases is equally mandatory.

## Anti-patterns — What NOT to do

These are recurring structural mistakes that developers produce. Each one violates the hexagonal multi-module architecture. If you generate any of these, the output is non-compliant.

| Anti-pattern | Why it's wrong | Correct structure |
|---|---|---|
| **Single `infrastructure/` module** with all adapters in one package | Infrastructure MUST be organized into independent Gradle modules per adapter, not a single flat module. | Each adapter is its own Gradle module inside `driven-adapters/` with its own `build.gradle`. |
| **`domain/ports/in/` and `domain/ports/out/`** sub-packages | The standard does not use `in/out` separation for ports. The `port` (singular) naming is also wrong. | `domain/ports/` is FLAT (plural). Only `I*Gateway` interfaces. No `in/` or `out/` sub-packages. |
| **Use cases in `application/`** (e.g., `application/usecase/`, `application/service/`) | `application/app-service/` is ONLY the assembler: `MainApplication` + `UseCasesConfig`. It must NEVER contain business logic. | Use cases MUST be in `domain/usecases/`. Each class is a `*UseCase` that depends only on `model` and `ports`. |
| **Mocks inside `infrastructure/`** (e.g., `infrastructure/src/main/java/...`) | Client library mocks must be a separate, standalone Gradle module at the project root. | Mocks are a separate Gradle module: `/` at the project root. |
| **Manual/static mappers** (e.g., `AccountMapper.toEntity()` as static method) | Manual mappers are error-prone, verbose, and have no compile-time field coverage validation. | ALL mappers MUST be MapStruct `@Mapper(componentModel = "spring")` interfaces. |
| **Missing `I` prefix on interfaces** (e.g., `AccountGateway` instead of `IAccountGateway`) | Java convention requires `I` prefix on all interfaces for immediate visual identification. | All Java interfaces MUST have `I` prefix: `IAccountGateway`, `ITransactionGateway`, etc. |
| **Missing `helpers/` module** | The `helpers/` module is mandatory for cross-cutting infrastructure utilities. Without it, shared utilities end up duplicated or misplaced. | `infrastructure/helpers/` MUST exist as its own Gradle module with its own `build.gradle`. |
| **`rest-consumer` as adapter name** | Generic names don't identify the external system being consumed. | Use `{system}-client-api` (e.g., `transactions-client-api`, `payments-client-api`). |
| **`UseCasesConfig` with `@Bean` methods** | Use cases are auto-registered by regex scan. Manual `@Bean` methods defeat the purpose and require maintenance for every new use case. | `UseCasesConfig` uses `@ComponentScan` with regex `^.+UseCase$`. Body is ALWAYS empty. |
| **DTOs as classes with getters/setters** (e.g., `@Data` class) | DTOs should be immutable data carriers. Mutable classes add unnecessary complexity. | DTOs MUST be Java Records: `public record AccountRequest(@NotBlank String name) {}`. |
| **DTOs with `*DTO` suffix** (e.g., `AccountResponseDTO`) | The `DTO` suffix is redundant when the class lives in a `dto/` package. | Use `*Request` / `*Response` directly: `AccountRequest`, `AccountResponse`. No `DTO` suffix. |
| **`app-service/` inside `domain/`** | The application layer depends on ALL modules. Placing it inside domain creates circular dependencies. | `application/app-service/` MUST be at the project root level, as a sibling of `domain/` and `infrastructure/`. |
| **`entry-points/` at root level** | Entry-points are inbound adapters and belong inside the infrastructure layer. | Entry-points MUST be inside `infrastructure/entry-points/{adapter-name}/`. |
| **Importing client libraries as real dependencies** | Client libraries are in private repositories not accessible during generation. | Client libraries MUST ALWAYS be mocked via `/`. |
| **Mock module with generic names** (e.g., `stubs/`, `mock-libs/`) | Generic names don't identify which client library is being mocked. | MUST be named `` (e.g., ``). |
| **Only 3 Gradle modules** (domain, infrastructure, app-service) | This is a monolithic structure, not hexagonal multi-module. | Minimum 8+ modules: model, ports, use-case, rest, at least one driven-adapter, helpers, app-service, . |

## Important rules

- Java 21 mandatory. Earlier versions are not supported.
- Gradle mandatory. Maven is not used.
- Spring Boot 4.x with Spring Framework 7 and Jakarta EE 11.
- The domain is divided into 3 Gradle modules: `model`, `ports`, and `usecases`.
- `domain/ports` is a separate module from `domain/model`. Interfaces do NOT live inside model.
- All outbound port interfaces are named `I*Gateway`. The `I` prefix is NON-NEGOTIABLE.
- All adapter classes are named `*Adapter`.
- DTOs are Java Records. No `@Data` classes for DTOs.
- Domain entities are POJOs with Lombok, no framework annotations.
- Use cases have no Spring annotations. They are registered via `UseCasesConfig` regex scan (empty body, NO `@Bean` methods). If the client provides a meta-annotation that already includes regex scan (e.g., {client}'s `@{client}MainApplication`), `UseCasesConfig` is not needed.
- Each adapter is an independent Gradle module with its own internal structure (`entities/`, `repository/`).
- Mappers are MapStruct `@Mapper(componentModel = "spring")` interfaces. No manual/static mappers.
- Framework entities are internal to each driven-adapter. The domain never sees them.
- `infrastructure/helpers/` is a mandatory shared module.
- `/` is a mandatory root-level module.
- `main.gradle` MUST contain quality tool configuration (JaCoCo 85%, PIT, SonarQube, OWASP, MapStruct). An empty `main.gradle` is NOT compliant.
- `gradle.properties` MUST exist with plugin versions.
- Use concrete domain names (Account, Transaction), not generic names (MyEntity).

## Enforced constraints (limits)

The following limits are enforced across ALL Java projects. Violating any of these results in rejected output:

| Limit | What it prohibits |
|-------|-------------------|
| I prefix on interfaces | Interfaces without `I` prefix (e.g., `AccountGateway` instead of `IAccountGateway`) |
| No manual/static mappers | Static method mappers, utility class mappers, any non-MapStruct mapping |
| DTOs must be Records | `@Data` classes for DTOs. All DTOs (request/response) must be Java Records |
| WebFlux non-blocking | `.block()`, `.blockFirst()`, `.blockLast()` outside tests |
| Default architecture | Deviating from hexagonal multi-module without explicit justification |
| Mandatory project files | Missing README, .gitignore, Dockerfile, build config files |

## Enforced decisions

The following decisions are mandatory for ALL Java projects and are embedded in this architecture:

| Decision | What it mandates |
|----------|------------------|
| MapStruct mandatory | All mappers must be `@Mapper(componentModel = "spring")` interfaces |
| Mock client libraries | `` module ALWAYS included |
| OWASP mandatory | OWASP plugin in build.gradle + config in main.gradle |
| Post-generation verification | compileJava → test → jacocoTestReport → dependencyCheckAnalyze |
| SonarQube mandatory | SonarQube plugin + config with env-var properties |
| Use case registration | Regex scan (empty body) or client annotation. Never manual @Bean |
| gradle.properties mandatory | Plugin versions in gradle.properties, library versions in libs.versions.toml |

## Tools and Resources

Consolidated from backend engineering archetype repositories and KB standards.

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_
