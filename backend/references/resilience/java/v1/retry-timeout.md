<!-- keywords: retry, timeout, exponential backoff, jitter, idempotency, resilience4j, spring retry, java -->
# Retry and Timeout Patterns — Java Implementation

## Purpose

Define and implement the standard patterns for retries with exponential backoff, jitter, timeouts, and idempotency in Java applications with Resilience4j and Spring Retry.

## Scope of Application

- When implementing calls to external services
- When configuring resilient HTTP clients
- When designing idempotent operations
- When handling transient network failures
- When integrating with AWS services

## Main content

### Backoff Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    Backoff Strategies                            │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Constant      │   Exponential   │   Exponential + Jitter      │
│   1s, 1s, 1s    │   1s, 2s, 4s    │   1s±0.5, 2s±1, 4s±2       │
│   (Do not use)  │   (Basic)       │   (Recommended)             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Exponential backoff with jitter formula

```
delay = min(maxDelay, initialDelay * (multiplier ^ attempt))
jitter = delay * jitterFactor * random(-1, 1)
finalDelay = max(0, delay + jitter)
```

### Configuration parameters

| Parameter | Description | Typical value |
|-----------|-------------|--------------|
| maxAttempts | Maximum number of attempts | 3-5 |
| initialDelay | Initial delay | 500ms-1s |
| maxDelay | Maximum delay | 10s-30s |
| multiplier | Multiplication factor | 2.0 |
| jitterFactor | Randomness factor | 0.5 |
| timeout | Timeout per operation | 5s-30s |

### Retryable exceptions

```
┌─────────────────────────────────────────────────────────────────┐
│  Exceptions that SHOULD be retried:                              │
│  ├── IOException (transient network errors)                     │
│  ├── TimeoutException (timeouts)                                │
│  ├── ServiceUnavailableException (503)                          │
│  ├── TooManyRequestsException (429)                             │
│  └── ConnectionResetException                                   │
├─────────────────────────────────────────────────────────────────┤
│  Exceptions that SHOULD NOT be retried:                          │
│  ├── ValidationException (400)                                  │
│  ├── UnauthorizedException (401)                                │
│  ├── ForbiddenException (403)                                   │
│  ├── NotFoundException (404)                                    │
│  └── ConflictException (409)                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Resilience decorator order

```
┌─────────────────────────────────────────────────────────────────┐
│  Recommended order (outer to inner):                            │
│                                                                  │
│  CircuitBreaker → TimeLimiter → Retry → Bulkhead → Operation   │
│                                                                  │
│  The CircuitBreaker wraps everything to avoid retries           │
│  when the service is down.                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Idempotency

For retries to be safe, operations must be idempotent:

```
┌─────────────────────────────────────────────────────────────────┐
│  Idempotency strategies:                                        │
│                                      
│  1. Idempotency Key: Unique header per operation                │
│  2. Deduplication: Store results by key                         │
│  3. Naturally idempotent operations: GET, PUT, DELETE           │
│  4. Transaction tokens: For financial operations                │
└─────────────────────────────────────────────────────────────────┘
```

### Dependencies

```groovy
// build.gradle
dependencies {
    implementation 'io.github.resilience4j:resilience4j-spring-boot3:2.2.0'
    implementation 'io.github.resilience4j:resilience4j-reactor:2.2.0'
    implementation 'org.springframework.retry:spring-retry:2.0.4'
    implementation 'org.springframework.boot:spring-boot-starter-aop'
}
```

### Resilience4j Configuration

```java
@Configuration
public class RetryConfig {
    
    @Bean
    public RetryRegistry retryRegistry() {
        io.github.resilience4j.retry.RetryConfig defaultConfig = 
            io.github.resilience4j.retry.RetryConfig.custom()
                .maxAttempts(3)
                .waitDuration(Duration.ofMillis(500))
                .enableExponentialBackoff()
                .exponentialBackoffMultiplier(2.0)
                .randomizedWaitFactor(0.5) // Jitter
                .retryOnException(this::isRetryable)
                .retryOnResult(response -> response == null)
                .ignoreExceptions(BusinessException.class)
                .build();
        
        return RetryRegistry.of(defaultConfig);
    }
    
    private boolean isRetryable(Throwable throwable) {
        return throwable instanceof IOException
            || throwable instanceof TimeoutException
            || throwable instanceof ServiceUnavailableException
            || (throwable instanceof HttpClientErrorException ex 
                && ex.getStatusCode().is5xxServerError());
    }
}

@Configuration
public class TimeoutConfig {
    
    @Bean
    public TimeLimiterRegistry timeLimiterRegistry() {
        TimeLimiterConfig config = TimeLimiterConfig.custom()
            .timeoutDuration(Duration.ofSeconds(5))
            .cancelRunningFuture(true)
            .build();
        
        return TimeLimiterRegistry.of(config);
    }
}
```

### Service with Retry

```java
@Service
public class RetryableService {
    
    private final Retry retry;
    private final ExternalServiceClient client;
    
    public RetryableService(RetryRegistry retryRegistry, ExternalServiceClient client) {
        this.retry = retryRegistry.retry("externalService");
        this.client = client;
    }
    
    public Mono<Response> callWithRetry(Request request) {
        return Mono.fromCallable(() -> client.call(request))
            .transformDeferred(RetryOperator.of(retry))
            .doOnError(e -> log.error("All retries exhausted: {}", e.getMessage()));
    }
}
```

### Combining Retry + Timeout + CircuitBreaker

```java
@Service
public class ResilientService {
    
    private final Retry retry;
    private final TimeLimiter timeLimiter;
    private final CircuitBreaker circuitBreaker;
    private final ExternalClient client;
    
    public Mono<Response> resilientCall(Request request) {
        Supplier<CompletableFuture<Response>> supplier = () ->
            CompletableFuture.supplyAsync(() -> client.call(request));
        
        // Order: CircuitBreaker -> TimeLimiter -> Retry
        Supplier<CompletableFuture<Response>> decorated = Decorators
            .ofSupplier(supplier)
            .withCircuitBreaker(circuitBreaker)
            .withTimeLimiter(timeLimiter)
            .withRetry(retry)
            .decorate();
        
        return Mono.fromFuture(decorated.get());
    }
}
```

### Spring Retry with Annotations

```java
@Configuration
@EnableRetry
public class SpringRetryConfig {
    
    @Bean
    public RetryTemplate retryTemplate() {
        RetryTemplate template = new RetryTemplate();
        
        ExponentialRandomBackOffPolicy backOffPolicy = new ExponentialRandomBackOffPolicy();
        backOffPolicy.setInitialInterval(500);
        backOffPolicy.setMultiplier(2.0);
        backOffPolicy.setMaxInterval(10000);
        template.setBackOffPolicy(backOffPolicy);
        
        Map<Class<? extends Throwable>, Boolean> retryableExceptions = new HashMap<>();
        retryableExceptions.put(IOException.class, true);
        retryableExceptions.put(TimeoutException.class, true);
        
        SimpleRetryPolicy retryPolicy = new SimpleRetryPolicy(3, retryableExceptions);
        template.setRetryPolicy(retryPolicy);
        
        return template;
    }
}

@Service
public class PaymentService {
    
    @Retryable(
        retryFor = {IOException.class, TimeoutException.class},
        maxAttempts = 3,
        backoff = @Backoff(delay = 500, multiplier = 2, random = true)
    )
    public PaymentResult processPayment(PaymentRequest request) {
        return paymentGateway.process(request);
    }
    
    @Recover
    public PaymentResult recoverPayment(Exception e, PaymentRequest request) {
        log.error("Payment failed after retries: {}", request.getId());
        return PaymentResult.failed(e.getMessage());
    }
}
```

### YAML Configuration

```yaml
# application.yml
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
          - com.example.BusinessException
  
  timelimiter:
    instances:
      externalService:
        timeoutDuration: 5s
        cancelRunningFuture: true
```

## Important Rules

- Always use exponential backoff with jitter to avoid thundering herd
- Limit retries to 3-5 maximum attempts
- Configure timeouts on all external calls
- Design idempotent operations for safe retry
- Only retry transient errors
- Combine with circuit breaker for protection
- Log each retry attempt for debugging
- Decorator order matters: CircuitBreaker → TimeLimiter → Retry
- Configure `@Recover` to handle failures after retries

## Example

```java
@Bean
public WebClient resilientWebClient(
        RetryRegistry retryRegistry,
        CircuitBreakerRegistry cbRegistry) {
    
    return WebClient.builder()
        .baseUrl("https://api.external.com")
        .filter((request, next) -> next.exchange(request)
            .timeout(Duration.ofSeconds(5))
            .transformDeferred(RetryOperator.of(retryRegistry.retry("http")))
            .transformDeferred(CircuitBreakerOperator.of(cbRegistry.circuitBreaker("http"))))
        .build();
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
