<!-- keywords: sqs, aws, queue, fifo, dlq, dead letter queue, batch processing, lambda trigger, messaging, java -->
# Amazon SQS Integration in Java

## Purpose

Document integration patterns with Amazon SQS in Java using AWS SDK v2, including Standard vs FIFO queues, DLQ handling, batch processing, Lambda triggers, and reactive/imperative approaches.

## Scope of Application

- Java projects that require SQS
- Implementation with Spring WebFlux (reactive)
- Serverless applications with Lambda
- To choose between Standard and FIFO queues
- When implementing retry and DLQ patterns

## Scope and use cases

- Asynchronous communication between services
- Component decoupling
- Background task processing
- Buffer for load spikes

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Producer   │────▶│  SQS Queue  │────▶│  Consumer   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼ (after N attempts)
                    ┌─────────────┐
                    │     DLQ     │
                    └─────────────┘
```

## Standard vs FIFO

| Feature | Standard | FIFO |
|---------|----------|------|
| Throughput | Unlimited | 3000 msg/s (batch) |
| Order | Best-effort | Guaranteed |
| Duplicates | Possible | Exactly once |
| Use case | High volume | Critical ordering |

## Main Content

### Dependencies

```xml
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>sqs</artifactId>
</dependency>
<dependency>
    <groupId>software.amazon.awssdk</groupId>
    <artifactId>netty-nio-client</artifactId>
</dependency>
```

### Async Client

```java
@Configuration
public class SqsConfig {
    
    @Bean
    public SqsAsyncClient sqsAsyncClient() {
        return SqsAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .httpClientBuilder(NettyNioAsyncHttpClient.builder()
                .maxConcurrency(50))
            .build();
    }
}
```

### Reactive Producer

```java
@Service
public class ReactiveMessageProducer {
    
    private final SqsAsyncClient sqsClient;
    private final ObjectMapper objectMapper;
    private final String queueUrl;
    
    public <T> Mono<String> sendMessage(T message) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(message))
            .flatMap(body -> Mono.fromFuture(() -> 
                sqsClient.sendMessage(SendMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .messageBody(body)
                    .build())))
            .map(SendMessageResponse::messageId);
    }

    
    public <T> Mono<SendMessageBatchResponse> sendBatch(List<T> messages) {
        return Flux.fromIterable(messages)
            .index()
            .map(tuple -> {
                try {
                    return SendMessageBatchRequestEntry.builder()
                        .id(String.valueOf(tuple.getT1()))
                        .messageBody(objectMapper.writeValueAsString(tuple.getT2()))
                        .build();
                } catch (JsonProcessingException e) {
                    throw new RuntimeException(e);
                }
            })
            .collectList()
            .flatMap(entries -> Mono.fromFuture(() ->
                sqsClient.sendMessageBatch(SendMessageBatchRequest.builder()
                    .queueUrl(queueUrl)
                    .entries(entries)
                    .build())));
    }
}
```

### Reactive Consumer

```java
@Service
public class ReactiveMessageConsumer {
    
    private final SqsAsyncClient sqsClient;
    private final String queueUrl;
    
    public Flux<Message> receiveMessages() {
        return Flux.defer(() -> Mono.fromFuture(() ->
                sqsClient.receiveMessage(ReceiveMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .maxNumberOfMessages(10)
                    .waitTimeSeconds(20)
                    .visibilityTimeout(30)
                    .build())))
            .flatMapMany(response -> Flux.fromIterable(response.messages()))
            .repeat();
    }
    
    public Mono<Void> deleteMessage(Message message) {
        return Mono.fromFuture(() ->
            sqsClient.deleteMessage(DeleteMessageRequest.builder()
                .queueUrl(queueUrl)
                .receiptHandle(message.receiptHandle())
                .build()))
            .then();
    }
}
```

### Lambda Handler

```java
public class SqsLambdaHandler implements RequestHandler<SQSEvent, SQSBatchResponse> {
    
    @Override
    public SQSBatchResponse handleRequest(SQSEvent event, Context context) {
        List<SQSBatchResponse.BatchItemFailure> failures = new ArrayList<>();
        
        for (SQSEvent.SQSMessage message : event.getRecords()) {
            try {
                processMessage(message.getBody());
            } catch (Exception e) {
                failures.add(SQSBatchResponse.BatchItemFailure.builder()
                    .itemIdentifier(message.getMessageId())
                    .build());
            }
        }
        
        return SQSBatchResponse.builder()
            .batchItemFailures(failures)
            .build();
    }
}
```

## Important Rules

- Use FIFO only when ordering is critical
- Implement DLQ for messages that fail repeatedly
- Configure visibility timeout greater than processing time
- Use batch operations for better throughput (max 10 messages)
- Implement partial batch response in Lambda
- Implement idempotency in consumers
- Monitor queue metrics (age, depth)
- Use long polling (waitTimeSeconds=20) to reduce costs

## Example

```java
// Processing with retry
public Mono<Void> processMessages(Function<Message, Mono<Void>> processor) {
    return receiveMessages()
        .flatMap(message -> 
            processor.apply(message)
                .then(deleteMessage(message))
                .onErrorResume(e -> Mono.empty()),
            10)
        .then();
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
