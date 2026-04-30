<!-- keywords: spring boot 4, spring framework 7, jspecify, null-safety, opentelemetry, declarative http client, gradle 9, java -->
# Reference: Spring Boot 4 with Spring Framework 7 — New Features and Configuration

## Purpose

After reading this reference, the developer or agent will know how to configure and apply the new features of Spring Boot 4 (based on Spring Framework 7) in the the organization's Java microservices. It covers null-safety with JSpecify, native API versioning, declarative HTTP clients, observability with OpenTelemetry, testing with RestTestClient, and Gradle 9 configuration.

## Scope of Application

Mandatory for all Java microservices in the the organization that use:
- Java 21 (minimum and current standard)
- Spring Boot 4.x (currently 4.0.3)
- Gradle as build tool (Maven is not used)
- Jakarta EE 11

Applies to both new projects (green field) and migrations of existing services from Spring Boot 3.x.

## Step by Step / Guidelines

### 1. Base project configuration (Gradle)

Spring Boot 4 supports Gradle 9. The project must use Gradle 9.x (or minimum 8.14).

```properties
# gradle/wrapper/gradle-wrapper.properties
distributionUrl=https\://services.gradle.org/distributions/gradle-9.0-bin.zip
```

Versions are centralized in `gradle/libs.versions.toml` (see reference `02-archetypes/version-catalog.md`):

```toml
# gradle/libs.versions.toml
[versions]
spring-boot = "4.0.3"
spring-dependency-management = "1.1.7"
lombok = "1.18.36"
jspecify = "1.0.0"

[plugins]
spring-boot = { id = "org.springframework.boot", version.ref = "spring-boot" }
spring-dependency-management = { id = "io.spring.dependency-management", version.ref = "spring-dependency-management" }

[libraries]
lombok = { module = "org.projectlombok:lombok", version.ref = "lombok" }
jspecify = { module = "org.jspecify:jspecify", version.ref = "jspecify" }
```

```groovy
// Root build.gradle — uses version catalog aliases, NOT hardcoded versions
plugins {
    id 'java'
    alias(libs.plugins.spring.boot) apply false
    alias(libs.plugins.spring.dependency.management) apply false
}

java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(21)
    }
}

subprojects {
    apply plugin: 'java'

    java {
        toolchain {
            languageVersion = JavaLanguageVersion.of(21)
        }
    }

    dependencies {
        compileOnly libs.lombok
        annotationProcessor libs.lombok
        implementation libs.jspecify
    }
}
```

### 2. Null-Safety with JSpecify

Spring Framework 7 adopts JSpecify as the null-safety standard. The entire framework is annotated, and IDEs (IntelliJ 2025.3+) show warnings when potentially null values are passed to APIs that don't accept them.

**Rule:** Each project package must have a `package-info.java` with `@NullMarked`. JSpecify does NOT inherit to sub-packages, so it must be repeated in each one.

```java
// package-info.java — one per package
@NullMarked
package com.company.myservice.model;

import org.jspecify.annotations.NullMarked;
```

**Usage of `@Nullable`:** Only where a value can legitimately be null.

```java
// In a domain gateway
public interface MyEntityRepository {
    MyEntity save(MyEntity entity);           // never returns null
    @Nullable MyEntity findById(String id);   // may not exist
    List<MyEntity> findAll();                  // never returns null
}
```

```java
// Correct — no JSpecify warnings
@Bean
public CreateEntityUseCase createEntityUseCase(MyEntityRepository repository) {
    return new CreateEntityUseCase(repository);
}
```

**Dependency** (defined in `libs.versions.toml`):
```groovy
implementation libs.jspecify
```

### 3. Native API Versioning

Spring Framework 7 introduces the `version` attribute in `@RequestMapping` and derivatives (`@GetMapping`, `@PostMapping`, etc.). A versioning strategy is configured and used directly in controllers.

**Java configuration (recommended):**

```java
// config/WebConfig.java in app-service
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void configureApiVersioning(ApiVersionConfigurer configurer) {
        configurer
            .useRequestHeader("X-API-Version")
            .addSupportedVersions("1.0", "2.0")
            .setDefaultVersion("1.0");
    }
}
```

**Properties alternative:**
```yaml
spring:
  mvc:
    apiversion:
      use:
        header: X-API-Version
      supported: 1.0,2.0
      default: 1.0
```

**Usage in controllers (entry-points):**

```java
@RestController
@RequestMapping("/api/entities")
@RequiredArgsConstructor
public class MyController {

    private final CreateEntityUseCase createEntityUseCase;

    @PostMapping(version = "1.0")
    public ResponseEntity<MyResponse> createV1(@Valid @RequestBody MyRequest request) {
        // version 1
    }

    @PostMapping(version = "2.0")
    public ResponseEntity<MyResponseV2> createV2(@Valid @RequestBody MyRequestV2 request) {
        // version 2 with extended fields
    }
}
```

**Available strategies (choose ONE, do not mix):**

| Strategy | Configuration | Request example |
|----------|---------------|-----------------|
| Header | `useRequestHeader("X-API-Version")` | `X-API-Version: 2.0` |
| Path segment | `usePathSegment(1)` | `/api/v2/entities` |
| Query param | `useQueryParam("version")` | `?version=2.0` |
| Media type | `useMediaTypeParameter(MediaType.APPLICATION_JSON, "version")` | `Accept: application/json;version=2.0` |

**Custom parser (optional):** Allows accepting formats like `v1` or `v2` in addition to `1.0` or `2.0`:

```java
public class ApiVersionParser implements org.springframework.web.accept.ApiVersionParser {
    @Override
    public Comparable<?> parseVersion(String version) {
        if (version.startsWith("v") || version.startsWith("V")) {
            version = version.substring(1);
        }
        if (!version.contains(".")) {
            version = version + ".0";
        }
        return version;
    }
}
```

### 4. HTTP Service Clients with @HttpExchange

Spring Boot 4 auto-configures declarative HTTP clients based on `@HttpExchange` interfaces. Replaces manual `RestTemplate`/`WebClient` configuration in driven-adapters that consume external APIs.

**Define the client interface:**

```java
// In driven-adapters/rest-consumer/
@HttpExchange
public interface OtherServiceClient {

    @GetExchange("/api/v1/resources/{id}")
    ExternalResourceResponse getResource(@PathVariable String id);

    @PostExchange("/api/v1/resources")
    ExternalResourceResponse createResource(@RequestBody CreateResourceRequest request);
}
```

**Register with `@ImportHttpServices`:**

```java
// config/HttpClientsConfig.java in app-service
@Configuration
@ImportHttpServices(group = "other-service", types = OtherServiceClient.class)
public class HttpClientsConfig {
}
```

**Configure the base URL:**

```yaml
spring:
  http:
    serviceclient:
      other-service:
        base-url: https://api.other-service.com
```

**Advanced configuration (optional):**

```java
@Bean
RestClientHttpServiceGroupConfigurer groupConfigurer() {
    return groups -> groups
        .filterByName("other-service")
        .forEachClient((group, builder) ->
            builder.baseUrl("https://api.other-service.com"));
}
```

**The domain adapter delegates to the client:**

```java
@Component
@RequiredArgsConstructor
public class OtherServiceAdapter implements OtherServiceGateway {

    private final OtherServiceClient client;

    @Override
    public ExternalResource get(String id) {
        return OtherServiceMapper.toModel(client.getResource(id));
    }
}
```

### 5. Native observability with OpenTelemetry

Spring Boot 4 includes `spring-boot-starter-opentelemetry` which auto-configures the OpenTelemetry SDK for metrics and traces via OTLP. Integrates Micrometer 2 natively.

**Dependency** (defined in `libs.versions.toml`):
```groovy
implementation libs.boot.starter.opentelemetry
```

**Configuration:**
```yaml
management:
  otlp:
    tracing:
      endpoint: http://otel-collector:4318/v1/traces
    metrics:
      export:
        endpoint: http://otel-collector:4318/v1/metrics
```

### 6. Native resilience with @Retryable and @ConcurrencyLimit

Spring Framework 7 incorporates resilience directly into the core. The `spring-retry` project is now in maintenance mode. External dependencies for retry, backoff, or concurrency control are no longer needed.

**Activation:** Add `@EnableResilientMethods` to the configuration class or `MainApplication`. This enables both `@Retryable` and `@ConcurrencyLimit`.

```java
@SpringBootApplication(scanBasePackages = "{base.package}")
@EnableResilientMethods
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}
```

**@Retryable — Declarative retries with exponential backoff:**

Use on methods that call external services with transient failures (timeouts, unstable APIs, DB connections).

```java
@Service
@RequiredArgsConstructor
public class NotificationService {

    private final NotificationGateway gateway;

    @Retryable(
        maxAttempts = 4,
        includes = ExternalServiceException.class,
        delay = 1000,
        multiplier = 2
    )
    public void sendNotification(String recipient, String message) {
        gateway.send(recipient, message);
    }
}
```

| Attribute | What it does |
|-----------|-------------|
| `maxAttempts` | Total attempts (1 initial + N retries) |
| `includes` | Exceptions that trigger retry. Only transient ones. |
| `delay` | Initial wait time between retries (ms) |
| `multiplier` | Exponential backoff factor (1s → 2s → 4s) |

**RetryTemplate — Programmatic control for complex scenarios:**

When different policies per operation or observability listeners are needed.

```java
@Service
public class DriverAssignmentService {

    private final RetryTemplate retryTemplate;

    public DriverAssignmentService() {
        RetryPolicy retryPolicy = RetryPolicy.builder()
            .maxAttempts(5)
            .delay(Duration.ofMillis(2000))
            .multiplier(1.5)
            .maxDelay(Duration.ofMillis(10000))
            .includes(ResourceUnavailableException.class)
            .build();

        this.retryTemplate = new RetryTemplate(retryPolicy);
    }

    public Driver assign(String orderId) throws RetryException {
        return retryTemplate.execute(() -> {
            // logic that may fail transiently
            return findAvailableDriver(orderId);
        });
    }
}
```

**RetryListener — Retry observability:**

```java
@Component
public class MyRetryListener implements RetryListener {

    private static final Logger log = LoggerFactory.getLogger(MyRetryListener.class);

    @Override
    public void beforeRetry(RetryPolicy retryPolicy, Retryable<?> retryable) {
        log.info("Retrying operation: {}", retryable.getName());
    }

    @Override
    public void onRetrySuccess(RetryPolicy retryPolicy, Retryable<?> retryable, Object result) {
        log.info("Operation successful: {}", retryable.getName());
    }

    @Override
    public void onRetryFailure(RetryPolicy retryPolicy, Retryable<?> retryable, Throwable throwable) {
        log.error("Operation failed after retries: {} - {}", retryable.getName(), throwable.getMessage());
    }
}
```

**@ConcurrencyLimit — Resource protection against overload:**

Limits how many threads can execute a method simultaneously. Works equally with platform threads and virtual threads (Java 21+).

```java
@Service
public class RestaurantNotificationService {

    @ConcurrencyLimit(3)
    public void notifyRestaurant(Order order) {
        // Only 3 simultaneous notifications.
        // The rest waits for a permit to be released.
        sendWebhook(order);
    }
}
```

**`@Retryable` + `@ConcurrencyLimit` can be combined on the same method:**

```java
@Retryable(maxAttempts = 3, includes = TimeoutException.class, delay = 1000, multiplier = 2)
@ConcurrencyLimit(5)
public void processPayment(String paymentId) {
    // Maximum 5 concurrent + retry on timeout
    gateway.process(paymentId);
}
```

**When to use each:**

| Scenario | Use |
|----------|-----|
| Simple retries with backoff | `@Retryable` |
| Different policies per operation | `RetryTemplate` |
| Need for listeners/observability | `RetryTemplate` + `RetryListener` |
| Protect downstream service from overload | `@ConcurrencyLimit` |
| Reactive methods (Mono/Flux) | `@Retryable` (decorates reactive pipelines automatically) |

### 7. RestTestClient for testing

Spring Boot 4 introduces `RestTestClient` as a lighter and more fluent alternative for HTTP integration tests.

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class MyControllerIntegrationTest {

    @Autowired
    private RestTestClient restTestClient;

    @Test
    void shouldCreateEntity() {
        restTestClient.post()
            .uri("/api/entities")
            .header("X-API-Version", "1.0")
            .body(new MyRequest("name"))
            .exchange()
            .expectStatus().isCreated()
            .expectBody(MyResponse.class)
            .value(response -> assertThat(response.name()).isEqualTo("name"));
    }
}
```

With `@AutoConfigureMockMvc`, `RestTestClient` operates over `MockMvc`. With random or defined port, it points to the real server.

### 8. Key updated dependencies

| Dependency | Version in Spring Boot 4 |
|------------|--------------------------|
| Spring Framework | 7.0 |
| Hibernate | 7.1 |
| Jackson | 3.0 |
| Jakarta EE | 11 |
| Micrometer | 1.16 |
| OpenTelemetry | 1.54 |
| Mockito | 5.20 |
| TestContainers | 2.0 |
| HikariCP | 7.0 |
| Flyway | 11.11 |
| Kafka Client | 4.1 |

## ⚠️ Migration Warnings from Spring Boot 3.x

Spring Boot 4 removed everything that was deprecated in Spring Boot 3.x. If migrating an existing service, review these critical changes:

### Removed or relocated APIs and classes

| What was used in Spring Boot 3 | What happened in Spring Boot 4 | Replacement |
|--------------------------------|--------------------------------|-------------|
| `@MockBean` / `@SpyBean` | Deprecated (will be removed soon) | `@MockitoBean` / `@MockitoSpyBean` |
| `@MockBean` in shared `@Configuration` | No longer works in `@Configuration` classes | `@MockitoBean(types = {X.class})` in the test class |
| `RestTemplate` (for new clients) | Still exists but not recommended | `@HttpExchange` + `@ImportHttpServices` or `RestClient` |
| `TestRestTemplate` | Requires explicit `@AutoConfigureTestRestTemplate` | `RestTestClient` with `@AutoConfigureRestTestClient` |
| `spring-boot-starter-web` | Deprecated (renamed) | `spring-boot-starter-webmvc` |
| `spring-boot-starter-aop` | Deprecated (renamed) | `spring-boot-starter-aspectj` |
| `spring-boot-starter-json` | Removed | `spring-boot-starter-jackson` |
| `spring-boot-starter-oauth2-*` | Deprecated (renamed) | `spring-boot-starter-security-oauth2-*` |
| `spring-retry` (external dependency) | No dependency management | Native resilience: `@Retryable`, `@ConcurrencyLimit` |
| `org.springframework.lang.Nullable` | Doesn't work in Actuator endpoints | `org.jspecify.annotations.Nullable` |
| `@SpringBootTest` + auto MockMVC | No longer auto-configured | Add `@AutoConfigureMockMvc` explicitly |
| `@SpringBootTest` + WebClient/TestRestTemplate | No longer auto-configured | Add `@AutoConfigureRestTestClient` or `@AutoConfigureTestRestTemplate` |
| `JsonObjectSerializer` | Renamed | `ObjectValueSerializer` |
| `JsonValueDeserializer` | Renamed | `ObjectValueDeserializer` |
| `Jackson2ObjectMapperBuilderCustomizer` | Renamed | `JsonMapperBuilderCustomizer` |
| `@JsonComponent` / `@JsonMixin` | Renamed | `@JacksonComponent` / `@JacksonMixin` |
| `HttpMessageConverters` custom bean | Deprecated | `ClientHttpMessageConvertersCustomizer` / `ServerHttpMessageConvertersCustomizer` |
| `@EntityScan` (old import) | Package moved | `org.springframework.boot.persistence.autoconfigure.EntityScan` |
| `spring.dao.exceptiontranslation.enabled` | Removed | `spring.persistence.exceptiontranslation.enabled` |
| `BootstrapRegistry` (old package) | Moved | `org.springframework.boot.bootstrap.BootstrapRegistry` |
| `EnvironmentPostProcessor` (old package) | Moved | `org.springframework.boot.EnvironmentPostProcessor` |
| `MockitoTestExecutionListener` | Removed | `MockitoExtension` from Mockito |
| Undertow as embedded server | Removed (not compatible with Servlet 6.1) | Tomcat or Jetty |

### Jackson 2 → Jackson 3

Jackson 3 is the default in Spring Boot 4. Main changes:
- Group IDs change from `com.fasterxml.jackson` to `tools.jackson` (except `jackson-annotations`).
- Java packages change accordingly.
- Properties `spring.jackson.read.*` and `spring.jackson.write.*` move to `spring.jackson.json.read.*` and `spring.jackson.json.write.*`.
- If temporary compatibility with Jackson 2 is needed: add `spring-boot-jackson2` and use `spring.jackson.use-jackson2-defaults=true`. This is temporary and will be removed in future versions.

### Starter modularization

Spring Boot 4 splits large JARs into small modules. Impact:
- Dependencies that previously came transitively now require an explicit starter.
- Example: Flyway now needs `spring-boot-starter-flyway` (previously the Flyway dependency was enough).
- Each technology has a separate test starter: `spring-boot-starter-<tech>-test`.
- `@WithMockUser` now requires `spring-boot-starter-security-test`.

**Quick migration:** Use `spring-boot-starter-classic` and `spring-boot-starter-test-classic` as an intermediate step. These replicate the Spring Boot 3 classpath. Migrate gradually and then remove them.

### Hibernate and persistence

- `hibernate-jpamodelgen` → replaced by `hibernate-processor`.
- `hibernate-proxool` and `hibernate-vibur` are no longer published.
- MongoDB properties: `spring.data.mongodb.*` → many move to `spring.mongodb.*`.


## Verification Checklist

- [ ] Versions centralized in `gradle/libs.versions.toml` (not hardcoded in `build.gradle`).
- [ ] `build.gradle` uses `alias(libs.plugins.spring.boot)`, not `version '4.0.3'`.
- [ ] Gradle wrapper points to Gradle 9.x (or minimum 8.14).
- [ ] Maven is not used anywhere in the project.
- [ ] Each package has `package-info.java` with `@NullMarked`.
- [ ] `@Nullable` used only where a value can legitimately be null.
- [ ] `libs.jspecify` dependency included in the TOML and referenced in `build.gradle`.
- [ ] If API versioning is used: `WebConfig` with `ApiVersionConfigurer` or equivalent properties.
- [ ] Controllers use `version = "x.x"` in mapping annotations.
- [ ] Driven-adapters consuming external APIs use `@HttpExchange` + `@ImportHttpServices`.
- [ ] `RestTemplate` is not used for new HTTP clients (use `@HttpExchange` or `RestClient`).
- [ ] If retries are used: `@EnableResilientMethods` activated in configuration.
- [ ] `@Retryable` used only for transient failures (not for validation or logic errors).
- [ ] `@ConcurrencyLimit` applied on methods calling downstream services sensitive to overload.
- [ ] External `spring-retry` dependency is not used (resilience is native in Spring Framework 7).
- [ ] Observability configured with `spring-boot-starter-opentelemetry` if applicable.
- [ ] Integration tests use `RestTestClient`.
- [ ] Request/response DTOs as Java Records.
- [ ] Project compiles without JSpecify warnings in the IDE.

## Tools and Resources

