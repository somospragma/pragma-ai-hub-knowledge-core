---
id: backend-skill-java-webflux-resiliencia
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Resiliencia — Java WebFlux (Reactivo)

## Propósito

Implementar patrones de resiliencia en microservicios reactivos: circuit breaker con decoradores reactivos (`transformDeferred`), retry reactivo con `retryWhen`, timeout con `Mono.timeout()`, bulkhead reactivo y rate limiting usando Resilience4j con Project Reactor.

---

## 1. Circuit Breaker (Reactivo)

### Estados del Circuit Breaker

```
CLOSED (Normal) → failures > threshold → OPEN (Fallando)
OPEN → timeout → HALF-OPEN (Probando)
HALF-OPEN → success → CLOSED
HALF-OPEN → failure → OPEN
```

### Dependencias

```groovy
implementation 'io.github.resilience4j:resilience4j-reactor:2.2.0'
implementation 'io.github.resilience4j:resilience4j-circuitbreaker:2.2.0'
implementation 'io.github.resilience4j:resilience4j-timelimiter:2.2.0'
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

### Uso con `transformDeferred` (Patrón Reactivo)

En WebFlux se usa `transformDeferred` en lugar de anotaciones `@CircuitBreaker`:

```java
@Component
@RequiredArgsConstructor
public class PaymentAdapter implements IPaymentGateway {
    private final WebClient webClient;
    private final CircuitBreakerRegistry circuitBreakerRegistry;

    @Override
    public Mono<PaymentResponse> processPayment(PaymentRequest request) {
        CircuitBreaker circuitBreaker = circuitBreakerRegistry.circuitBreaker("paymentService");

        return webClient.post()
            .uri("/payments")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PaymentResponse.class)
            .transformDeferred(CircuitBreakerOperator.of(circuitBreaker))
            .onErrorResume(CallNotPermittedException.class,
                e -> fallback(request, e));
    }

    private Mono<PaymentResponse> fallback(PaymentRequest request, Throwable t) {
        log.warn("Fallback activado para pago: {}", request.getId(), t);
        return Mono.just(PaymentResponse.pending("Servicio de pagos no disponible"));
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

## 2. Retry Reactivo

### Fórmula de Backoff Exponencial

```
delay = min(maxDelay, initialDelay * (multiplier ^ attempt))
jitter = delay * jitterFactor * random(0, 1)
finalDelay = delay + jitter
```

### Retry con `retryWhen` de Reactor

```java
@Component
@RequiredArgsConstructor
public class ExternalServiceAdapter implements IExternalServiceGateway {
    private final WebClient webClient;

    @Override
    public Mono<ExternalResource> fetchById(String id) {
        return webClient.get()
            .uri("/api/v1/resources/{id}", id)
            .retrieve()
            .bodyToMono(ExternalResourceDto.class)
            .map(mapper::toModel)
            .retryWhen(Retry.backoff(3, Duration.ofMillis(500))
                .maxBackoff(Duration.ofSeconds(5))
                .jitter(0.5)
                .filter(this::isRetryable)
                .doBeforeRetry(signal ->
                    log.warn("Reintentando llamada, intento {}",
                        signal.totalRetries() + 1))
            );
    }

    private boolean isRetryable(Throwable throwable) {
        if (throwable instanceof WebClientResponseException ex) {
            return ex.getStatusCode().is5xxServerError()
                || ex.getStatusCode().value() == 429;
        }
        return throwable instanceof IOException
            || throwable instanceof TimeoutException;
    }
}
```

### Retry con Resilience4j `transformDeferred`

```java
@Component
@RequiredArgsConstructor
public class ResilientAdapter implements IServiceGateway {
    private final WebClient webClient;
    private final RetryRegistry retryRegistry;

    @Override
    public Mono<ServiceResponse> call(ServiceRequest request) {
        io.github.resilience4j.retry.Retry retry = retryRegistry.retry("externalService");

        return webClient.post()
            .uri("/api/resource")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ServiceResponse.class)
            .transformDeferred(RetryOperator.of(retry));
    }
}
```

### Excepciones Retryables vs No-Retryables

| Reintentar | NO reintentar |
|-----------|--------------|
| IOException (errores de red) | ValidationException (400) |
| TimeoutException | UnauthorizedException (401) |
| ServiceUnavailableException (503) | ForbiddenException (403) |
| TooManyRequestsException (429) | NotFoundException (404) |
| ConnectionResetException | ConflictException (409) |

---

## 3. Timeout Reactivo

### Timeout con `Mono.timeout()`

```java
@Component
@RequiredArgsConstructor
public class PaymentAdapter implements IPaymentGateway {
    private final WebClient webClient;

    @Override
    public Mono<PaymentResponse> processPayment(PaymentRequest request) {
        return webClient.post()
            .uri("/payments")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PaymentResponse.class)
            .timeout(Duration.ofSeconds(5))
            .onErrorResume(TimeoutException.class,
                e -> Mono.error(new ServiceTimeoutException("Payment service timeout")));
    }
}
```

### Timeout con Resilience4j TimeLimiter

```java
@Component
@RequiredArgsConstructor
public class TimeLimitedAdapter implements IServiceGateway {
    private final WebClient webClient;
    private final TimeLimiterRegistry timeLimiterRegistry;

    @Override
    public Mono<ServiceResponse> call(ServiceRequest request) {
        TimeLimiter timeLimiter = timeLimiterRegistry.timeLimiter("externalService");

        return webClient.post()
            .uri("/api/resource")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ServiceResponse.class)
            .transformDeferred(TimeLimiterOperator.of(timeLimiter));
    }
}
```

### Configuración de Timeout en WebClient

```java
@Configuration
public class WebClientConfig {
    @Bean
    public WebClient externalWebClient(
            @Value("${external.base-url}") String baseUrl) {
        HttpClient httpClient = HttpClient.create()
            .responseTimeout(Duration.ofSeconds(10))
            .option(ChannelOption.CONNECT_TIMEOUT_MILLIS, 5000);

        return WebClient.builder()
            .baseUrl(baseUrl)
            .clientConnector(new ReactorClientHttpConnector(httpClient))
            .build();
    }
}
```

---

## 4. Bulkhead Reactivo

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

### Uso con `transformDeferred`

```java
@Component
@RequiredArgsConstructor
public class PaymentAdapter implements IPaymentGateway {
    private final WebClient webClient;
    private final BulkheadRegistry bulkheadRegistry;

    @Override
    public Mono<PaymentResult> processPayment(PaymentRequest request) {
        Bulkhead bulkhead = bulkheadRegistry.bulkhead("payment");

        return webClient.post()
            .uri("/payments")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PaymentResult.class)
            .transformDeferred(BulkheadOperator.of(bulkhead))
            .onErrorResume(BulkheadFullException.class,
                e -> {
                    log.warn("Bulkhead de pagos lleno, rechazando solicitud");
                    return Mono.just(PaymentResult.rejected("Servicio de pagos saturado"));
                });
    }
}
```

---

## 5. Rate Limiting Reactivo

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

### Uso con `transformDeferred`

```java
@Component
@RequiredArgsConstructor
public class RateLimitedHandler {
    private final RateLimiterRegistry rateLimiterRegistry;
    private final GetAccountUseCase getAccountUseCase;

    public Mono<ServerResponse> findById(ServerRequest request) {
        RateLimiter rateLimiter = rateLimiterRegistry.rateLimiter("api");
        String id = request.pathVariable("id");

        return getAccountUseCase.execute(id)
            .transformDeferred(RateLimiterOperator.of(rateLimiter))
            .flatMap(account -> ServerResponse.ok().bodyValue(account))
            .onErrorResume(RequestNotPermitted.class,
                e -> ServerResponse.status(HttpStatus.TOO_MANY_REQUESTS)
                    .header("Retry-After", "30")
                    .bodyValue(Map.of("error", "Rate limit exceeded")));
    }
}
```

---

## 6. Orden de Decoradores (Importante)

```
CircuitBreaker → TimeLimiter → Retry → Bulkhead → Operación
```

El CircuitBreaker envuelve todo para evitar reintentos cuando el servicio está caído.

### Combinación Completa con `transformDeferred`

```java
@Component
@RequiredArgsConstructor
public class ResilientExternalService implements IExternalServiceGateway {
    private final WebClient webClient;
    private final CircuitBreakerRegistry cbRegistry;
    private final RetryRegistry retryRegistry;
    private final BulkheadRegistry bulkheadRegistry;
    private final TimeLimiterRegistry timeLimiterRegistry;

    @Override
    public Mono<ExternalResponse> call(ExternalRequest request) {
        CircuitBreaker cb = cbRegistry.circuitBreaker("external");
        io.github.resilience4j.retry.Retry retry = retryRegistry.retry("external");
        Bulkhead bulkhead = bulkheadRegistry.bulkhead("external");
        TimeLimiter timeLimiter = timeLimiterRegistry.timeLimiter("external");

        return webClient.post()
            .uri("/api/resource")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(ExternalResponse.class)
            .transformDeferred(BulkheadOperator.of(bulkhead))
            .transformDeferred(RetryOperator.of(retry))
            .transformDeferred(TimeLimiterOperator.of(timeLimiter))
            .transformDeferred(CircuitBreakerOperator.of(cb))
            .onErrorResume(CallNotPermittedException.class,
                e -> Mono.just(ExternalResponse.defaultResponse()));
    }
}
```

---

## Reglas Importantes

- Usar `transformDeferred` con operadores de Resilience4j (NO anotaciones `@CircuitBreaker`).
- Usar `retryWhen(Retry.backoff(...))` de Reactor para reintentos simples.
- Siempre usar backoff exponencial con jitter para evitar thundering herd.
- Limitar reintentos a 3-5 intentos máximo.
- Configurar timeouts en TODAS las llamadas externas (`Mono.timeout()` o `TimeLimiter`).
- Diseñar operaciones idempotentes para retry seguro.
- Solo reintentar errores transitorios (5xx, timeout, IOException).
- Combinar con circuit breaker para protección completa.
- Loguear cada intento de retry para debugging.
- Implementar fallbacks significativos para el negocio.
- Retornar 429 con header `Retry-After` cuando se excede el rate limit.
- **NUNCA** usar `.block()` en lógica de resiliencia.
