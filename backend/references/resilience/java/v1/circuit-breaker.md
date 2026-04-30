<!-- keywords: circuit breaker, resilience4j, cascading failure, graceful degradation, fault tolerance, java -->
# Circuit Breaker Patterns — Java Implementation

## Purpose

Implement the Circuit Breaker pattern in Java applications with Resilience4j, protecting services against cascading failures and enabling graceful degradation.

## Scope of Application

- When implementing calls to external services in Spring Boot
- When configuring circuit breakers with Resilience4j
- When implementing fallbacks for unavailable services
- When designing resilient systems against cascading failures

## Main content

### Circuit Breaker States

```
┌─────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER STATES                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│    ┌──────────┐    failures > threshold   ┌──────────┐     │
│    │  CLOSED  │──────────────────────────▶│   OPEN   │     │
│    │ (Normal) │                           │ (Failing)│     │
│    └────▲─────┘                           └────┬─────┘     │
│         │                                      │            │
│         │ success                     timeout  │            │
│         │                                      ▼            │
│         │                              ┌──────────┐        │
│         └──────────────────────────────│HALF-OPEN │        │
│                                        │ (Testing)│        │
│                                        └──────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### State descriptions

| State | Description | Behavior |
|--------|-------------|----------------|
| CLOSED | Normal state | All calls pass through to the service |
| OPEN | Circuit open | Calls fail immediately (fallback) |
| HALF-OPEN | Recovery test | Allows limited test calls |

### Configuration parameters

| Parameter | Description | Typical value |
|-----------|-------------|--------------|
| failureRateThreshold | % of failures to open | 50% |
| slowCallRateThreshold | % of slow calls | 50% |
| slowCallDurationThreshold | Latency threshold | 2s |
| waitDurationInOpenState | Time in OPEN state | 30s |
| permittedCallsInHalfOpen | Test calls | 3-5 |
| slidingWindowSize | Window size | 10-100 |
| minimumNumberOfCalls | Minimum to evaluate | 5-10 |

### Exceptions to consider

```
┌─────────────────────────────────────────────────────────────┐
│  Exceptions that SHOULD trigger the circuit breaker:        │
│  ├── IOException (network errors)                           │
│  ├── TimeoutException (timeouts)                            │
│  ├── ServiceUnavailableException (503)                      │
│  └── ConnectionRefusedException                             │
├─────────────────────────────────────────────────────────────┤
│  Exceptions that SHOULD NOT trigger the circuit breaker:    │
│  ├── ValidationException (client errors)                    │
│  ├── NotFoundException (404)                                │
│  └── BusinessException (business errors)                    │
└─────────────────────────────────────────────────────────────┘
```

### Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'io.github.resilience4j:resilience4j-spring-boot3:2.2.0'
    implementation 'io.github.resilience4j:resilience4j-reactor:2.2.0'
    implementation 'org.springframework.boot:spring-boot-starter-aop'
}
```

```xml
<!-- pom.xml -->
<dependency>
    <groupId>io.github.resilience4j</groupId>
    <artifactId>resilience4j-spring-boot3</artifactId>
    <version>2.2.0</version>
</dependency>
```

### Circuit Breaker Configuration

```java
@Configuration
public class CircuitBreakerConfig {
    
    @Bean
    public CircuitBreakerRegistry circuitBreakerRegistry() {
        io.github.resilience4j.circuitbreaker.CircuitBreakerConfig config = 
            io.github.resilience4j.circuitbreaker.CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .slowCallRateThreshold(50)
                .slowCallDurationThreshold(Duration.ofSeconds(2))
                .waitDurationInOpenState(Duration.ofSeconds(30))
                .permittedNumberOfCallsInHalfOpenState(3)
                .slidingWindowType(SlidingWindowType.COUNT_BASED)
                .slidingWindowSize(10)
                .minimumNumberOfCalls(5)
                .recordExceptions(IOException.class, TimeoutException.class)
                .ignoreExceptions(BusinessException.class)
                .build();
        
        return CircuitBreakerRegistry.of(config);
    }
    
    @Bean
    public CircuitBreaker paymentServiceCircuitBreaker(CircuitBreakerRegistry registry) {
        return registry.circuitBreaker("paymentService");
    }
}
```

### Reactive Circuit Breaker Service

```java
@Service
public class PaymentService {
    
    private final WebClient webClient;
    private final CircuitBreaker circuitBreaker;
    
    public PaymentService(WebClient webClient, CircuitBreaker circuitBreaker) {
        this.webClient = webClient;
        this.circuitBreaker = circuitBreaker;
    }
    
    public Mono<PaymentResponse> processPayment(PaymentRequest request) {
        return webClient.post()
            .uri("/payments")
            .bodyValue(request)
            .retrieve()
            .bodyToMono(PaymentResponse.class)
            .transformDeferred(CircuitBreakerOperator.of(circuitBreaker))
            .onErrorResume(CallNotPermittedException.class, e -> 
                Mono.just(PaymentResponse.fallback("Circuit breaker open")))
            .onErrorResume(e -> 
                Mono.just(PaymentResponse.fallback("Service unavailable")));
    }
}
```

### Usage with Annotations

```java
@Service
public class ExternalApiService {
    
    private final RestTemplate restTemplate;
    
    @CircuitBreaker(name = "externalApi", fallbackMethod = "fallback")
    @Retry(name = "externalApi")
    @TimeLimiter(name = "externalApi")
    public CompletableFuture<ApiResponse> callExternalApi(ApiRequest request) {
        return CompletableFuture.supplyAsync(() -> 
            restTemplate.postForObject("/api", request, ApiResponse.class));
    }
    
    public CompletableFuture<ApiResponse> fallback(ApiRequest request, Throwable t) {
        log.warn("Fallback triggered for request: {}", request, t);
        return CompletableFuture.completedFuture(ApiResponse.defaultResponse());
    }
}
```

### Event Monitoring

```java
@Component
public class CircuitBreakerEventListener {
    
    private static final Logger log = LoggerFactory.getLogger(CircuitBreakerEventListener.class);
    
    @PostConstruct
    public void registerEventListeners(CircuitBreakerRegistry registry) {
        registry.getAllCircuitBreakers().forEach(cb -> {
            cb.getEventPublisher()
                .onStateTransition(event -> 
                    log.info("Circuit breaker {} transitioned from {} to {}",
                        event.getCircuitBreakerName(),
                        event.getStateTransition().getFromState(),
                        event.getStateTransition().getToState()))
                .onFailureRateExceeded(event ->
                    log.warn("Circuit breaker {} failure rate exceeded: {}%",
                        event.getCircuitBreakerName(),
                        event.getFailureRate()))
                .onSlowCallRateExceeded(event ->
                    log.warn("Circuit breaker {} slow call rate exceeded: {}%",
                        event.getCircuitBreakerName(),
                        event.getSlowCallRate()));
        });
    }
}
```

### YAML Configuration

```yaml
# application.yml
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
          - com.example.BusinessException
```

## Important Rules

- Configure thresholds based on service SLAs
- Implement meaningful business fallbacks
- Monitor circuit breaker state transitions
- Do not use circuit breaker for validation or business errors
- Combine with retry for transient errors
- Use `CircuitBreakerOperator` for reactive flows
- Register listeners for transition monitoring
- Combine with `@Retry` and `@TimeLimiter` for complete resilience

## Example

```java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    
    private final PaymentService paymentService;
    
    @PostMapping
    public Mono<OrderResponse> createOrder(@RequestBody OrderRequest request) {
        return paymentService.processPayment(request.getPayment())
            .map(payment -> OrderResponse.success(payment))
            .onErrorReturn(OrderResponse.pending("Payment processing delayed"));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
