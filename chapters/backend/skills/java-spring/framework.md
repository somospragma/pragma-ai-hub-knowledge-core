---
id: backend-skill-java-spring-framework
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Framework: Spring Boot 4 — Java Spring

## Propósito

Documentar las features de Spring Boot 4 (basado en Spring Framework 7), configuración recomendada, template de application.yml, profiles y actuator.

---

## 1. Stack Base

| Componente | Versión |
|-----------|---------|
| Spring Boot | 4.0.3 |
| Spring Framework | 7.0 |
| Java | 21 (mínimo) |
| Jakarta EE | 11 |
| Hibernate | 7.1 |
| Jackson | 3.0 |
| Micrometer | 1.16 |
| HikariCP | 7.0 |
| Gradle | 9.x (mínimo 8.14) |

---

## 2. Null-Safety con JSpecify

Spring Framework 7 adopta JSpecify como estándar de null-safety. Cada paquete debe tener un `package-info.java`:

```java
@NullMarked
package com.pragma.myservice.model;

import org.jspecify.annotations.NullMarked;
```

Usar `@Nullable` solo donde un valor puede legítimamente ser null:

```java
public interface ICustomerGateway {
    Customer save(Customer entity);           // nunca retorna null
    @Nullable Customer findById(String id);   // puede no existir
    List<Customer> findAll();                  // nunca retorna null
}
```

---

## 3. Versionamiento Nativo de APIs

```java
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

Uso en controllers:

```java
@PostMapping(version = "1.0")
public ResponseEntity<ResponseV1> createV1(@Valid @RequestBody RequestV1 request) { }

@PostMapping(version = "2.0")
public ResponseEntity<ResponseV2> createV2(@Valid @RequestBody RequestV2 request) { }
```

---

## 4. HTTP Clients Declarativos (@HttpExchange)

Reemplaza la configuración manual de `RestClient` para consumir APIs externas:

```java
@HttpExchange
public interface OtherServiceClient {
    @GetExchange("/api/v1/resources/{id}")
    ExternalResourceResponse getResource(@PathVariable String id);

    @PostExchange("/api/v1/resources")
    ExternalResourceResponse createResource(@RequestBody CreateResourceRequest request);
}
```

Registro:

```java
@Configuration
@ImportHttpServices(group = "other-service", types = OtherServiceClient.class)
public class HttpClientsConfig {}
```

Configuración:

```yaml
spring:
  http:
    serviceclient:
      other-service:
        base-url: https://api.other-service.com
```

---

## 5. Resiliencia Nativa

Spring Framework 7 incorpora resiliencia directamente. No se necesita `spring-retry` externo.

```java
@SpringBootApplication
@EnableResilientMethods
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}
```

### @Retryable

```java
@Retryable(
    maxAttempts = 4,
    includes = ExternalServiceException.class,
    delay = 1000,
    multiplier = 2
)
public void sendNotification(String recipient, String message) {
    gateway.send(recipient, message);
}
```

### @ConcurrencyLimit

```java
@ConcurrencyLimit(5)
public void processPayment(String paymentId) {
    gateway.process(paymentId);
}
```

### RetryTemplate Programático

```java
RetryPolicy retryPolicy = RetryPolicy.builder()
    .maxAttempts(5)
    .delay(Duration.ofMillis(2000))
    .multiplier(1.5)
    .maxDelay(Duration.ofMillis(10000))
    .includes(ResourceUnavailableException.class)
    .build();

RetryTemplate retryTemplate = new RetryTemplate(retryPolicy);

Driver driver = retryTemplate.execute(() -> findAvailableDriver(orderId));
```

---

## 6. Observabilidad con OpenTelemetry

```groovy
implementation libs.boot.starter.opentelemetry
```

```yaml
management:
  otlp:
    tracing:
      endpoint: http://otel-collector:4318/v1/traces
    metrics:
      export:
        endpoint: http://otel-collector:4318/v1/metrics
```

---

## 7. Testing con RestTestClient

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureRestTestClient
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

---

## 8. Template de application.yml

```yaml
spring:
  application:
    name: ${SERVICE_NAME:my-service}
  datasource:
    hikari:
      jdbc-url: ${DB_URL:jdbc:postgresql://localhost:5432/mydb}
      username: ${DB_USER}
      password: ${DB_PASSWORD}
      maximum-pool-size: 20
      minimum-idle: 5
      connection-timeout: 30000
  jpa:
    hibernate:
      ddl-auto: validate
    open-in-view: false

server:
  port: ${SERVER_PORT:8080}
  shutdown: graceful

management:
  endpoints:
    web:
      exposure:
        include: health
  endpoint:
    health:
      probes:
        enabled: true
      show-details: never
  health:
    readinessstate:
      enabled: true
    livenessstate:
      enabled: true

logging:
  level:
    root: INFO
    com.pragma: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"
```

---

## 9. Profiles

```yaml
# application-dev.yml
spring:
  jpa:
    show-sql: true
management:
  endpoint:
    health:
      show-details: always

# application-prod.yml
spring:
  jpa:
    show-sql: false
logging:
  level:
    root: WARN
    com.pragma: INFO
```

Activación:

```bash
java -jar app.jar --spring.profiles.active=prod
```

---

## 10. Cambios Importantes desde Spring Boot 3.x

| Spring Boot 3 | Spring Boot 4 |
|--------------|---------------|
| `@MockBean` / `@SpyBean` | `@MockitoBean` / `@MockitoSpyBean` |
| `RestTemplate` (nuevos clientes) | `@HttpExchange` + `@ImportHttpServices` o `RestClient` |
| `spring-boot-starter-web` | `spring-boot-starter-webmvc` |
| `spring-boot-starter-aop` | `spring-boot-starter-aspectj` |
| `spring-boot-starter-json` | `spring-boot-starter-jackson` |
| `spring-retry` (externo) | `@Retryable` nativo + `@ConcurrencyLimit` |
| `org.springframework.lang.Nullable` | `org.jspecify.annotations.Nullable` |
| `@SpringBootTest` + auto MockMVC | Agregar `@AutoConfigureMockMvc` explícitamente |
| `TestRestTemplate` | `RestTestClient` con `@AutoConfigureRestTestClient` |
| Undertow como servidor | Removido (usar Tomcat o Jetty) |

---

## Reglas Importantes

- Versiones centralizadas en `gradle/libs.versions.toml`.
- `build.gradle` usa `alias(libs.plugins.spring.boot)`, no versión hardcodeada.
- Gradle wrapper apunta a Gradle 9.x.
- Cada paquete tiene `package-info.java` con `@NullMarked`.
- `RestTemplate` NO se usa para nuevos clientes HTTP.
- `spring-retry` externo NO se usa (resiliencia es nativa).
- DTOs como Java Records.
- `@EnableResilientMethods` activado si se usan retries.
