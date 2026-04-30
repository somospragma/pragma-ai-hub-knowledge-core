<!-- keywords: sns, aws, pub/sub, publish subscribe, notification, messaging, java -->
# Amazon SNS Integration in Java

## Purpose

Document integration patterns with Amazon Simple Notification Service (SNS) in Java using AWS SDK v2 for microservice architectures with publish/subscribe.

## Scope of Application

- Java projects that require publishing messages to SNS
- Reactive implementation with WebFlux and Reactor
- Imperative implementation with traditional Spring Boot
- When designing fan-out architectures with multiple subscribers
- When configuring message filtering by attributes
- When using FIFO topics for guaranteed ordering

## Scope and use cases

- Notifications to multiple systems from a single event
- Decoupling of producers and consumers
- Event distribution to SQS queues, Lambdas, and HTTP endpoints
- Guaranteed ordering with FIFO topics
- Message filtering to reduce unnecessary processing

## Fan-Out Architecture

```
                              ┌─────────────────┐
                              │   SQS Queue 1   │──▶ Service A
                              └─────────────────┘
┌─────────────┐     ┌─────┐   ┌─────────────────┐
│  Publisher  │────▶│ SNS │──▶│   SQS Queue 2   │──▶ Service B
└─────────────┘     │Topic│   └─────────────────┘
                    └─────┘   ┌─────────────────┐
                              │   Lambda        │──▶ Processing
                              └─────────────────┘
```

## Message filtering by attributes

```json
{
  "eventType": ["ORDER_CREATED", "ORDER_UPDATED"],
  "source": [{"prefix": "order-service"}],
  "version": [{"numeric": [">=", 1]}]
}
```

## Service limits

| Limit | Value |
|-------|-------|
| Messages per batch | 10 maximum |
| Message size | 256 KB maximum |
| Attributes per message | 10 maximum |

## Main Content

### Dependencies

```xml
<!-- Maven - Imperative -->
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>sns</artifactId>
</dependency>

<!-- Maven - Reactive -->
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>sns</artifactId>
</dependency>
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>netty-nio-client</artifactId>
</dependency>
```

```groovy
// Gradle - Imperative
implementation 'software.amazon.awssdk:sns'

// Gradle - Reactive
implementation 'software.amazon.awssdk:sns'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Reactive Client

```java
@Configuration
public class SnsReactiveConfig {
    
    @Bean
    public SnsAsyncClient snsAsyncClient() {
        return SnsAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClient(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(100)
                .connectionTimeout(Duration.ofSeconds(5))
                .readTimeout(Duration.ofSeconds(30))
                .build())
            .build();
    }
}

@Component
public class SnsReactivePublisher {
    
    private final SnsAsyncClient snsClient;
    private final String topicArn;
    
    public SnsReactivePublisher(
            SnsAsyncClient snsClient,
            @Value("${sns.topic.arn}") String topicArn) {
        this.snsClient = snsClient;
        this.topicArn = topicArn;
    }
    
    public Mono<String> publish(DomainEvent event) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(serializeEvent(event))
            .messageAttributes(buildAttributes(event))
            .build();
        
        return Mono.fromFuture(snsClient.publish(request))
            .map(PublishResponse::messageId)
            .doOnSuccess(id -> log.info("Published event: {}", id))
            .doOnError(e -> log.error("Failed to publish: {}", e.getMessage()));
    }
    
    public Flux<String> publishBatch(List<DomainEvent> events) {
        List<PublishBatchRequestEntry> entries = events.stream()
            .map(event -> PublishBatchRequestEntry.builder()
                .id(UUID.randomUUID().toString())
                .message(serializeEvent(event))
                .messageAttributes(buildAttributes(event))
                .build())
            .toList();
        
        return Flux.fromIterable(partition(entries, 10))
            .flatMap(batch -> {
                PublishBatchRequest request = PublishBatchRequest.builder()
                    .topicArn(topicArn)
                    .publishBatchRequestEntries(batch)
                    .build();
                
                return Mono.fromFuture(snsClient.publishBatch(request))
                    .flatMapMany(response -> {
                        if (!response.failed().isEmpty()) {
                            log.warn("Failed entries: {}", response.failed());
                        }
                        return Flux.fromIterable(response.successful())
                            .map(BatchResultEntry::messageId);
                    });
            }, 5);
    }
    
    public Mono<String> publishFifo(DomainEvent event, String messageGroupId) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(serializeEvent(event))
            .messageGroupId(messageGroupId)
            .messageDeduplicationId(event.getEventId())
            .messageAttributes(buildAttributes(event))
            .build();
        
        return Mono.fromFuture(snsClient.publish(request))
            .map(PublishResponse::messageId);
    }
    
    private Map<String, MessageAttributeValue> buildAttributes(DomainEvent event) {
        return Map.of(
            "eventType", MessageAttributeValue.builder()
                .dataType("String")
                .stringValue(event.getEventType())
                .build(),
            "source", MessageAttributeValue.builder()
                .dataType("String")
                .stringValue(event.getSource())
                .build(),
            "version", MessageAttributeValue.builder()
                .dataType("Number")
                .stringValue(String.valueOf(event.getVersion()))
                .build()
        );
    }
}
```

### Imperative Client

```java
@Configuration
public class SnsConfig {
    
    @Bean
    public SnsClient snsClient() {
        return SnsClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}

@Component
public class SnsPublisher {
    
    private final SnsClient snsClient;
    private final String topicArn;
    
    public SnsPublisher(
            SnsClient snsClient,
            @Value("${sns.topic.arn}") String topicArn) {
        this.snsClient = snsClient;
        this.topicArn = topicArn;
    }
    
    public String publish(DomainEvent event) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(serializeEvent(event))
            .messageAttributes(buildAttributes(event))
            .build();
        
        PublishResponse response = snsClient.publish(request);
        return response.messageId();
    }
    
    public void publishWithRetry(DomainEvent event, int maxRetries) {
        int attempts = 0;
        while (attempts < maxRetries) {
            try {
                publish(event);
                return;
            } catch (SnsException e) {
                attempts++;
                if (attempts >= maxRetries) {
                    throw e;
                }
                try {
                    Thread.sleep((long) Math.pow(2, attempts) * 100);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(ie);
                }
            }
        }
    }
}
```

### Error handling

```java
public Mono<String> publishWithErrorHandling(DomainEvent event) {
    return publish(event)
        .onErrorResume(SnsException.class, e -> {
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

- Use message attributes for subscription filtering
- Configure filters on subscribers to reduce costs and processing
- Implement idempotency in consumers
- Use MessageDeduplicationId for FIFO topics
- Configure `maxConcurrency` according to system capacity
- Use appropriate `connectionTimeout` and `readTimeout`
- Implement retry with exponential backoff
- Partition batches into groups of 10 messages
- Consider Dead Letter Queues for unprocessed messages
- Close client when application shuts down

## Example

```java
@Service
public class OrderEventPublisher {
    
    private final SnsReactivePublisher publisher;
    
    public Mono<Void> publishOrderCreated(Order order) {
        DomainEvent event = DomainEvent.builder()
            .eventId(UUID.randomUUID().toString())
            .eventType("ORDER_CREATED")
            .source("order-service")
            .version(1)
            .payload(Map.of(
                "orderId", order.getId(),
                "customerId", order.getCustomerId(),
                "amount", order.getAmount()
            ))
            .build();
        
        return publisher.publish(event).then();
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
