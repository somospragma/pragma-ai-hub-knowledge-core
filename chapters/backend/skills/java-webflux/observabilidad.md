---
id: backend-skill-java-webflux-observabilidad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Observabilidad — Java WebFlux (Reactivo)

## Propósito

Documentar la configuración de Spring Actuator para WebFlux, custom health indicators reactivos, métricas con Micrometer + Reactor, tracing con OpenTelemetry y context propagation reactivo.

---

## 1. Spring Boot Actuator (WebFlux)

### Dependencia

```toml
# gradle/libs.versions.toml
[libraries]
boot-starter-actuator = { module = "org.springframework.boot:spring-boot-starter-actuator" }
```

```groovy
// application/app-service/build.gradle
dependencies {
    implementation libs.boot.starter.actuator
}
```

### Configuración (application.yml)

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health
  endpoint:
    health:
      probes:
        enabled: true
      show-details: never    # never en producción, always en dev
  health:
    readinessstate:
      enabled: true
    livenessstate:
      enabled: true
```

### Probes de Kubernetes

```yaml
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
```

### Seguridad de Endpoints

Excluir endpoints de health de los filtros de seguridad:

```java
@Bean
public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    return http
        .authorizeExchange(exchanges -> exchanges
            .pathMatchers("/actuator/health/**").permitAll()
            .anyExchange().authenticated()
        )
        .build();
}
```

---

## 2. Custom Health Indicators (Reactivos)

En WebFlux se usa `ReactiveHealthIndicator` en lugar de `HealthIndicator`:

### Health Indicator para R2DBC

```java
@Component
public class R2dbcHealthIndicator implements ReactiveHealthIndicator {

    private final ConnectionFactory connectionFactory;

    public R2dbcHealthIndicator(ConnectionFactory connectionFactory) {
        this.connectionFactory = connectionFactory;
    }

    @Override
    public Mono<Health> health() {
        return Mono.from(connectionFactory.create())
            .flatMap(connection ->
                Mono.from(connection.createStatement("SELECT 1").execute())
                    .flatMap(result -> Mono.from(result.getRowsUpdated()))
                    .doFinally(signal -> connection.close())
                    .map(rows -> Health.up()
                        .withDetail("database", "R2DBC PostgreSQL")
                        .withDetail("validation", "SELECT 1 OK")
                        .build())
            )
            .onErrorResume(e -> Mono.just(
                Health.down()
                    .withDetail("error", e.getMessage())
                    .build()
            ))
            .timeout(Duration.ofSeconds(5),
                Mono.just(Health.down().withDetail("error", "Timeout").build()));
    }
}
```

### Health Indicator para Servicio Externo (WebClient)

```java
@Component
public class ExternalServiceHealthIndicator implements ReactiveHealthIndicator {

    private final WebClient webClient;

    public ExternalServiceHealthIndicator(
            @Value("${external.health-url}") String healthUrl) {
        this.webClient = WebClient.builder().baseUrl(healthUrl).build();
    }

    @Override
    public Mono<Health> health() {
        return webClient.get()
            .uri("/health")
            .retrieve()
            .toBodilessEntity()
            .map(response -> Health.up()
                .withDetail("service", "external-api")
                .withDetail("status", response.getStatusCode().value())
                .build())
            .onErrorResume(e -> Mono.just(
                Health.down()
                    .withDetail("service", "external-api")
                    .withDetail("error", e.getMessage())
                    .build()
            ))
            .timeout(Duration.ofSeconds(3),
                Mono.just(Health.down().withDetail("error", "Timeout").build()));
    }
}
```

### Health Indicator para Kafka (Reactor Kafka)

```java
@Component
@ConditionalOnProperty(name = "kafka.enabled", havingValue = "true")
public class KafkaHealthIndicator implements ReactiveHealthIndicator {

    private final KafkaSender<String, String> kafkaSender;

    public KafkaHealthIndicator(KafkaSender<String, String> kafkaSender) {
        this.kafkaSender = kafkaSender;
    }

    @Override
    public Mono<Health> health() {
        return Mono.fromCallable(() -> {
                kafkaSender.doOnProducer(producer -> {
                    producer.metrics();
                    return true;
                }).block(Duration.ofSeconds(2));
                return Health.up().withDetail("kafka", "connected").build();
            })
            .subscribeOn(Schedulers.boundedElastic())
            .onErrorResume(e -> Mono.just(
                Health.down()
                    .withDetail("kafka", "disconnected")
                    .withDetail("error", e.getMessage())
                    .build()
            ));
    }
}
```

---

## 3. Métricas con Micrometer + Reactor

### Métricas Personalizadas

```java
@Component
@RequiredArgsConstructor
public class OrderMetrics {

    private final MeterRegistry meterRegistry;
    private final AtomicInteger activeOrders = new AtomicInteger(0);

    @PostConstruct
    public void init() {
        Gauge.builder("orders.active", activeOrders, AtomicInteger::get)
            .description("Número de órdenes activas")
            .tag("service", "order-service")
            .register(meterRegistry);
    }

    public void orderCreated(String type) {
        Counter.builder("orders.created.total")
            .description("Total de órdenes creadas")
            .tag("type", type)
            .register(meterRegistry)
            .increment();
        activeOrders.incrementAndGet();
    }

    public void recordProcessingTime(String operation, Duration duration) {
        Timer.builder("orders.processing.duration")
            .description("Duración del procesamiento de órdenes")
            .tag("operation", operation)
            .register(meterRegistry)
            .record(duration);
    }

    public void recordOrderAmount(double amount) {
        DistributionSummary.builder("orders.amount")
            .description("Monto de las órdenes")
            .baseUnit("USD")
            .register(meterRegistry)
            .record(amount);
    }
}
```

### Métricas Automáticas de Reactor (Reactor Metrics)

Activar métricas automáticas de Reactor para monitorear suscripciones, errores y latencia:

```java
@Configuration
public class ReactorMetricsConfig {

    @PostConstruct
    public void enableReactorMetrics() {
        Hooks.onOperatorDebug(); // Solo en dev
    }

    @Bean
    public MeterRegistryCustomizer<MeterRegistry> reactorMetrics() {
        return registry -> {
            // Habilitar métricas de Reactor Netty
            // Se activan automáticamente con spring-boot-starter-actuator
        };
    }
}
```

### Instrumentación de Pipelines Reactivos

```java
@RequiredArgsConstructor
public class CreateOrderUseCase {
    private final IOrderGateway orderGateway;
    private final OrderMetrics metrics;

    public Mono<Order> execute(OrderRequest request) {
        return Mono.defer(() -> {
            Instant start = Instant.now();
            return orderGateway.save(buildOrder(request))
                .doOnSuccess(order -> {
                    metrics.orderCreated(request.type());
                    metrics.recordOrderAmount(request.amount().doubleValue());
                    metrics.recordProcessingTime("create",
                        Duration.between(start, Instant.now()));
                })
                .doOnError(e -> {
                    Counter.builder("orders.errors.total")
                        .tag("operation", "create")
                        .tag("error", e.getClass().getSimpleName())
                        .register(metrics.getMeterRegistry())
                        .increment();
                });
        });
    }
}
```

### Métricas de WebClient

```java
@Configuration
public class WebClientMetricsConfig {

    @Bean
    public WebClient metricsWebClient(
            @Value("${external.base-url}") String baseUrl,
            MeterRegistry meterRegistry) {
        return WebClient.builder()
            .baseUrl(baseUrl)
            .filter(MetricsWebClientFilterFunction.builder(meterRegistry)
                .metricsName("http.client.requests")
                .build())
            .build();
    }
}
```

---

## 4. Tracing con OpenTelemetry (Context Propagation Reactivo)

### Dependencia

```groovy
implementation libs.boot.starter.opentelemetry
```

### Configuración

```yaml
management:
  otlp:
    tracing:
      endpoint: http://otel-collector:4318/v1/traces
    metrics:
      export:
        endpoint: http://otel-collector:4318/v1/metrics
  tracing:
    sampling:
      probability: 1.0  # 100% en dev, reducir en prod (0.1 = 10%)
```

### Context Propagation con Reactor Context

En WebFlux, el trace context se propaga automáticamente a través del Reactor Context (no ThreadLocal). Spring Boot 4 + Micrometer manejan esto automáticamente.

Para propagación manual:

```java
@Component
@RequiredArgsConstructor
public class TracedPaymentAdapter implements IPaymentGateway {
    private final WebClient webClient;
    private final ObservationRegistry observationRegistry;

    @Override
    public Mono<PaymentResult> process(PaymentRequest request) {
        return Mono.deferContextual(ctx -> {
            Observation observation = Observation.createNotStarted("payment.process", observationRegistry)
                .lowCardinalityKeyValue("payment.type", request.getType())
                .start();

            return webClient.post()
                .uri("/payments")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(PaymentResult.class)
                .doOnSuccess(result ->
                    observation.lowCardinalityKeyValue("payment.status", result.getStatus()))
                .doOnError(observation::error)
                .doFinally(signal -> observation.stop());
        });
    }
}
```

### Spans Personalizados con Reactor

```java
@Component
@RequiredArgsConstructor
public class ObservedOrderUseCase {
    private final IOrderGateway orderGateway;
    private final ObservationRegistry observationRegistry;

    public Mono<Order> execute(CreateOrderRequest request) {
        return Mono.deferContextual(ctx -> {
            Observation observation = Observation.createNotStarted("order.create", observationRegistry)
                .lowCardinalityKeyValue("order.type", request.type())
                .highCardinalityKeyValue("customer.id", request.customerId())
                .start();

            return orderGateway.save(buildOrder(request))
                .doOnSuccess(order ->
                    observation.lowCardinalityKeyValue("order.status", order.getStatus()))
                .doOnError(observation::error)
                .doFinally(signal -> observation.stop());
        });
    }
}
```

---

## 5. Logging Estructurado (Reactivo)

### Configuración

```yaml
logging:
  level:
    root: INFO
    com.pragma: DEBUG
    reactor.netty: INFO
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n"
```

### Propagación de TraceId con Reactor Context

En WebFlux NO funciona MDC directamente (es ThreadLocal). Se usa Reactor Context + hook:

```java
@Component
public class CorrelationWebFilter implements WebFilter {

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        String traceId = exchange.getRequest().getHeaders().getFirst("X-Request-ID");
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

### Logging con Context en Operadores

```java
@Component
public class LoggingHelper {

    public static <T> Mono<T> logWithContext(Mono<T> mono, String message) {
        return mono.doOnEach(signal -> {
            if (!signal.isOnComplete() && !signal.isOnError()) {
                String traceId = signal.getContextView().getOrDefault("traceId", "unknown");
                MDC.put("traceId", traceId);
                log.info("[{}] {}", traceId, message);
                MDC.remove("traceId");
            }
        });
    }
}
```

### Activar Context Propagation Automático (Micrometer)

```java
@Configuration
public class ContextPropagationConfig {

    @PostConstruct
    public void enableAutomaticContextPropagation() {
        // Spring Boot 4 + Micrometer activa esto automáticamente
        // con la dependencia de context-propagation
        Hooks.enableAutomaticContextPropagation();
    }
}
```

---

## 6. Configuración de Exportación de Métricas

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
    tags:
      application: ${spring.application.name}
      environment: ${ENVIRONMENT:dev}
    distribution:
      percentiles-histogram:
        http.server.requests: true
      slo:
        http.server.requests: 100ms, 500ms, 1s, 5s
```

---

## Reglas Importantes

- Solo exponer endpoint `health` en producción.
- Implementar `ReactiveHealthIndicator` (NO `HealthIndicator`) para cada dependencia crítica.
- Usar métricas para monitorear KPIs de negocio (órdenes creadas, montos, tiempos).
- Configurar sampling de tracing según el ambiente (100% dev, 10% prod).
- Usar `Reactor Context` para propagación de traceId (NO MDC directamente).
- Activar `Hooks.enableAutomaticContextPropagation()` para propagación automática.
- No exponer información sensible en health details en producción.
- Excluir endpoints de actuator de filtros de autenticación.
- Instrumentar pipelines reactivos con `doOnSuccess`/`doOnError` para métricas.
- Usar `Observation` API de Micrometer para spans personalizados.
- **NUNCA** usar `.block()` en health indicators — usar `ReactiveHealthIndicator`.
