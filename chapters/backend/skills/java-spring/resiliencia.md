---
id: backend-skill-java-spring-resiliencia
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Resiliencia — Java Spring

## Propósito

Implementar patrones de resiliencia: circuit breaker, retry con backoff exponencial, timeouts explícitos, bulkhead pattern y rate limiting usando Resilience4j y las capacidades nativas de Spring Framework 7.

---

## 1. Circuit Breaker

### Estados del Circuit Breaker

```
CLOSED (Normal) → failures > threshold → OPEN (Fallando)
OPEN → timeout → HALF-OPEN (Probando)
HALF-OPEN → success → CLOSED
HALF-OPEN → failure → OPEN
```

### Dependencias

```groovy
implementation 'io.github.resilience4j:resilience4j-spring-boot3:2.2.0'
implementation 'org.springframework.boot:spring-boot-starter-aspectj'
```

### Configuración (application.yml)

```yaml
resilience4j:
  circuitbreaker:
    instances:
      paymentService:
        registerHealthIndicator: true
        slidingWindowSize: 10
        minimumNumberOfCalls: 5
        permittedNumberOfCallsInHalfOpenState: 3
        automaticTransitionFromOpenToHalfOpenEnabled: true
        waitDurationInOpenState: 30s
        failureRateThreshold: 50
        slowCallRateThreshold: 50
        slowCallDurationThreshold: 2s
        recordExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
        ignoreExceptions:
          - com.pragma.BusinessException
```

### Uso con Anotaciones

```java
@Service
@RequiredArgsConstructor
public class PaymentAdapter implements IPaymentGateway {
    private final RestClient restClient;

    @CircuitBreaker(name = "paymentService", fallbackMethod = "fallback")
    @Retry(name = "paymentService")
    @TimeLimiter(name = "paymentService")
    public PaymentResponse processPayment(PaymentRequest request) {
        return restClient.post()
            .uri("/payments")
            .body(request)
            .retrieve()
            .body(PaymentResponse.class);
    }

    private PaymentResponse fallback(PaymentRequest request, Throwable t) {
        log.warn("Fallback activado para pago: {}", request.getId(), t);
        return PaymentResponse.pending("Servicio de pagos no disponible");
    }
}
```

### Monitoreo de Eventos

```java
@Component
public class CircuitBreakerEventListener {
    @PostConstruct
    public void register(CircuitBreakerRegistry registry) {
        registry.getAllCircuitBreakers().forEach(cb ->
            cb.getEventPublisher()
                .onStateTransition(event ->
                    log.info("CB {} transición: {} → {}",
                        event.getCircuitBreakerName(),
                        event.getStateTransition().getFromState(),
                        event.getStateTransition().getToState()))
        );
    }
}
```

---

## 2. Retry con Backoff Exponencial

### Fórmula

```
delay = min(maxDelay, initialDelay * (multiplier ^ attempt))
jitter = delay * jitterFactor * random(-1, 1)
finalDelay = max(0, delay + jitter)
```

### Configuración

```yaml
resilience4j:
  retry:
    instances:
      externalService:
        maxAttempts: 3
        waitDuration: 500ms
        enableExponentialBackoff: true
        exponentialBackoffMultiplier: 2
        randomizedWaitFactor: 0.5
        retryExceptions:
          - java.io.IOException
          - java.util.concurrent.TimeoutException
        ignoreExceptions:
          - com.pragma.BusinessException
```

### Excepciones Retryables vs No-Retryables

| Reintentar | NO reintentar |
|-----------|--------------|
| IOException (errores de red) | ValidationException (400) |
| TimeoutException | UnauthorizedException (401) |
| ServiceUnavailableException (503) | ForbiddenException (403) |
| TooManyRequestsException (429) | NotFoundException (404) |
| ConnectionResetException | ConflictException (409) |

### Resiliencia Nativa Spring Framework 7

Spring Boot 4 incluye `@Retryable` nativo (sin dependencia externa):

```java
@SpringBootApplication
@EnableResilientMethods
public class MainApplication {
    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }
}

@Service
@RequiredArgsConstructor
public class NotificationService {
    private final INotificationGateway gateway;

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

---

## 3. Timeouts Explícitos

### Configuración

```yaml
resilience4j:
  timelimiter:
    instances:
      externalService:
        timeoutDuration: 5s
        cancelRunningFuture: true
```

### Timeout en RestClient

```java
@Component
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final RestClient restClient;

    public ExternalServiceAdapter(@Value("${external.base-url}") String baseUrl) {
        this.restClient = RestClient.builder()
            .baseUrl(baseUrl)
            .requestFactory(createRequestFactory())
            .build();
    }

    private ClientHttpRequestFactory createRequestFactory() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(5));
        factory.setReadTimeout(Duration.ofSeconds(10));
        return factory;
    }
}
```

---

## 4. Bulkhead Pattern

### Configuración

```yaml
resilience4j:
  bulkhead:
    instances:
      payment:
        maxConcurrentCalls: 10
        maxWaitDuration: 1s
      inventory:
        maxConcurrentCalls: 50
        maxWaitDuration: 100ms
```

### Uso

```java
@Service
public class OrderService {

    @Bulkhead(name = "payment", fallbackMethod = "paymentBulkheadFallback")
    public PaymentResult processPayment(PaymentRequest request) {
        return paymentGateway.process(request);
    }

    private PaymentResult paymentBulkheadFallback(PaymentRequest request, BulkheadFullException e) {
        log.warn("Bulkhead de pagos lleno, rechazando solicitud");
        return PaymentResult.rejected("Servicio de pagos saturado");
    }
}
```

### ConcurrencyLimit Nativo (Spring Framework 7)

```java
@Service
public class NotificationService {
    @ConcurrencyLimit(3)
    public void notifyRestaurant(Order order) {
        // Solo 3 notificaciones simultáneas
        sendWebhook(order);
    }
}
```

---

## 5. Rate Limiting

### Configuración

```yaml
resilience4j:
  ratelimiter:
    instances:
      api:
        limitForPeriod: 1000
        limitRefreshPeriod: 1s
        timeoutDuration: 0
```

### Rate Limiter Multi-Tenant

```java
@Service
public class MultiTenantRateLimiter {
    private final Map<String, RateLimiter> tenantLimiters = new ConcurrentHashMap<>();

    public void checkRateLimit(String tenantId, int limit) {
        RateLimiter limiter = tenantLimiters.computeIfAbsent(tenantId,
            id -> RateLimiter.of(id, RateLimiterConfig.custom()
                .limitRefreshPeriod(Duration.ofSeconds(1))
                .limitForPeriod(limit)
                .timeoutDuration(Duration.ZERO)
                .build()));

        if (!limiter.acquirePermission()) {
            throw new TooManyRequestsException(tenantId);
        }
    }
}
```

### Headers de Rate Limiting en Respuesta

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
Retry-After: 30
```

---

## Orden de Decoradores (Importante)

```
CircuitBreaker → TimeLimiter → Retry → Bulkhead → Operación
```

El CircuitBreaker envuelve todo para evitar reintentos cuando el servicio está caído.

### Combinación Completa

```java
@Service
@RequiredArgsConstructor
public class ResilientExternalService {
    private final RestClient restClient;

    @CircuitBreaker(name = "external", fallbackMethod = "fallback")
    @TimeLimiter(name = "external")
    @Retry(name = "external")
    @Bulkhead(name = "external")
    public ExternalResponse call(ExternalRequest request) {
        return restClient.post()
            .uri("/api/resource")
            .body(request)
            .retrieve()
            .body(ExternalResponse.class);
    }

    private ExternalResponse fallback(ExternalRequest request, Throwable t) {
        return ExternalResponse.defaultResponse();
    }
}
```

---

## Reglas Importantes

- Siempre usar backoff exponencial con jitter para evitar thundering herd.
- Limitar reintentos a 3-5 intentos máximo.
- Configurar timeouts en TODAS las llamadas externas.
- Diseñar operaciones idempotentes para retry seguro.
- Solo reintentar errores transitorios.
- Combinar con circuit breaker para protección.
- Loguear cada intento de retry para debugging.
- Implementar fallbacks significativos para el negocio.
- Retornar 429 con header `Retry-After` cuando se excede el rate limit.
