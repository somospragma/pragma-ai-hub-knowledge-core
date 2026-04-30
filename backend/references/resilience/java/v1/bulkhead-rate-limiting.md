<!-- keywords: bulkhead, rate limiting, throttling, resource isolation, resilience4j, overload protection, java -->
# Bulkhead and Rate Limiting Patterns — Java Implementation

## Purpose

Define and implement the standard patterns for resource isolation (bulkhead), rate limiting, and throttling in Java applications with Resilience4j, to protect services from overload.

## Scope of Application

- When protecting services from overload by abusive clients
- When isolating resources between different types of operations
- When implementing throttling in API Gateway
- When designing multi-tenant systems with per-tenant limits
- When configuring bulkheads and rate limiters with Resilience4j

## Main content

### Isolation Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    Bulkhead Patterns                             │
├─────────────────────────────────┬───────────────────────────────┤
│   Thread Pool Bulkhead          │   Semaphore Bulkhead          │
│   ┌─────────────────────┐       │   ┌─────────────────────┐     │
│   │ Pool A (10 threads) │       │   │ Semaphore A (10)    │     │
│   │ → Service A         │       │   │ → Service A         │     │
│   └─────────────────────┘       │   └─────────────────────┘     │
│   ┌─────────────────────┐       │   ┌─────────────────────┐     │
│   │ Pool B (5 threads)  │       │   │ Semaphore B (5)     │     │
│   │ → Service B         │       │   │ → Service B         │     │
│   └─────────────────────┘       │   └─────────────────────┘     │
└─────────────────────────────────┴───────────────────────────────┘
```

### Bulkhead Types

| Type | Usage | Advantages | Disadvantages |
|------|-------|------------|---------------|
| Semaphore | Non-blocking operations | Low overhead | Does not isolate threads |
| Thread Pool | Blocking operations | Complete isolation | Higher overhead |

### Rate Limiting Algorithms

```
┌─────────────────────────────────────────────────────────────────┐
│                    Rate Limiting Algorithms                      │
├─────────────────────────────────────────────────────────────────┤
│  Token Bucket:                                                   │
│  - Tokens are added at a constant rate                          │
│  - Allows bursts up to the bucket size                          │
│  - Ideal for APIs with variable traffic                         │
├─────────────────────────────────────────────────────────────────┤
│  Sliding Window:                                                 │
│  - Counts requests in a sliding window                          │
│  - More accurate than fixed window                              │
│  - Higher memory usage                                          │
├─────────────────────────────────────────────────────────────────┤
│  Fixed Window:                                                   │
│  - Counts requests in fixed windows                             │
│  - Simple to implement                                          │
│  - Can allow bursts at window edges                             │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration parameters

| Parameter | Description | Typical value |
|-----------|-------------|--------------|
| maxConcurrentCalls | Maximum concurrent calls | 10-50 |
| maxWaitDuration | Maximum wait time | 500ms-2s |
| requestsPerSecond | Requests per second limit | 100-1000 |
| burstSize | Allowed burst size | 10-50 |

### Rate Limiting Headers

```
X-RateLimit-Limit: 100        # Total limit
X-RateLimit-Remaining: 45     # Remaining requests
X-RateLimit-Reset: 1640000000 # Reset timestamp
Retry-After: 30               # Seconds to retry
```

### Multi-tenant Rate Limiting

```
┌─────────────────────────────────────────────────────────────────┐
│  Per-tenant limit strategy:                                     │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Tenant A   │  │  Tenant B   │  │  Tenant C   │             │
│  │  Premium    │  │  Standard   │  │  Free       │             │
│  │  1000 req/s │  │  100 req/s  │  │  10 req/s   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  Identification: X-Tenant-ID header or API Key                  │
└─────────────────────────────────────────────────────────────────┘
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

### Bulkhead Configuration

```java
@Configuration
public class BulkheadConfig {
    
    @Bean
    public BulkheadRegistry bulkheadRegistry() {
        io.github.resilience4j.bulkhead.BulkheadConfig semaphoreConfig = 
            io.github.resilience4j.bulkhead.BulkheadConfig.custom()
                .maxConcurrentCalls(25)
                .maxWaitDuration(Duration.ofMillis(500))
                .build();
        
        return BulkheadRegistry.of(semaphoreConfig);
    }
    
    @Bean
    public ThreadPoolBulkheadRegistry threadPoolBulkheadRegistry() {
        ThreadPoolBulkheadConfig threadPoolConfig = ThreadPoolBulkheadConfig.custom()
            .maxThreadPoolSize(10)
            .coreThreadPoolSize(5)
            .queueCapacity(100)
            .keepAliveDuration(Duration.ofMinutes(1))
            .build();
        
        return ThreadPoolBulkheadRegistry.of(threadPoolConfig);
    }
}
```

### Service with Bulkhead

```java
@Service
public class BulkheadService {
    
    private final Bulkhead paymentBulkhead;
    private final Bulkhead inventoryBulkhead;
    
    public BulkheadService(BulkheadRegistry bulkheadRegistry) {
        this.paymentBulkhead = bulkheadRegistry.bulkhead("payment",
            io.github.resilience4j.bulkhead.BulkheadConfig.custom()
                .maxConcurrentCalls(10)
                .maxWaitDuration(Duration.ofSeconds(1))
                .build());
        
        this.inventoryBulkhead = bulkheadRegistry.bulkhead("inventory",
            io.github.resilience4j.bulkhead.BulkheadConfig.custom()
                .maxConcurrentCalls(50)
                .maxWaitDuration(Duration.ofMillis(100))
                .build());
    }
    
    public Mono<PaymentResult> processPayment(PaymentRequest request) {
        return Mono.fromCallable(() -> paymentGateway.process(request))
            .transformDeferred(BulkheadOperator.of(paymentBulkhead))
            .onErrorResume(BulkheadFullException.class, e -> {
                log.warn("Payment bulkhead full, rejecting request");
                return Mono.error(new ServiceOverloadedException("Payment service busy"));
            });
    }
    
    @Bulkhead(name = "inventory", fallbackMethod = "inventoryFallback")
    public InventoryStatus checkInventory(String productId) {
        return inventoryService.check(productId);
    }
    
    private InventoryStatus inventoryFallback(String productId, BulkheadFullException e) {
        return InventoryStatus.unknown();
    }
}
```

### Rate Limiter Configuration

```java
@Configuration
public class RateLimiterConfig {
    
    @Bean
    public RateLimiterRegistry rateLimiterRegistry() {
        io.github.resilience4j.ratelimiter.RateLimiterConfig config = 
            io.github.resilience4j.ratelimiter.RateLimiterConfig.custom()
                .limitRefreshPeriod(Duration.ofSeconds(1))
                .limitForPeriod(100)
                .timeoutDuration(Duration.ofMillis(500))
                .build();
        
        return RateLimiterRegistry.of(config);
    }
}
```

### Multi-tenant Rate Limiter

```java
@Service
public class MultiTenantRateLimiter {
    
    private final Map<String, RateLimiter> tenantLimiters = new ConcurrentHashMap<>();
    private final TenantConfigService configService;
    
    public Mono<Void> checkRateLimit(String tenantId) {
        TenantConfig config = configService.getConfig(tenantId);
        RateLimiter limiter = tenantLimiters.computeIfAbsent(tenantId,
            id -> createLimiter(config));
        
        if (!limiter.acquirePermission()) {
            return Mono.error(new RateLimitExceededException(tenantId,
                limiter.getMetrics().getAvailablePermissions()));
        }
        return Mono.empty();
    }
    
    private RateLimiter createLimiter(TenantConfig config) {
        return RateLimiter.of(config.getTenantId(),
            io.github.resilience4j.ratelimiter.RateLimiterConfig.custom()
                .limitRefreshPeriod(Duration.ofSeconds(1))
                .limitForPeriod(config.getRateLimit())
                .timeoutDuration(Duration.ZERO)
                .build());
    }
}
```

### Service with Rate Limiter

```java
@Service
public class RateLimitedService {
    
    private final RateLimiter apiRateLimiter;
    private final MultiTenantRateLimiter tenantRateLimiter;
    
    public Mono<Response> handleRequest(String tenantId, Request request) {
        return tenantRateLimiter.checkRateLimit(tenantId)
            .then(Mono.fromCallable(() -> processRequest(request)))
            .transformDeferred(RateLimiterOperator.of(apiRateLimiter))
            .onErrorResume(RequestNotPermitted.class, e -> {
                log.warn("Rate limit exceeded for tenant: {}", tenantId);
                return Mono.error(new TooManyRequestsException(tenantId));
            });
    }
}
```

### YAML Configuration

```yaml
# application.yml
resilience4j:
  bulkhead:
    instances:
      payment:
        maxConcurrentCalls: 10
        maxWaitDuration: 1s
      inventory:
        maxConcurrentCalls: 50
        maxWaitDuration: 100ms
  
  ratelimiter:
    instances:
      api:
        limitForPeriod: 1000
        limitRefreshPeriod: 1s
        timeoutDuration: 0
```

## Important Rules

- Isolate critical resources from non-critical operations
- Implement rate limiting at multiple levels (API Gateway, application)
- Use separate limits per tenant in multi-tenant systems
- Include X-RateLimit-* headers in responses
- Return 429 with Retry-After header when limit is exceeded
- Use `BulkheadOperator` for reactive flows
- Configure `maxWaitDuration` according to SLAs
- Implement fallbacks for `BulkheadFullException`
- Make limits configurable per environment

## Example

```java
@RestController
@RequestMapping("/api")
public class ApiController {
    
    private final RateLimitedService service;
    
    @GetMapping("/resource")
    public Mono<ResponseEntity<Response>> getResource(
            @RequestHeader("X-Tenant-ID") String tenantId,
            @RequestBody Request request) {
        
        return service.handleRequest(tenantId, request)
            .map(ResponseEntity::ok)
            .onErrorResume(TooManyRequestsException.class, e ->
                Mono.just(ResponseEntity.status(429)
                    .header("Retry-After", "30")
                    .build()));
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
