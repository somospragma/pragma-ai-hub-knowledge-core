<!-- keywords: eventbridge, aws, event-driven, event bus, event routing, saga pattern, cross-account, java -->
# Amazon EventBridge Integration in Java

## Purpose

Document integration patterns with Amazon EventBridge in Java using AWS SDK v2 for event-driven architectures, including event publishing, conditional routing, Saga patterns, and cross-account communication.

## Scope of Application

- Java projects that require publishing events to EventBridge
- Reactive implementation with WebFlux and Reactor
- Imperative implementation with traditional Spring Boot
- When designing decoupled communication between microservices
- When configuring event routing rules
- When implementing cross-account event patterns

## Scope and use cases

- Microservice orchestration through events
- Integration with native AWS services
- Conditional routing based on event content
- Centralized event auditing and logging
- Saga pattern implementation
- Cross-account and cross-region communication

## Event-Driven Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Service A  │────▶│  EventBridge │────▶│  Rule: Orders   │──▶ Lambda
└─────────────┘     │  Custom Bus  │     └─────────────────┘
                    │              │     ┌─────────────────┐
┌─────────────┐     │              │────▶│  Rule: Payments │──▶ SQS
│  Service B  │────▶│              │     └─────────────────┘
└─────────────┘     └──────────────┘     ┌─────────────────┐
                                         │  Rule: Audit    │──▶ CloudWatch
                                         └─────────────────┘
```

## Event structure

```json
{
  "version": "0",
  "id": "uuid",
  "detail-type": "OrderCreated",
  "source": "com.company.orders",
  "account": "123456789012",
  "time": "2024-01-15T10:30:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:orders:order-123"],
  "detail": {
    "eventId": "evt-123",
    "aggregateId": "order-123",
    "payload": {}
  }
}
```

## Rule pattern with filtering

```json
{
  "source": ["com.company.orders"],
  "detail-type": ["OrderCreated", "OrderUpdated"],
  "detail": {
    "payload": {
      "orderType": ["PREMIUM", "STANDARD"],
      "amount": [{"numeric": [">=", 1000]}]
    }
  }
}
```

## Service limits

| Limit | Value |
|-------|-------|
| Events per PutEvents | 10 maximum |
| Event size | 256 KB maximum |
| Rules per bus | 300 by default |
| Targets per rule | 5 maximum |

## Main Content

### Dependencies

```xml
<!-- Maven - Imperative -->
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>eventbridge</artifactId>
</dependency>

<!-- Maven - Reactive -->
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>eventbridge</artifactId>
</dependency>
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>netty-nio-client</artifactId>
</dependency>
```

```groovy
// Gradle - Imperative
implementation 'software.amazon.awssdk:eventbridge'

// Gradle - Reactive
implementation 'software.amazon.awssdk:eventbridge'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Reactive Client

```java
@Configuration
public class EventBridgeReactiveConfig {
    
    @Bean
    public EventBridgeAsyncClient eventBridgeAsyncClient() {
        return EventBridgeAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClient(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(100)
                .connectionTimeout(Duration.ofSeconds(5))
                .build())
            .build();
    }
}

@Component
public class EventBridgeReactivePublisher {
    
    private final EventBridgeAsyncClient eventBridgeClient;
    private final String eventBusName;
    private final String source;
    private final ObjectMapper objectMapper;
    
    public EventBridgeReactivePublisher(
            EventBridgeAsyncClient eventBridgeClient,
            @Value("${eventbridge.bus.name}") String eventBusName,
            @Value("${eventbridge.source}") String source,
            ObjectMapper objectMapper) {
        this.eventBridgeClient = eventBridgeClient;
        this.eventBusName = eventBusName;
        this.source = source;
        this.objectMapper = objectMapper;
    }
    
    public Mono<String> publish(DomainEvent event) {
        PutEventsRequestEntry entry = buildEntry(event);
        
        PutEventsRequest request = PutEventsRequest.builder()
            .entries(entry)
            .build();
        
        return Mono.fromFuture(eventBridgeClient.putEvents(request))
            .flatMap(response -> {
                if (response.failedEntryCount() > 0) {
                    PutEventsResultEntry failed = response.entries().get(0);
                    return Mono.error(new EventPublishException(
                        failed.errorCode(), failed.errorMessage()));
                }
                return Mono.just(response.entries().get(0).eventId());
            })
            .doOnSuccess(id -> log.info("Published event: {}", id))
            .doOnError(e -> log.error("Failed to publish: {}", e.getMessage()));
    }
    
    public Flux<String> publishBatch(List<DomainEvent> events) {
        List<PutEventsRequestEntry> entries = events.stream()
            .map(this::buildEntry)
            .toList();
        
        return Flux.fromIterable(partition(entries, 10))
            .flatMap(batch -> {
                PutEventsRequest request = PutEventsRequest.builder()
                    .entries(batch)
                    .build();
                
                return Mono.fromFuture(eventBridgeClient.putEvents(request))
                    .flatMapMany(response -> {
                        List<String> eventIds = new ArrayList<>();
                        for (PutEventsResultEntry entry : response.entries()) {
                            if (entry.eventId() != null) {
                                eventIds.add(entry.eventId());
                            } else {
                                log.warn("Failed entry: {} - {}", 
                                    entry.errorCode(), entry.errorMessage());
                            }
                        }
                        return Flux.fromIterable(eventIds);
                    });
            }, 5);
    }
    
    private PutEventsRequestEntry buildEntry(DomainEvent event) {
        try {
            return PutEventsRequestEntry.builder()
                .eventBusName(eventBusName)
                .source(source)
                .detailType(event.getEventType())
                .detail(objectMapper.writeValueAsString(event))
                .time(Instant.now())
                .resources(event.getResources())
                .build();
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize event", e);
        }
    }
}

@Data
@Builder
public class DomainEvent {
    private String eventId;
    private String eventType;
    private String aggregateId;
    private String aggregateType;
    private int version;
    private Instant timestamp;
    private Map<String, Object> payload;
    private List<String> resources;
    private Map<String, String> metadata;
}
```

### Imperative Client

```java
@Configuration
public class EventBridgeConfig {
    
    @Bean
    public EventBridgeClient eventBridgeClient() {
        return EventBridgeClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}

@Component
public class EventBridgePublisher {
    
    private final EventBridgeClient eventBridgeClient;
    private final String eventBusName;
    private final String source;
    
    public String publish(DomainEvent event) {
        PutEventsRequestEntry entry = PutEventsRequestEntry.builder()
            .eventBusName(eventBusName)
            .source(source)
            .detailType(event.getEventType())
            .detail(serialize(event))
            .time(Instant.now())
            .build();
        
        PutEventsRequest request = PutEventsRequest.builder()
            .entries(entry)
            .build();
        
        PutEventsResponse response = eventBridgeClient.putEvents(request);
        
        if (response.failedEntryCount() > 0) {
            throw new EventPublishException(
                response.entries().get(0).errorMessage());
        }
        
        return response.entries().get(0).eventId();
    }
}
```

### Error handling

```java
public Mono<String> publishWithErrorHandling(DomainEvent event) {
    return publish(event)
        .onErrorResume(EventBridgeException.class, e -> {
            if (e.isThrottlingException()) {
                return Mono.delay(Duration.ofMillis(100))
                    .flatMap(ignored -> publish(event));
            }
            return Mono.error(e);
        })
        .retry(3)
        .onErrorMap(e -> new EventPublishException("Failed after retries", e));
}
```

## Important Rules

- Design idempotent consumers (events can be duplicated)
- Use Schema Registry for contract versioning
- Configure Dead Letter Queues for failed events
- Configure `maxConcurrency` according to system capacity
- Use appropriate `connectionTimeout`
- Implement retry with exponential backoff
- Partition batches into groups of 10 events
- Validate response for failed entries
- Use custom buses to separate domains
- Configure resource-based policies for cross-account
- Monitor failed invocation metrics

## Example

```java
@Service
public class OrderSagaPublisher {
    
    private final EventBridgeReactivePublisher publisher;
    
    public Mono<Void> startOrderSaga(Order order) {
        return publisher.publish(DomainEvent.builder()
                .eventType("OrderSagaStarted")
                .aggregateId(order.getId())
                .aggregateType("Order")
                .payload(Map.of(
                    "orderId", order.getId(),
                    "customerId", order.getCustomerId(),
                    "amount", order.getAmount()
                ))
                .resources(List.of(
                    "arn:aws:orders:" + order.getId()
                ))
                .build())
            .then();
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
