---
id: backend-skill-java-webflux-framework
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Framework: Spring Boot 4 + WebFlux — Java Reactivo

## Propósito

Documentar las features de Spring Boot 4 con WebFlux: Netty como servidor, configuración reactiva, functional endpoints, Reactor Context, Project Reactor y las diferencias clave con el stack imperativo.

---

## 1. Stack Base

| Componente | Versión |
|-----------|---------|
| Spring Boot | 4.0.3 |
| Spring Framework | 7.0 |
| Spring WebFlux | 7.0 |
| Java | 21 (mínimo) |
| Project Reactor | 3.7.x |
| Netty | 4.1.x (servidor por defecto) |
| Jakarta EE | 11 |
| Jackson | 3.0 |
| Micrometer | 1.16 |
| R2DBC | 1.0 |
| Gradle | 9.x (mínimo 8.14) |

---

## 2. Netty como Servidor

WebFlux usa Netty por defecto (event-loop, non-blocking). **NO** Tomcat.

### Configuración de Netty

```yaml
server:
  port: ${SERVER_PORT:8080}
  netty:
    connection-timeout: 30s
    idle-timeout: 60s
    max-initial-line-length: 8192
    max-header-size: 16384
```

### Tuning de Event Loop

```java
@Configuration
public class NettyConfig {

    @Bean
    public NettyReactiveWebServerFactory nettyFactory() {
        NettyReactiveWebServerFactory factory = new NettyReactiveWebServerFactory();
        factory.addServerCustomizers(httpServer -> httpServer
            .accessLog(true)
            .wiretap(false)
            .metrics(true, Function.identity())
        );
        return factory;
    }
}
```

---

## 3. Project Reactor — Conceptos Clave

### Mono y Flux

```java
// Mono: 0 o 1 elemento
Mono<Account> account = accountGateway.findById("acc-123");

// Flux: 0 a N elementos
Flux<Account> accounts = accountGateway.findAll();

// Transformaciones
Mono<AccountResponse> response = account
    .map(mapper::toResponse)
    .switchIfEmpty(Mono.error(new AccountNotFoundException("Not found")));

// Composición
Mono<Order> order = customerGateway.findById(customerId)
    .flatMap(customer -> orderGateway.createForCustomer(customer));
```

### Operadores Comunes

| Operador | Uso |
|----------|-----|
| `map` | Transformación síncrona 1:1 |
| `flatMap` | Transformación asíncrona (retorna Mono/Flux) |
| `switchIfEmpty` | Valor alternativo cuando está vacío |
| `defaultIfEmpty` | Valor por defecto cuando está vacío |
| `zip` | Combinar múltiples Monos en paralelo |
| `concatMap` | flatMap con orden garantizado |
| `collectList` | Flux → Mono<List> |
| `filter` | Filtrar elementos |
| `doOnNext` | Side-effect sin modificar el flujo |
| `onErrorResume` | Fallback en caso de error |
| `retryWhen` | Reintentos con estrategia |
| `timeout` | Timeout para la operación |

### Ejemplo de Composición Compleja

```java
@RequiredArgsConstructor
public class CreateOrderUseCase {
    private final ICustomerGateway customerGateway;
    private final IInventoryGateway inventoryGateway;
    private final IOrderGateway orderGateway;

    public Mono<Order> execute(CreateOrderRequest request) {
        return customerGateway.findById(request.customerId())
            .switchIfEmpty(Mono.error(new CustomerNotFoundException(request.customerId())))
            .flatMap(customer ->
                inventoryGateway.checkAvailability(request.items())
                    .filter(available -> available)
                    .switchIfEmpty(Mono.error(new InsufficientStockException()))
                    .thenReturn(customer)
            )
            .flatMap(customer -> {
                Order order = Order.builder()
                    .customerId(customer.getId())
                    .items(request.items())
                    .status(OrderStatus.PENDING)
                    .createdAt(Instant.now())
                    .build();
                return orderGateway.save(order);
            });
    }
}
```

---

## 4. Functional Endpoints (Router + Handler)

### Patrón Obligatorio

```java
// Router: define rutas
@Configuration
@RequiredArgsConstructor
public class OrderRouter {
    private final OrderHandler handler;

    @Bean
    public RouterFunction<ServerResponse> orderRoutes() {
        return RouterFunctions.route()
            .path("/api/v1/orders", builder -> builder
                .GET("", handler::findAll)
                .GET("/{id}", handler::findById)
                .POST("", handler::create)
                .PUT("/{id}", handler::update)
                .DELETE("/{id}", handler::delete)
            )
            .build();
    }
}

// Handler: procesa requests
@Component
@RequiredArgsConstructor
public class OrderHandler {
    private final CreateOrderUseCase createOrderUseCase;

    public Mono<ServerResponse> create(ServerRequest request) {
        return request.bodyToMono(CreateOrderRequest.class)
            .flatMap(createOrderUseCase::execute)
            .flatMap(order -> ServerResponse.status(HttpStatus.CREATED).bodyValue(order));
    }
}
```

---

## 5. Reactor Context

Reactor Context reemplaza `ThreadLocal` (que no funciona en reactive). Se usa para propagar datos transversales (traceId, userId, tenantId).

### Escribir en el Context

```java
@Component
public class CorrelationWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String traceId = exchange.getRequest().getHeaders()
            .getFirst("X-Request-ID");
        if (traceId == null) {
            traceId = UUID.randomUUID().toString();
        }
        exchange.getResponse().getHeaders().add("X-Request-ID", traceId);

        String finalTraceId = traceId;
        return chain.filter(exchange)
            .contextWrite(Context.of("traceId", finalTraceId));
    }
}
```

### Leer del Context

```java
@Component
public class AuditAdapter implements IAuditGateway {

    @Override
    public Mono<Void> logAccess(String resource) {
        return Mono.deferContextual(ctx -> {
            String traceId = ctx.getOrDefault("traceId", "unknown");
            log.info("[{}] Acceso a recurso: {}", traceId, resource);
            return Mono.empty();
        });
    }
}
```

### Context en Use Cases

```java
@RequiredArgsConstructor
public class GetAccountUseCase {
    private final IAccountGateway accountGateway;
    private final IAuditGateway auditGateway;

    public Mono<Account> execute(String id) {
        return accountGateway.findById(id)
            .switchIfEmpty(Mono.error(new AccountNotFoundException(id)))
            .flatMap(account ->
                auditGateway.logAccess("account:" + id)
                    .thenReturn(account)
            );
    }
}
```

---

## 6. Configuración Reactiva

### WebClient Configuration

```java
@Configuration
public class WebClientConfig {

    @Bean
    public WebClient externalServiceWebClient(
            @Value("${external-service.base-url}") String baseUrl) {
        HttpClient httpClient = HttpClient.create()
            .responseTimeout(Duration.ofSeconds(10))
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000);

        return WebClient.builder()
            .baseUrl(baseUrl)
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .filter(ExchangeFilterFunction.ofRequestProcessor(request -> {
                log.debug("Request: {} {}", request.method(), request.url());
                return Mono.just(request);
            }))
            .build();
    }
}
```

### R2DBC Configuration

```java
@Configuration
@EnableR2dbcRepositories
public class R2dbcConfig extends AbstractR2dbcConfiguration {

    @Override
    public ConnectionFactory connectionFactory() {
        return ConnectionFactories.get(ConnectionFactoryOptions.builder()
            .option(DRIVER, "postgresql")
            .option(HOST, "localhost")
            .option(PORT, 5432)
            .option(DATABASE, "mydb")
            .option(USER, System.getenv("DB_USER"))
            .option(PASSWORD, System.getenv("DB_PASSWORD"))
            .build());
    }
}
```

---

## 7. Template de application.yml

```yaml
spring:
  application:
    name: ${SERVICE_NAME:my-reactive-service}
  r2dbc:
    url: ${DB_URL:r2dbc:postgresql://localhost:5432/mydb}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
    pool:
      initial-size: 5
      max-size: 20
      max-idle-time: 30m

server:
  port: ${SERVER_PORT:8080}
  shutdown: graceful
  netty:
    connection-timeout: 30s

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
    reactor.netty: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n"

external-service:
  base-url: ${EXTERNAL_SERVICE_URL:https://api.external.com}
```

---

## 8. Profiles

```yaml
# application-dev.yml
spring:
  r2dbc:
    pool:
      max-size: 5
management:
  endpoint:
    health:
      show-details: always
logging:
  level:
    reactor.netty: DEBUG

# application-prod.yml
spring:
  r2dbc:
    pool:
      max-size: 50
logging:
  level:
    root: WARN
    com.pragma: INFO
    reactor.netty: WARN
management:
  tracing:
    sampling:
      probability: 0.1
```

---

## 9. Diferencias Clave con Spring MVC

| Spring MVC (Imperativo) | Spring WebFlux (Reactivo) |
|------------------------|--------------------------|
| `@RestController` | `RouterFunction` + `HandlerFunction` |
| `@RestControllerAdvice` | `AbstractErrorWebExceptionHandler` |
| `SecurityFilterChain` | `SecurityWebFilterChain` |
| `OncePerRequestFilter` | `WebFilter` |
| `SecurityContextHolder` | `ReactiveSecurityContextHolder` |
| `ThreadLocal` / MDC | `Reactor Context` |
| `RestClient` / `RestTemplate` | `WebClient` |
| JPA / `JpaRepository` | R2DBC / `ReactiveCrudRepository` |
| `MockMvc` | `WebTestClient` |
| `@WebMvcTest` | `@WebFluxTest` |
| Tomcat (thread-per-request) | Netty (event-loop) |
| `ResponseEntity<T>` | `Mono<ServerResponse>` |
| `@Transactional` | `TransactionalOperator` |
| `CompletableFuture` | `Mono<T>` / `Flux<T>` |

---

## 10. Schedulers de Reactor

| Scheduler | Uso |
|-----------|-----|
| `Schedulers.parallel()` | CPU-bound, NO permite bloqueo |
| `Schedulers.boundedElastic()` | I/O bloqueante (JDBC, file I/O) |
| `Schedulers.single()` | Un solo thread, tareas secuenciales |
| `Schedulers.immediate()` | Thread actual (default) |

```java
// Envolver código bloqueante
Mono.fromCallable(() -> blockingOperation())
    .subscribeOn(Schedulers.boundedElastic());

// Procesamiento CPU-intensive
Flux.range(1, 1000)
    .publishOn(Schedulers.parallel())
    .map(this::cpuIntensiveTransform);
```

---

## Reglas Importantes

- Servidor es Netty, **NO** Tomcat.
- Usar `RouterFunction` + `HandlerFunction`, **NO** `@RestController`.
- Usar `WebFilter`, **NO** `OncePerRequestFilter`.
- Usar `Reactor Context` para datos transversales, **NO** `ThreadLocal`.
- Usar `WebClient`, **NO** `RestClient` ni `RestTemplate`.
- Usar R2DBC, **NO** JPA/Hibernate.
- Usar `Schedulers.boundedElastic()` para envolver código bloqueante.
- **NUNCA** bloquear en `Schedulers.parallel()` ni en el event loop de Netty.
- Versiones centralizadas en `gradle/libs.versions.toml`.
- DTOs como Java Records.
- `reactive=true` en `gradle.properties`.
