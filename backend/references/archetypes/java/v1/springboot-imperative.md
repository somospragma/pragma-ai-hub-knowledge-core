<!-- keywords: spring boot, imperative, spring mvc, jpa, hibernate, gradle, multi-module, microservice, java, archetype, blocking -->
# Java Imperative Archetype — Spring Boot MVC + Gradle Multi-Module

## Purpose

Provide the standardized base for **imperative** (blocking) Java microservices using Spring MVC, JPA/Hibernate, and Gradle multi-module.

This file only covers what is **specific to the imperative paradigm**.

## Scope of Application

- Traditional request-response with JPA/Hibernate.
- Team is more familiar with blocking paradigm.
- Integrations are primarily JDBC-based with no reactive alternative.
- Simpler mental model is preferred over performance optimization.

## Mandatory tech stack

- **Java:** 21
- **Framework:** Spring Boot 4.x + **Spring MVC**
- **Build:** Gradle multi-module with version catalog (`libs.versions.toml`)
- **Persistence:** JPA / Hibernate (blocking)
- **HTTP Client:** `RestClient` (Spring 6.1+). NOT `RestTemplate` (deprecated).
- **Entry-points:** `@RestController` + `@GetMapping` / `@PostMapping` / etc.
- **Lombok:** boilerplate reduction
- **Testing:** `MockMvc` + JUnit 5

## Project structure

```
project/
├── domain/
│   ├── model/                          ← Pure entities, value objects, enums. No framework.
│   ├── ports/                          ← *Gateway interfaces. Plain Java return types.
│   └── usecases/                       ← *UseCase classes. Business logic.
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── persistence/                ← JPA/Hibernate persistence
│   │   ├── {name}-client-api/           ← External API consumer (RestClient)
│   │   └── .../
│   ├── entry-points/
│   │   └── rest/                       ← @RestController + @GetMapping
│   └── helpers/                        ← Cross infra utilities (RequestParameterValidator)
├── application/
│   └── app-service/                    ← MainApplication + UseCasesConfig + application.yml
├── gradle/
│   └── libs.versions.toml
├── build.gradle
├── gradle.properties
├── settings.gradle
├── main.gradle
├── lombok.config
├── Dockerfile
└── /            ← Mock of client corporate libraries. ALWAYS included.
```

## Key paradigm rules

1. **Return types** from use cases and gateways are plain Java types: `T`, `Optional<T>`, `List<T>`.
2. Entry-points use `@RestController` with annotation-based mapping.
3. Error handling with `@RestControllerAdvice`.
4. Persistence with JPA (`JpaRepository`).
5. HTTP consumption with `RestClient`.
6. Server: Tomcat (thread-per-request).
7. Filters: `OncePerRequestFilter`.

---

## Domain layer — Imperative specifics

### Ports (Gateway interfaces)

Return types are **plain Java types**:

```java
public interface IAccountGateway {
    Account save(Account account);
    Optional<Account> findById(String id);
    List<Account> findAll();
    void deleteById(String id);
}
```

### Use cases

Plain Java classes. No `@Service`, no `@Component`. Auto-registered by `UseCasesConfig` regex scan (`^.+UseCase$`):

```java
@RequiredArgsConstructor
public class CreateAccountUseCase {
    private final IAccountGateway accountGateway;

    public Account execute(String holderName, String holderDocument) {
        Account account = Account.builder()
            .holderName(holderName)
            .holderDocument(holderDocument)
            .balance(BigDecimal.ZERO)
            .status("ACTIVE")
            .createdAt(LocalDateTime.now())
            .build();
        return accountGateway.save(account);
    }
}
```

```java
@RequiredArgsConstructor
public class GetAccountUseCase {
    private final IAccountGateway accountGateway;

    public Account execute(String id) {
        return accountGateway.findById(id)
            .orElseThrow(() -> new IllegalArgumentException("Account not found: " + id));
    }
}
```

---

## Infrastructure layer — Imperative specifics

### driven-adapters/persistence (JPA)

JPA entity (internal to adapter):

```java
@Entity
@Table(name = "accounts")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AccountEntity {
    @Id private String id;
    @Column(name = "holder_name") private String holderName;
    @Column(name = "holder_document") private String holderDocument;
    @Column(name = "balance") private BigDecimal balance;
    @Column(name = "status") private String status;
    @Column(name = "created_at") private LocalDateTime createdAt;
}
```

JPA repository:

```java
public interface AccountJpaRepository extends JpaRepository<AccountEntity, String> {
}
```

Adapter implementing the gateway:

```java
@Repository
@RequiredArgsConstructor
public class AccountJpaAdapter implements IAccountGateway {
    private final AccountJpaRepository jpaRepository;
    private final AccountEntityMapper mapper;

    @Override
    public Account save(Account account) {
        if (account.getId() == null) { account.setId(UUID.randomUUID().toString()); }
        AccountEntity entity = mapper.toEntity(account);
        AccountEntity saved = jpaRepository.save(entity);
        return mapper.toModel(saved);
    }

    @Override
    public Optional<Account> findById(String id) {
        return jpaRepository.findById(id).map(mapper::toModel);
    }

    @Override
    public List<Account> findAll() {
        return jpaRepository.findAll().stream().map(mapper::toModel).toList();
    }

    @Override
    public void deleteById(String id) { jpaRepository.deleteById(id); }
}
```

MapStruct mapper (mandatory):

```java
@Mapper(componentModel = "spring")
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

### driven-adapters/{name}-client-api (RestClient)

```java
@Component
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final RestClient restClient;

    public ExternalServiceAdapter(@Value("${external-service.base-url}") String baseUrl) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
    }

    @Override
    public ExternalResource fetchById(String id) {
        ExternalResourceDto dto = restClient.get()
            .uri("/api/v1/resources/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError,
                (request, response) -> {
                    throw new ResourceNotFoundException("Not found: " + id);
                })
            .body(ExternalResourceDto.class);
        return ExternalServiceMapper.toModel(dto);
    }

    @Override
    public List<ExternalResource> fetchAll() {
        List<ExternalResourceDto> dtos = restClient.get()
            .uri("/api/v1/resources")
            .retrieve()
            .body(new ParameterizedTypeReference<List<ExternalResourceDto>>() {});
        return dtos.stream().map(ExternalServiceMapper::toModel).toList();
    }
}
```

### entry-points/rest (Spring MVC)

DTOs as Java Records:

```java
public record CreateAccountRequest(
    @NotBlank String holderName,
    @NotBlank String holderDocument
) {}

public record AccountResponse(
    String id, String holderName, String holderDocument,
    BigDecimal balance, String status, LocalDateTime createdAt
) {}
```

**Controller:**

```java
@RestController
@RequestMapping("/api/accounts")
@RequiredArgsConstructor
public class AccountController {
    private final CreateAccountUseCase createAccountUseCase;
    private final GetAccountUseCase getAccountUseCase;

    @PostMapping
    public ResponseEntity<AccountResponse> create(@Valid @RequestBody CreateAccountRequest request) {
        Account result = createAccountUseCase.execute(request.holderName(), request.holderDocument());
        return ResponseEntity.status(HttpStatus.CREATED).body(AccountRestMapper.toResponse(result));
    }

    @GetMapping("/{id}")
    public ResponseEntity<AccountResponse> getById(@PathVariable String id) {
        Account result = getAccountUseCase.execute(id);
        return ResponseEntity.ok(AccountRestMapper.toResponse(result));
    }
}
```

**Error handling:**

```java
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

---

## Application layer

```java
@SpringBootApplication(scanBasePackages = "{base.package}")
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}
```

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

`application.yml`:

```yaml
spring:
  application:
    name: my-imperative-service
  datasource:
    url: jdbc:postgresql://localhost:5432/mydb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
server:
  port: 8080
external-service:
  base-url: https://api.external.com
```

---

## Mandatory Quality Tools

Every project MUST include these quality tools configured in `main.gradle` and `build.gradle`. An empty `main.gradle` is NOT compliant.

### build.gradle (root) — Plugin declarations

```groovy
plugins {
    id "org.sonarqube" version "${sonarqubePluginVersion}"
    id 'org.owasp.dependencycheck' version "${owaspDependencyTrackPluginVersion}"
    id 'org.springframework.boot' version "${springBootVersion}" apply false
    id 'info.solidsoft.pitest' version "${pitestVersion}" apply false
    id 'jacoco'
}
```

Plugin versions come from `gradle.properties` (NOT from `libs.versions.toml`).

### main.gradle — Subproject configuration

`main.gradle` MUST configure ALL of these for every subproject:

| Tool | What it configures |
|------|-------------------|
| JaCoCo | `jacocoTestReport` (HTML + XML), `jacocoTestCoverageVerification` (85% minimum), `jacocoRootReport` (unified) |
| PIT | `pitest { targetClasses, threads=8, outputFormats=['XML','HTML'], junit5PluginVersion }` |
| SonarQube | `sonar { properties { host.url, token, coverage.exclusions matching JaCoCo } }` |
| OWASP | `dependencyCheck { formats=['HTML','JSON','XML'], failBuildOnCVSS=11, scanConfigurations }` |
| ArchUnit | `checkArchitecture` task depending on `:app-service:architectureTest` |
| MapStruct | `options.compilerArgs = ['-Amapstruct.suppressGeneratorTimestamp=true']` |

### app-service/build.gradle — ArchUnit test dependency

```groovy
testImplementation libs.archunit
```

With a dedicated `architectureTest` task:

```groovy
tasks.register('architectureTest', Test) {
    useJUnitPlatform()
    include '**/ArchitectureTest.class'
}
```

---

## Dependency rules

```
model           → nothing (Java + Lombok)
ports           → model
usecases        → model + ports
helpers         → model + ports + framework
driven-adapters → model + ports + helpers
entry-points    → model + ports + usecases + helpers
app-service     → ALL modules
 → nothing (standalone)
```

---

## Gradle configuration

### gradle/libs.versions.toml

```toml
[versions]
spring-boot = "4.0.3"
spring-dependency-management = "1.1.7"
lombok = "1.18.36"
mapstruct = "1.5.5.Final"

[libraries]
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }
spring-boot-starter-web = { module = "org.springframework.boot:spring-boot-starter-web" }
spring-boot-starter-data-jpa = { module = "org.springframework.boot:spring-boot-starter-data-jpa" }
spring-boot-starter-test = { module = "org.springframework.boot:spring-boot-starter-test" }
jakarta-validation-api = { module = "jakarta.validation:jakarta.validation-api" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version.ref = "spring-dependency-management" }
```

### build.gradle (root)

```groovy
plugins {
    alias(libs.plugins.spring.boot) apply false
    alias(libs.plugins.spring.dependency.management) apply false
}

allprojects {
    group = '{base.package}'
    version = '1.0.0'
    repositories { mavenCentral() }
}

subprojects {
    apply plugin: 'java'
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
```

### settings.gradle

```groovy
rootProject.name = 'my-imperative-service'
include ':domain:model'
include ':domain:ports'
include ':domain:usecases'
include ':infrastructure:driven-adapters:persistence'
include ':infrastructure:driven-adapters:{name}-client-api'
include ':infrastructure:entry-points:rest'
include ':infrastructure:helpers'
include ':application:app-service'

// Client library mocks — ALWAYS included
include ''
project(':').projectDir = file('')
```

### Module build.gradle examples

**domain/ports:**
```groovy
dependencies {
    implementation project(':domain:model')
}
```

**domain/usecases:**
```groovy
dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
}
```

**infrastructure/entry-points/rest:**
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
    implementation project(':')
    implementation libs.spring.boot.starter.web
    implementation libs.jakarta.validation.api
}
```

**application/app-service:**
```groovy
apply plugin: libs.plugins.spring.boot.get().pluginId
apply plugin: libs.plugins.spring.dependency.management.get().pluginId

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:driven-adapters:persistence')
    implementation project(':infrastructure:driven-adapters:{name}-client-api')
    implementation project(':infrastructure:entry-points:rest')
    implementation project(':infrastructure:helpers')
    implementation project(':')

    implementation libs.spring.boot.starter.web
    implementation libs.spring.boot.starter.data.jpa
    testImplementation libs.spring.boot.starter.test
}
```

---

## Enforced Constraints

These constraints apply to ALL imperative projects:

| Constraint |
|-----------|
| `I` prefix on ALL interfaces |
| MapStruct for ALL mappers (no static/manual) |
| DTOs as Java Records (no `@Data` classes) |
| `main.gradle` complete with all quality tools |
| `UseCasesConfig` empty body (no `@Bean`) |
| `` module ALWAYS included |

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
