<!-- keywords: webflux, reactive, spring boot, project reactor, gradle, multi-module, microservice, java, archetype, non-blocking -->
# Java Reactive Archetype — Spring WebFlux + Gradle Multi-Module

## Purpose

Provide the standardized base for **reactive** Java microservices using Spring WebFlux, Project Reactor, and Gradle multi-module.

This file only covers what is **specific to the reactive paradigm**.

## Scope of Application

- High concurrency with limited resources (event-loop model).
- Consuming or exposing data streams.
- Persistence with R2DBC (reactive SQL) or MongoDB Reactive.
- Non-blocking HTTP integrations with `WebClient`.
- When the client's standard is reactive.

## Mandatory tech stack

- **Java:** 21
- **Framework:** Spring Boot 4.x + **Spring WebFlux**
- **Reactor:** Project Reactor (`Mono<T>`, `Flux<T>`)
- **Build:** Gradle multi-module with version catalog (`libs.versions.toml`)
- **Reactive persistence:** R2DBC or MongoDB Reactive
- **HTTP Client:** `WebClient` (NOT `RestTemplate`, NOT `RestClient`)
- **Entry-points:** Functional Endpoints (`RouterFunction<ServerResponse>` + Handler). **`@RestController` is NOT allowed.**
- **Lombok:** boilerplate reduction
- **Testing:** `StepVerifier` (Reactor Test) + `WebTestClient`

## Project structure

```
project/
├── domain/
│   ├── model/                          ← Pure entities, value objects, enums. No framework.
│   ├── ports/                          ← I*Gateway interfaces. Mono<T>/Flux<T> return types.
│   └── usecases/                       ← *UseCase classes. Business logic.
├── infrastructure/
│   ├── driven-adapters/
│   │   ├── r2dbc-persistence/          ← R2DBC reactive persistence
│   │   ├── {name}-client-api/          ← External API consumer (WebClient)
│   │   └── .../
│   ├── entry-points/
│   │   └── reactive-web/              ← Router + Handler (NOT @RestController)
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
└── /                 ← Mock of client corporate libraries. ALWAYS included.
```

## Key paradigm rules

1. **Every return type** from use cases, gateways, and handlers is `Mono<T>` or `Flux<T>`. No blocking types.
2. **Zero blocking calls** inside the reactive pipeline. No `.block()`, `.blockFirst()`, `.blockLast()` outside tests.
3. Entry-points use **Router + Handler** pattern. No `@RestController`, no `@GetMapping`.
4. Error handling with `AbstractErrorWebExceptionHandler`, NOT `@RestControllerAdvice`.
5. Persistence with R2DBC (`ReactiveCrudRepository`), NOT JPA/Hibernate.
6. HTTP consumption with `WebClient`, NOT `RestTemplate`.
7. Server: Netty (event-loop, non-blocking). NOT Tomcat.
8. Filters: `WebFilter`, NOT `OncePerRequestFilter`.

---

## Domain layer — Reactive specifics

### Ports (Gateway interfaces)

Return types are **always reactive**:

```java
public interface IAccountGateway {
    Mono<Account> save(Account account);
    Mono<Account> findById(String id);
    Flux<Account> findAll();
    Mono<Void> deleteById(String id);
}
```

### Use cases

All methods return `Mono<T>` or `Flux<T>`. Composition via reactive operators:

```java
@RequiredArgsConstructor
public class CreateAccountUseCase {
    private final IAccountGateway accountGateway;

    public Mono<Account> execute(Account account) {
        account.setStatus("ACTIVE");
        account.setCreatedAt(LocalDateTime.now());
        return accountGateway.save(account);
    }
}
```

```java
@RequiredArgsConstructor
public class GetAccountUseCase {
    private final IAccountGateway accountGateway;

    public Mono<Account> execute(String id) {
        return accountGateway.findById(id)
            .switchIfEmpty(Mono.error(
                new AccountNotFoundException("Account not found: " + id)));
    }

    public Flux<Account> findAll() {
        return accountGateway.findAll();
    }
}
```

---

## Infrastructure layer — Reactive specifics

### driven-adapters/r2dbc-persistence

R2DBC entity (internal to adapter):

```java
@Table("accounts")
@Data @Builder @NoArgsConstructor @AllArgsConstructor
public class AccountEntity {
    @Id private String id;
    private String holderName;
    private String accountType;
    private BigDecimal balance;
    private String status;
    private LocalDateTime createdAt;
}
```

Reactive repository:

```java
public interface AccountR2dbcRepository extends ReactiveCrudRepository<AccountEntity, String> {
    Flux<AccountEntity> findByStatus(String status);
}
```

Adapter implementing the gateway:

```java
@Repository
@RequiredArgsConstructor
public class AccountR2dbcAdapter implements IAccountGateway {
    private final AccountR2dbcRepository r2dbcRepository;
    private final AccountEntityMapper mapper;

    @Override
    public Mono<Account> save(Account account) {
        return r2dbcRepository.save(mapper.toEntity(account))
            .map(mapper::toModel);
    }

    @Override
    public Mono<Account> findById(String id) {
        return r2dbcRepository.findById(id)
            .map(mapper::toModel);
    }

    @Override
    public Flux<Account> findAll() {
        return r2dbcRepository.findAll()
            .map(mapper::toModel);
    }

    @Override
    public Mono<Void> deleteById(String id) {
        return r2dbcRepository.deleteById(id);
    }
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

### driven-adapters/{name}-client-api (WebClient)

ExternalServiceMapper (MapStruct — mandatory):

```java
@Mapper(componentModel = "spring")
public interface ExternalServiceMapper {
    ExternalResource toModel(ExternalResourceDto dto);
}
```

```java
@Component
@RequiredArgsConstructor
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final WebClient webClient;
    private final ExternalServiceMapper mapper;

    @Override
    public Mono<ExternalResource> fetchById(String id) {
        return webClient.get()
            .uri("/api/v1/resources/{id}", id)
            .retrieve()
            .onStatus(HttpStatusCode::is4xxClientError,
                response -> Mono.error(new ResourceNotFoundException("Not found: " + id)))
            .bodyToMono(ExternalResourceDto.class)
            .map(mapper::toModel);
    }
}
```

### entry-points/reactive-web

DTOs as Java Records:

```java
public record AccountRequest(
    @NotBlank String holderName,
    @NotBlank String accountType,
    @NotNull BigDecimal initialBalance
) {}

public record AccountResponse(
    String id, String holderName, String accountType,
    BigDecimal balance, String status, LocalDateTime createdAt
) {}
```

MapStruct mapper (mandatory):

```java
@Mapper(componentModel = "spring")
public interface AccountRestMapper {
    Account toModel(AccountRequest request);
    AccountResponse toResponse(Account account);
}
```

**Router** — defines routes as `RouterFunction<ServerResponse>`:

```java
@Configuration
@RequiredArgsConstructor
public class AccountRouter {
    private final AccountHandler handler;

    @Bean
    public RouterFunction<ServerResponse> accountRoutes() {
        return RouterFunctions.route()
            .GET("/api/v1/accounts/{id}", handler::findById)
            .GET("/api/v1/accounts", handler::findAll)
            .POST("/api/v1/accounts", handler::create)
            .DELETE("/api/v1/accounts/{id}", handler::delete)
            .build();
    }
}
```

**Handler** — processes requests, calls use cases, builds reactive responses:

```java
@Component
@RequiredArgsConstructor
public class AccountHandler {
    private final CreateAccountUseCase createAccountUseCase;
    private final GetAccountUseCase getAccountUseCase;
    private final AccountRestMapper accountRestMapper;

    public Mono<ServerResponse> findById(ServerRequest request) {
        String id = request.pathVariable("id");
        return getAccountUseCase.execute(id)
            .map(accountRestMapper::toResponse)
            .flatMap(response -> ServerResponse.ok().bodyValue(response))
            .switchIfEmpty(ServerResponse.notFound().build());
    }

    public Mono<ServerResponse> findAll(ServerRequest request) {
        return getAccountUseCase.findAll()
            .map(accountRestMapper::toResponse)
            .collectList()
            .flatMap(list -> ServerResponse.ok().bodyValue(list));
    }

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(AccountRequest.class)
            .map(accountRestMapper::toModel)
            .flatMap(createAccountUseCase::execute)
            .map(accountRestMapper::toResponse)
            .flatMap(response -> ServerResponse.status(HttpStatus.CREATED).bodyValue(response));
    }

    public Mono<ServerResponse> delete(ServerRequest request) {
        String id = request.pathVariable("id");
        return getAccountUseCase.execute(id)
            .flatMap(account -> ServerResponse.noContent().build())
            .switchIfEmpty(ServerResponse.notFound().build());
    }
}
```

**Error handling** — reactive global error handler:

```java
@Component
@Order(-2)
public class GlobalErrorWebExceptionHandler extends AbstractErrorWebExceptionHandler {

    public GlobalErrorWebExceptionHandler(
            ErrorAttributes errorAttributes,
            WebProperties.Resources resources,
            ApplicationContext applicationContext,
            ServerCodecConfigurer configurer) {
        super(errorAttributes, resources, applicationContext);
        this.setMessageWriters(configurer.getWriters());
    }

    @Override
    protected RouterFunction<ServerResponse> getRoutingFunction(ErrorAttributes errorAttributes) {
        return RouterFunctions.route(RequestPredicates.all(), this::renderErrorResponse);
    }

    private Mono<ServerResponse> renderErrorResponse(ServerRequest request) {
        Throwable error = getError(request);
        if (error instanceof AccountNotFoundException) {
            return ServerResponse.status(HttpStatus.NOT_FOUND)
                .bodyValue(Map.of("error", error.getMessage()));
        }
        return ServerResponse.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .bodyValue(Map.of("error", "Internal server error"));
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

WebClient configuration:

```java
@Configuration
public class WebClientConfig {
    @Bean
    public WebClient externalServiceWebClient(
            @Value("${external-service.base-url}") String baseUrl) {
        return WebClient.builder()
            .baseUrl(baseUrl)
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .build();
    }
}
```

`application.yml`:

```yaml
spring:
  application:
    name: my-reactive-service
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/mydb
    username: ${DB_USER}
    password: ${DB_PASSWORD}
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
ports           → model (+ reactor-core for Mono/Flux)
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
lombok = "1.18.36"
reactor-test = "3.7.6"
mapstruct = "1.5.5.Final"

[libraries]
spring-boot-webflux = { module = "org.springframework.boot:spring-boot-starter-webflux" }
spring-boot-r2dbc = { module = "org.springframework.boot:spring-boot-starter-data-r2dbc" }
spring-boot-test = { module = "org.springframework.boot:spring-boot-starter-test" }
reactor-test = { module = "io.projectreactor:reactor-test" }
lombok = { module = "org.projectlombok:lombok" }
r2dbc-postgresql = { module = "org.postgresql:r2dbc-postgresql" }
mapstruct = { module = "org.mapstruct:mapstruct", version.ref = "mapstruct" }
mapstruct-processor = { module = "org.mapstruct:mapstruct-processor", version.ref = "mapstruct" }

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version = "1.1.7" }
```

### build.gradle (root)

```groovy
plugins {
    alias(libs.plugins.spring.boot) apply false
    alias(libs.plugins.spring.dependency.management) apply false
    id 'java'
}

java {
    toolchain { languageVersion = JavaLanguageVersion.of(21) }
}

subprojects {
    apply plugin: 'java'
    java { toolchain { languageVersion = JavaLanguageVersion.of(21) } }
    dependencies {
        compileOnly libs.lombok
        annotationProcessor libs.lombok
        testCompileOnly libs.lombok
        testAnnotationProcessor libs.lombok
        implementation libs.mapstruct
        annotationProcessor libs.mapstruct.processor
    }
}
```

### settings.gradle

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

// Client library mocks — ALWAYS included
include ''
project(':').projectDir = file('')
```

### Module build.gradle examples

**domain/ports:**
```groovy
dependencies {
    implementation project(':domain:model')
    implementation 'io.projectreactor:reactor-core'
}
```

**domain/usecases:**
```groovy
dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation 'io.projectreactor:reactor-core'
}
```

**infrastructure/driven-adapters/r2dbc-persistence:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':infrastructure:helpers')
    implementation project(':')
    implementation libs.spring.boot.r2dbc
    runtimeOnly libs.r2dbc.postgresql
}
```

**infrastructure/driven-adapters/{name}-client-api:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':infrastructure:helpers')
    implementation project(':')
    implementation libs.spring.boot.webflux
}
```

**infrastructure/entry-points/reactive-web:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'
bootJar { enabled = false }
jar { enabled = true }

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:helpers')
    implementation project(':')
    implementation libs.spring.boot.webflux
}
```

**application/app-service:**
```groovy
apply plugin: 'org.springframework.boot'
apply plugin: 'io.spring.dependency-management'

dependencies {
    implementation project(':domain:model')
    implementation project(':domain:ports')
    implementation project(':domain:usecases')
    implementation project(':infrastructure:driven-adapters:r2dbc-persistence')
    implementation project(':infrastructure:driven-adapters:{name}-client-api')
    implementation project(':infrastructure:entry-points:reactive-web')
    implementation project(':infrastructure:helpers')
    implementation project(':')

    implementation libs.spring.boot.webflux
    implementation libs.spring.boot.r2dbc
    runtimeOnly libs.r2dbc.postgresql
    testImplementation libs.spring.boot.test
    testImplementation libs.reactor.test
}
```

---


## Enforced Constraints

These constraints apply to ALL reactive projects:

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
