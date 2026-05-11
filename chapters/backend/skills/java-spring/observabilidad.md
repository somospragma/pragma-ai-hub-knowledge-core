---
id: backend-skill-java-spring-observabilidad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Observabilidad — Java Spring

## Propósito

Documentar la configuración de Spring Actuator, custom health indicators, métricas con Micrometer y tracing con OpenTelemetry para microservicios Java Spring Boot.

---

## 1. Spring Boot Actuator

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
# Deployment de Kubernetes
livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 5
```

### Seguridad de Endpoints

- Solo exponer el endpoint `health`. **NO** exponer `env`, `beans`, `configprops` en producción.
- Si el servicio tiene autenticación, los endpoints de health DEBEN excluirse de los filtros de auth.

---

## 2. Custom Health Indicators

### Health Indicator para Base de Datos

```java
@Component
public class DatabaseHealthIndicator implements HealthIndicator {

    private final DataSource dataSource;

    public DatabaseHealthIndicator(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public Health health() {
        try (Connection conn = dataSource.getConnection()) {
            if (conn.isValid(5)) {
                return Health.up()
                    .withDetail("database", "PostgreSQL")
                    .withDetail("validationTime", "< 5s")
                    .build();
            }
        } catch (SQLException e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .build();
        }
        return Health.down().build();
    }
}
```

### Health Indicator para Servicio Externo

```java
@Component
public class ExternalServiceHealthIndicator implements HealthIndicator {

    private final RestClient restClient;

    public ExternalServiceHealthIndicator(@Value("${external.health-url}") String healthUrl) {
        this.restClient = RestClient.builder().baseUrl(healthUrl).build();
    }

    @Override
    public Health health() {
        try {
            restClient.get()
                .uri("/health")
                .retrieve()
                .toBodilessEntity();
            return Health.up()
                .withDetail("service", "external-api")
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("service", "external-api")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

### Health Indicator para Kafka

```java
@Component
@ConditionalOnProperty(name = "kafka.enabled", havingValue = "true")
public class KafkaHealthIndicator implements HealthIndicator {

    private final KafkaTemplate<String, String> kafkaTemplate;

    @Override
    public Health health() {
        try {
            kafkaTemplate.getProducerFactory().createProducer().metrics();
            return Health.up().withDetail("kafka", "connected").build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("kafka", "disconnected")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

---

## 3. Métricas con Micrometer

### Dependencia (incluida en actuator)

Spring Boot 4 incluye Micrometer 1.16 automáticamente con `spring-boot-starter-actuator`.

### Métricas Personalizadas

```java
@Component
@RequiredArgsConstructor
public class OrderMetrics {

    private final MeterRegistry meterRegistry;
    private final AtomicInteger activeOrders = new AtomicInteger(0);

    @PostConstruct
    public void init() {
        // Gauge: valor actual
        Gauge.builder("orders.active", activeOrders, AtomicInteger::get)
            .description("Número de órdenes activas")
            .tag("service", "order-service")
            .register(meterRegistry);
    }

    // Counter: incrementar en cada orden creada
    public void orderCreated(String type) {
        Counter.builder("orders.created.total")
            .description("Total de órdenes creadas")
            .tag("type", type)
            .register(meterRegistry)
            .increment();
        activeOrders.incrementAndGet();
    }

    // Timer: medir duración de procesamiento
    public void recordProcessingTime(String operation, Duration duration) {
        Timer.builder("orders.processing.duration")
            .description("Duración del procesamiento de órdenes")
            .tag("operation", operation)
            .register(meterRegistry)
            .record(duration);
    }

    // Distribution Summary: medir valores
    public void recordOrderAmount(double amount) {
        DistributionSummary.builder("orders.amount")
            .description("Monto de las órdenes")
            .baseUnit("USD")
            .register(meterRegistry)
            .record(amount);
    }
}
```

### Uso en UseCase

```java
@RequiredArgsConstructor
public class CreateOrderUseCase {
    private final IOrderGateway orderGateway;
    private final OrderMetrics metrics;

    public Order execute(OrderRequest request) {
        Instant start = Instant.now();
        try {
            Order order = orderGateway.save(buildOrder(request));
            metrics.orderCreated(request.type());
            metrics.recordOrderAmount(request.amount().doubleValue());
            return order;
        } finally {
            metrics.recordProcessingTime("create",
                Duration.between(start, Instant.now()));
        }
    }
}
```

### Configuración de Exportación

```yaml
management:
  metrics:
    export:
      prometheus:
        enabled: true
    tags:
      application: ${spring.application.name}
      environment: ${ENVIRONMENT:dev}
```

---

## 4. Tracing con OpenTelemetry

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

### Propagación de Contexto

Spring Boot 4 propaga automáticamente el trace context entre servicios cuando se usa `RestClient` o `@HttpExchange`. No se requiere configuración adicional.

### Spans Personalizados

```java
@Component
@RequiredArgsConstructor
public class PaymentAdapter implements IPaymentGateway {

    private final RestClient restClient;
    private final Tracer tracer;

    @Override
    public PaymentResult process(PaymentRequest request) {
        Span span = tracer.nextSpan().name("payment.process").start();
        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            span.tag("payment.id", request.getId());
            span.tag("payment.amount", request.getAmount().toString());

            PaymentResult result = restClient.post()
                .uri("/payments")
                .body(request)
                .retrieve()
                .body(PaymentResult.class);

            span.tag("payment.status", result.getStatus());
            return result;
        } catch (Exception e) {
            span.error(e);
            throw e;
        } finally {
            span.end();
        }
    }
}
```

---

## 5. Logging Estructurado

### Configuración

```yaml
logging:
  level:
    root: INFO
    com.pragma: DEBUG
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n"
```

### MDC para Correlación

```java
@Component
public class CorrelationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
            HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String traceId = request.getHeader("X-Request-ID");
        if (traceId == null) {
            traceId = UUID.randomUUID().toString();
        }
        MDC.put("traceId", traceId);
        response.setHeader("X-Request-ID", traceId);
        try {
            chain.doFilter(request, response);
        } finally {
            MDC.clear();
        }
    }
}
```

---

## Reglas Importantes

- Solo exponer endpoint `health` en producción.
- Implementar health indicators para cada dependencia crítica (DB, servicios externos, Kafka).
- Usar métricas para monitorear KPIs de negocio (órdenes creadas, montos, tiempos).
- Configurar sampling de tracing según el ambiente (100% dev, 10% prod).
- Incluir `traceId` en todos los logs para correlación.
- No exponer información sensible en health details en producción.
- Excluir endpoints de actuator de filtros de autenticación.
