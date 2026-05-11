---
id: backend-skill-java-webflux-integraciones-mensajeria
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-webflux
---

# Integraciones con Servicios de Mensajería — Java WebFlux (Reactivo)

## Propósito

Documentar la integración reactiva con Kafka (Reactor Kafka), SQS (SDK async), SNS y EventBridge en microservicios Java WebFlux: configuración, producer/consumer reactivos, backpressure handling, serialización y dead letter queues.

---

## 1. Apache Kafka / Amazon MSK (Reactor Kafka)

### Dependencias

```groovy
implementation 'io.projectreactor.kafka:reactor-kafka:1.3.23'
implementation 'org.apache.kafka:kafka-clients'
```

### Configuración

```java
@Configuration
public class ReactorKafkaConfig {

    @Bean
    public SenderOptions<String, String> senderOptions(
            @Value("${kafka.bootstrap.servers}") String bootstrapServers) {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.ACKS_CONFIG, "all");
        props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
        return SenderOptions.create(props);
    }

    @Bean
    public KafkaSender<String, String> kafkaSender(SenderOptions<String, String> options) {
        return KafkaSender.create(options);
    }

    @Bean
    public ReceiverOptions<String, String> receiverOptions(
            @Value("${kafka.bootstrap.servers}") String bootstrapServers,
            @Value("${kafka.consumer.group-id}") String groupId) {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapServers);
        props.put(ConsumerConfig.GROUP_ID_CONFIG, groupId);
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        props.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        return ReceiverOptions.create(props);
    }
}
```

### Producer Reactivo

```java
@Component
@RequiredArgsConstructor
public class OrderEventProducer implements IOrderEventGateway {
    private final KafkaSender<String, String> kafkaSender;
    private final ObjectMapper objectMapper;

    @Value("${kafka.topic.orders}")
    private String topic;

    @Override
    public Mono<Void> publish(DomainEvent event) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(event))
            .flatMap(value -> {
                ProducerRecord<String, String> record =
                    new ProducerRecord<>(topic, event.getAggregateId(), value);
                SenderRecord<String, String, String> senderRecord =
                    SenderRecord.create(record, event.getEventId());
                return kafkaSender.send(Mono.just(senderRecord))
                    .next()
                    .doOnNext(result -> log.info("Evento enviado a partición {} offset {}",
                        result.recordMetadata().partition(),
                        result.recordMetadata().offset()))
                    .then();
            });
    }

    public Flux<SenderResult<String>> publishBatch(Flux<DomainEvent> events) {
        return kafkaSender.send(
            events.map(event -> {
                String value = serialize(event);
                ProducerRecord<String, String> record =
                    new ProducerRecord<>(topic, event.getAggregateId(), value);
                return SenderRecord.create(record, event.getEventId());
            })
        );
    }
}
```

### Consumer Reactivo con Backpressure

```java
@Component
@RequiredArgsConstructor
public class OrderEventConsumer {
    private final ReceiverOptions<String, String> receiverOptions;
    private final ObjectMapper objectMapper;
    private final IOrderEventHandler eventHandler;

    @Value("${kafka.topic.orders}")
    private String topic;

    @PostConstruct
    public void startConsuming() {
        ReceiverOptions<String, String> options = receiverOptions
            .subscription(Collections.singleton(topic))
            .commitInterval(Duration.ofSeconds(5))
            .commitBatchSize(100);

        KafkaReceiver.create(options)
            .receive()
            .groupBy(record -> record.receiverOffset().topicPartition())
            .flatMap(partitionFlux ->
                partitionFlux
                    .publishOn(Schedulers.boundedElastic())
                    .concatMap(this::processRecord)
            )
            .subscribe();
    }

    private Mono<Void> processRecord(ReceiverRecord<String, String> record) {
        return Mono.fromCallable(() -> objectMapper.readValue(record.value(), DomainEvent.class))
            .flatMap(eventHandler::handle)
            .doOnSuccess(v -> record.receiverOffset().acknowledge())
            .doOnError(e -> log.error("Error procesando mensaje en partición {} offset {}",
                record.partition(), record.offset(), e))
            .onErrorResume(e -> Mono.empty());
    }
}
```

### Reglas Kafka Reactivo

- Usar `KafkaSender` y `KafkaReceiver` de Reactor Kafka (NO `KafkaTemplate`).
- Configurar `enable.auto.commit=false` y usar `acknowledge()` manual.
- Usar `groupBy(topicPartition)` + `concatMap` para orden por partición.
- Implementar backpressure con `publishOn(Schedulers.boundedElastic())`.
- Configurar `commitInterval` y `commitBatchSize` para commits eficientes.

---

## 2. Amazon SQS (SDK Async)

### Dependencias

```groovy
implementation 'software.amazon.awssdk:sqs'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Configuración

```java
@Configuration
public class SqsConfig {
    @Bean
    public SqsAsyncClient sqsAsyncClient() {
        return SqsAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}
```

### Producer Reactivo

```java
@Component
@RequiredArgsConstructor
public class SqsMessageProducer implements ISqsMessageGateway {
    private final SqsAsyncClient sqsAsyncClient;
    private final ObjectMapper objectMapper;

    @Value("${sqs.queue.url}")
    private String queueUrl;

    @Override
    public Mono<String> sendMessage(Object message) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(message))
            .flatMap(body -> Mono.fromFuture(() ->
                sqsAsyncClient.sendMessage(SendMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .messageBody(body)
                    .build())
            ))
            .map(SendMessageResponse::messageId);
    }

    public Flux<String> sendBatch(List<Object> messages) {
        List<SendMessageBatchRequestEntry> entries = new ArrayList<>();
        for (int i = 0; i < messages.size(); i++) {
            entries.add(SendMessageBatchRequestEntry.builder()
                .id(String.valueOf(i))
                .messageBody(serialize(messages.get(i)))
                .build());
        }
        return Mono.fromFuture(() -> sqsAsyncClient.sendMessageBatch(
                SendMessageBatchRequest.builder()
                    .queueUrl(queueUrl)
                    .entries(entries)
                    .build()))
            .flatMapMany(response -> Flux.fromIterable(response.successful()))
            .map(SendMessageBatchResultEntry::messageId);
    }
}
```

### Consumer Reactivo (Polling con Flux)

```java
@Component
@RequiredArgsConstructor
public class SqsMessageConsumer {
    private final SqsAsyncClient sqsAsyncClient;
    private final ObjectMapper objectMapper;
    private final IEventHandler eventHandler;

    @Value("${sqs.queue.url}")
    private String queueUrl;

    @PostConstruct
    public void startPolling() {
        Flux.interval(Duration.ofSeconds(1))
            .flatMap(tick -> pollMessages(), 1)
            .subscribe();
    }

    private Flux<Void> pollMessages() {
        return Mono.fromFuture(() -> sqsAsyncClient.receiveMessage(
                ReceiveMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .maxNumberOfMessages(10)
                    .waitTimeSeconds(20)
                    .visibilityTimeout(30)
                    .build()))
            .flatMapMany(response -> Flux.fromIterable(response.messages()))
            .flatMap(this::processAndDelete);
    }

    private Mono<Void> processAndDelete(Message message) {
        return Mono.fromCallable(() -> objectMapper.readValue(message.body(), DomainEvent.class))
            .flatMap(eventHandler::handle)
            .then(Mono.fromFuture(() -> sqsAsyncClient.deleteMessage(
                DeleteMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .receiptHandle(message.receiptHandle())
                    .build())))
            .then()
            .onErrorResume(e -> {
                log.error("Error procesando mensaje: {}", message.messageId(), e);
                return Mono.empty();
            });
    }
}
```

### Reglas SQS Reactivo

- Usar `SqsAsyncClient` (NO `SqsClient` síncrono).
- Envolver con `Mono.fromFuture()` para integrar con el pipeline reactivo.
- Usar long polling (`waitTimeSeconds=20`) para reducir costos.
- Implementar DLQ para mensajes que fallan repetidamente.
- Configurar visibility timeout mayor que el tiempo de procesamiento.
- Implementar idempotencia en consumidores.

---

## 3. Amazon SNS

### Dependencias

```groovy
implementation 'software.amazon.awssdk:sns'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Publisher Reactivo

```java
@Configuration
public class SnsConfig {
    @Bean
    public SnsAsyncClient snsAsyncClient() {
        return SnsAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}

@Component
@RequiredArgsConstructor
public class SnsPublisher implements ISnsPublishGateway {
    private final SnsAsyncClient snsAsyncClient;
    private final ObjectMapper objectMapper;

    @Value("${sns.topic.arn}")
    private String topicArn;

    @Override
    public Mono<String> publish(DomainEvent event) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(event))
            .flatMap(body -> Mono.fromFuture(() ->
                snsAsyncClient.publish(PublishRequest.builder()
                    .topicArn(topicArn)
                    .message(body)
                    .messageAttributes(Map.of(
                        "eventType", MessageAttributeValue.builder()
                            .dataType("String")
                            .stringValue(event.getEventType())
                            .build()
                    ))
                    .build())
            ))
            .map(PublishResponse::messageId);
    }

    public Mono<String> publishFifo(DomainEvent event, String messageGroupId) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(event))
            .flatMap(body -> Mono.fromFuture(() ->
                snsAsyncClient.publish(PublishRequest.builder()
                    .topicArn(topicArn)
                    .message(body)
                    .messageGroupId(messageGroupId)
                    .messageDeduplicationId(event.getEventId())
                    .build())
            ))
            .map(PublishResponse::messageId);
    }
}
```

### Reglas SNS Reactivo

- Usar `SnsAsyncClient` (NO `SnsClient` síncrono).
- Usar message attributes para filtrado en suscriptores.
- Usar `MessageDeduplicationId` para topics FIFO.
- Considerar Dead Letter Queues para mensajes no procesados.

---

## 4. Amazon EventBridge

### Dependencias

```groovy
implementation 'software.amazon.awssdk:eventbridge'
implementation 'software.amazon.awssdk:netty-nio-client'
```

### Publisher Reactivo

```java
@Configuration
public class EventBridgeConfig {
    @Bean
    public EventBridgeAsyncClient eventBridgeAsyncClient() {
        return EventBridgeAsyncClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}

@Component
@RequiredArgsConstructor
public class EventBridgePublisher implements IEventBridgeGateway {
    private final EventBridgeAsyncClient eventBridgeAsyncClient;
    private final ObjectMapper objectMapper;

    @Value("${eventbridge.bus.name}")
    private String eventBusName;

    @Value("${eventbridge.source}")
    private String source;

    @Override
    public Mono<String> publish(DomainEvent event) {
        return Mono.fromCallable(() -> objectMapper.writeValueAsString(event))
            .flatMap(detail -> {
                PutEventsRequestEntry entry = PutEventsRequestEntry.builder()
                    .eventBusName(eventBusName)
                    .source(source)
                    .detailType(event.getEventType())
                    .detail(detail)
                    .time(Instant.now())
                    .build();

                return Mono.fromFuture(() -> eventBridgeAsyncClient.putEvents(
                    PutEventsRequest.builder().entries(entry).build()));
            })
            .flatMap(response -> {
                if (response.failedEntryCount() > 0) {
                    return Mono.error(new EventPublishException(
                        response.entries().get(0).errorMessage()));
                }
                return Mono.just(response.entries().get(0).eventId());
            });
    }
}
```

### Reglas EventBridge Reactivo

- Usar `EventBridgeAsyncClient` (NO `EventBridgeClient` síncrono).
- Diseñar consumidores idempotentes (eventos pueden duplicarse).
- Particionar batches en grupos de 10 eventos (límite del servicio).
- Validar response para entradas fallidas.
- Tamaño máximo de evento: 256 KB.

---

## 5. Backpressure Handling

### Estrategias de Backpressure

```java
// Limitar concurrencia de procesamiento
kafkaReceiver.receive()
    .flatMap(record -> processRecord(record), 16)  // máximo 16 en paralelo
    .subscribe();

// Buffer con overflow strategy
sqsFlux
    .onBackpressureBuffer(1000, dropped ->
        log.warn("Mensaje descartado por backpressure: {}", dropped))
    .flatMap(this::process)
    .subscribe();

// Rate limiting
eventFlux
    .limitRate(100)  // solicitar de a 100 elementos
    .flatMap(this::process)
    .subscribe();
```

---

## Error Handling Reactivo para Mensajería

```java
@Component
@RequiredArgsConstructor
public class ResilientPublisher {
    private final EventBridgePublisher publisher;

    public Mono<String> publishWithRetry(DomainEvent event) {
        return publisher.publish(event)
            .retryWhen(Retry.backoff(3, Duration.ofMillis(500))
                .maxBackoff(Duration.ofSeconds(5))
                .filter(e -> e instanceof EventBridgeException)
                .doBeforeRetry(signal ->
                    log.warn("Reintentando publicación, intento {}",
                        signal.totalRetries() + 1)));
    }
}
```

---

## Reglas Generales

- Usar clientes **async** de AWS SDK (NO clientes síncronos).
- Envolver `CompletableFuture` con `Mono.fromFuture()`.
- Implementar backpressure para evitar saturación.
- Configurar Dead Letter Queues para mensajes fallidos.
- Implementar idempotencia en todos los consumidores.
- Usar `retryWhen(Retry.backoff(...))` para reintentos reactivos.
- **NUNCA** usar `.block()` en producers ni consumers.
