<!-- keywords: kafka, msk, event streaming, reactor kafka, spring kafka, consumer, producer, java -->
# Apache Kafka / Amazon MSK Integration in Java

## Purpose

Document integration patterns with Apache Kafka and Amazon MSK in Java using Reactor Kafka and Spring Kafka for event streaming architectures.

## Scope of Application

- Java projects that require Kafka producers and consumers
- Reactive implementation with Reactor Kafka
- Imperative implementation with Spring Kafka
- When designing partitioning strategies
- When configuring MSK Serverless or MSK Provisioned
- When implementing reactive streaming patterns

## Scope and use cases

- High-volume event streaming
- Real-time event processing
- Event sourcing and CQRS
- Integration with legacy systems
- Data pipelines with guaranteed ordering
- Microservice communication with backpressure

## Streaming Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  Producer   │────▶│           MSK Cluster                │
└─────────────┘     │  ┌────────┐ ┌────────┐ ┌────────┐   │
                    │  │Topic P0│ │Topic P1│ │Topic P2│   │
┌─────────────┐     │  └────────┘ └────────┘ └────────┘   │
│  Producer   │────▶│                                      │
└─────────────┘     └──────────────────────────────────────┘
                              │         │         │
                              ▼         ▼         ▼
                    ┌─────────┐ ┌─────────┐ ┌─────────┐
                    │Consumer │ │Consumer │ │Consumer │
                    │ Group A │ │ Group A │ │ Group A │
                    └─────────┘ └─────────┘ └─────────┘
```

## Partitioning strategies

| Strategy | Use | Key example |
|----------|-----|-------------|
| By entity | Ordering by aggregate | `order-123` |
| By tenant | Data isolation | `tenant-abc` |
| By region | Data locality | `us-east-1` |
| Round-robin | Uniform distribution | `null` |

## Limits and considerations

| Aspect | Recommendation |
|--------|----------------|
| Message size | < 1 MB (configurable) |
| Partitions per topic | 3-12 to start |
| Replication factor | 3 for production |
| Consumer lag | Monitor actively |

## Main Content

### Dependencies

```xml
<!-- Maven - Reactive (Reactor Kafka) -->
<dependency>
    <groupId>io.projectreactor.kafka</groupId>
    <artifactId>reactor-kafka</artifactId>
</dependency>

<!-- Maven - Imperative (Spring Kafka) -->
<dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
</dependency>
```

```groovy
// Gradle - Reactive
implementation 'io.projectreactor.kafka:reactor-kafka'

// Gradle - Imperative
implementation 'org.springframework.kafka:spring-kafka'
```

### Reactive Client (Reactor Kafka)

```java
@Configuration
public class KafkaReactiveConfig {
    
    @Value("${kafka.bootstrap.servers}")
    private String bootstrapServers;
    
    @Bean
    public ReceiverOptions<String, String> receiverOptions() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "reactive-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        
        return ReceiverOptions.<String, String>create(props)
            .commitInterval(Duration.ofSeconds(5))
            .commitBatchSize(100);
    }

    @Bean
    public SenderOptions<String, String> senderOptions() {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        
        return SenderOptions.create(props);
    }
    
    @Bean
    public KafkaSender<String, String> kafkaSender(
            SenderOptions<String, String> senderOptions) {
        return KafkaSender.create(senderOptions);
    }
    
    @Bean
    public KafkaReceiver<String, String> kafkaReceiver(
            ReceiverOptions<String, String> receiverOptions) {
        return KafkaReceiver.create(
            receiverOptions.subscription(List.of("orders-topic"))
        );
    }
}

@Component
public class KafkaReactiveProducer {
    
    private final KafkaSender<String, String> kafkaSender;
    private final ObjectMapper objectMapper;
    private final String topic;
    
    public Mono<SenderResult<String>> send(DomainEvent event) {
        String key = event.getAggregateId();
        String value = serialize(event);
        
        SenderRecord<String, String, String> record = SenderRecord.create(
            new ProducerRecord<>(topic, key, value),
            event.getEventId()
        );
        
        return kafkaSender.send(Mono.just(record))
            .single()
            .doOnSuccess(result -> log.info(
                "Sent to partition {} offset {}", 
                result.recordMetadata().partition(),
                result.recordMetadata().offset()))
            .doOnError(e -> log.error("Failed to send: {}", e.getMessage()));
    }
    
    public Flux<SenderResult<String>> sendBatch(List<DomainEvent> events) {
        Flux<SenderRecord<String, String, String>> records = Flux.fromIterable(events)
            .map(event -> SenderRecord.create(
                new ProducerRecord<>(topic, event.getAggregateId(), serialize(event)),
                event.getEventId()
            ));
        
        return kafkaSender.send(records)
            .doOnNext(result -> {
                if (result.exception() != null) {
                    log.error("Failed: {}", result.correlationMetadata());
                }
            });
    }
    
    private String serialize(DomainEvent event) {
        try {
            return objectMapper.writeValueAsString(event);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Serialization failed", e);
        }
    }
}

@Component
public class KafkaReactiveConsumer {
    
    private final KafkaReceiver<String, String> kafkaReceiver;
    private final ObjectMapper objectMapper;
    private final EventHandler eventHandler;
    
    @PostConstruct
    public void startConsuming() {
        kafkaReceiver.receive()
            .groupBy(record -> record.receiverOffset().topicPartition())
            .flatMap(partitionFlux -> partitionFlux
                .publishOn(Schedulers.boundedElastic())
                .concatMap(this::processRecord)
                .sample(Duration.ofSeconds(5))
                .concatMap(record -> record.receiverOffset().commit()))
            .subscribe();
    }
    
    private Mono<ReceiverRecord<String, String>> processRecord(
            ReceiverRecord<String, String> record) {
        return Mono.fromCallable(() -> {
            DomainEvent event = objectMapper.readValue(
                record.value(), DomainEvent.class);
            eventHandler.handle(event);
            return record;
        })
        .onErrorResume(e -> {
            log.error("Processing failed for offset {}: {}", 
                record.offset(), e.getMessage());
            return Mono.just(record);
        });
    }
}
```

### Imperative Client (Spring Kafka)

```java
@Configuration
@EnableKafka
public class KafkaConfig {
    
    @Bean
    public ProducerFactory<String, String> producerFactory(
            @Value("${kafka.bootstrap.servers}") String bootstrapServers) {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        return new DefaultKafkaProducerFactory<>(props);
    }
    
    @Bean
    public KafkaTemplate<String, String> kafkaTemplate(
            ProducerFactory<String, String> producerFactory) {
        return new KafkaTemplate<>(producerFactory);
    }
    
    @Bean
    public ConsumerFactory<String, String> consumerFactory(
            @Value("${kafka.bootstrap.servers}") String bootstrapServers) {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "order-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        return new DefaultKafkaConsumerFactory<>(props);
    }
}

@Component
public class OrderEventListener {
    
    @KafkaListener(
        topics = "${kafka.topic.orders}",
        groupId = "order-consumer-group",
        concurrency = "3"
    )
    public void handleOrderEvent(
            @Payload String message,
            @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
            @Header(KafkaHeaders.OFFSET) long offset,
            Acknowledgment ack) {
        
        try {
            DomainEvent event = objectMapper.readValue(message, DomainEvent.class);
            eventHandler.handle(event);
            ack.acknowledge();
        } catch (Exception e) {
            log.error("Failed to process message at partition {} offset {}", 
                partition, offset, e);
        }
    }
}
```

### Error handling

```java
public Mono<SenderResult<String>> sendWithRetry(DomainEvent event) {
    return send(event)
        .retryWhen(Retry.backoff(3, Duration.ofMillis(100))
            .filter(e -> e instanceof KafkaException))
        .onErrorMap(e -> new EventPublishException("Failed after retries", e));
}
```

## Important Rules

- Use consistent key to guarantee ordering per partition
- Configure `enable.idempotence=true` for exactly-once
- Use `acks=all` for maximum durability
- Design consumer groups according to consumption patterns
- Implement manual commits for fine-grained control
- Use `groupBy` per partition for ordering
- Implement backpressure control in consumers
- Use Schema Registry for schema evolution
- Configure IAM or SASL authentication for MSK
- Close sender and receiver on shutdown

## Example

```java
@Service
public class OrderEventPublisher {
    
    private final KafkaReactiveProducer producer;
    
    public Mono<Void> publishOrderCreated(Order order) {
        DomainEvent event = DomainEvent.builder()
            .eventId(UUID.randomUUID().toString())
            .eventType("ORDER_CREATED")
            .aggregateId(order.getId())
            .payload(Map.of(
                "customerId", order.getCustomerId(),
                "amount", order.getAmount()
            ))
            .build();
        
        return producer.send(event).then();
    }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
