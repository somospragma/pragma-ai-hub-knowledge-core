---
id: backend-skill-java-spring-integraciones-mensajeria
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: java-spring
---

# Integraciones con Servicios de Mensajería — Java Spring

## Propósito

Documentar la integración con Kafka/MSK, SQS, SNS y EventBridge en microservicios Java Spring Boot MVC: configuración, producer/consumer, serialización, error handling y dead letter queues.

---

## 1. Apache Kafka / Amazon MSK

### Dependencias

```groovy
implementation 'org.springframework.kafka:spring-kafka'
```

### Configuración

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
        props.put(ProducerConfig.RETRIES_CONFIG, 3);
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
```

### Producer

```java
@Component
@RequiredArgsConstructor
public class OrderEventProducer {
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final ObjectMapper objectMapper;

    @Value("${kafka.topic.orders}")
    private String topic;

    public void publish(DomainEvent event) {
        try {
            String value = objectMapper.writeValueAsString(event);
            kafkaTemplate.send(topic, event.getAggregateId(), value)
                .whenComplete((result, ex) -> {
                    if (ex != null) {
                        log.error("Error publicando evento: {}", ex.getMessage());
                    } else {
                        log.info("Evento enviado a partición {} offset {}",
                            result.getRecordMetadata().partition(),
                            result.getRecordMetadata().offset());
                    }
                });
        } catch (JsonProcessingException e) {
            throw new EventSerializationException("Error serializando evento", e);
        }
    }
}
```

### Consumer

```java
@Component
@RequiredArgsConstructor
public class OrderEventListener {
    private final ObjectMapper objectMapper;
    private final OrderEventHandler eventHandler;

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
            log.error("Error procesando mensaje en partición {} offset {}", partition, offset, e);
            // El mensaje irá al DLQ después de los reintentos configurados
        }
    }
}
```

### Reglas Kafka

- Usar key consistente para garantizar orden por partición.
- Configurar `enable.idempotence=true` para exactly-once.
- Usar `acks=all` para máxima durabilidad.
- Implementar commits manuales para control fino.
- Configurar autenticación IAM o SASL para MSK.

---

## 2. Amazon SQS

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
    public SqsClient sqsClient() {
        return SqsClient.builder()
            .region(Region.of(System.getenv("AWS_REGION")))
            .build();
    }
}
```

### Producer

```java
@Component
@RequiredArgsConstructor
public class SqsMessageProducer {
    private final SqsClient sqsClient;
    private final ObjectMapper objectMapper;

    @Value("${sqs.queue.url}")
    private String queueUrl;

    public String sendMessage(Object message) {
        try {
            String body = objectMapper.writeValueAsString(message);
            SendMessageResponse response = sqsClient.sendMessage(
                SendMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .messageBody(body)
                    .build());
            return response.messageId();
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Error serializando mensaje", e);
        }
    }

    public void sendBatch(List<Object> messages) {
        List<SendMessageBatchRequestEntry> entries = new ArrayList<>();
        for (int i = 0; i < messages.size(); i++) {
            entries.add(SendMessageBatchRequestEntry.builder()
                .id(String.valueOf(i))
                .messageBody(serialize(messages.get(i)))
                .build());
        }
        sqsClient.sendMessageBatch(SendMessageBatchRequest.builder()
            .queueUrl(queueUrl)
            .entries(entries)
            .build());
    }
}
```

### Consumer (Polling)

```java
@Component
@RequiredArgsConstructor
public class SqsMessageConsumer {
    private final SqsClient sqsClient;
    private final ObjectMapper objectMapper;
    private final EventHandler eventHandler;

    @Value("${sqs.queue.url}")
    private String queueUrl;

    @Scheduled(fixedDelay = 1000)
    public void pollMessages() {
        ReceiveMessageResponse response = sqsClient.receiveMessage(
            ReceiveMessageRequest.builder()
                .queueUrl(queueUrl)
                .maxNumberOfMessages(10)
                .waitTimeSeconds(20)
                .visibilityTimeout(30)
                .build());

        for (Message message : response.messages()) {
            try {
                DomainEvent event = objectMapper.readValue(message.body(), DomainEvent.class);
                eventHandler.handle(event);
                sqsClient.deleteMessage(DeleteMessageRequest.builder()
                    .queueUrl(queueUrl)
                    .receiptHandle(message.receiptHandle())
                    .build());
            } catch (Exception e) {
                log.error("Error procesando mensaje: {}", message.messageId(), e);
            }
        }
    }
}
```

### Reglas SQS

- Usar FIFO solo cuando el orden es crítico.
- Implementar DLQ para mensajes que fallan repetidamente.
- Configurar visibility timeout mayor que el tiempo de procesamiento.
- Usar batch operations para mejor throughput (máximo 10 mensajes).
- Implementar idempotencia en consumidores.
- Usar long polling (`waitTimeSeconds=20`) para reducir costos.

---

## 3. Amazon SNS

### Dependencias

```groovy
implementation 'software.amazon.awssdk:sns'
```

### Configuración y Publisher

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
@RequiredArgsConstructor
public class SnsPublisher {
    private final SnsClient snsClient;
    private final ObjectMapper objectMapper;

    @Value("${sns.topic.arn}")
    private String topicArn;

    public String publish(DomainEvent event) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(serialize(event))
            .messageAttributes(Map.of(
                "eventType", MessageAttributeValue.builder()
                    .dataType("String")
                    .stringValue(event.getEventType())
                    .build(),
                "source", MessageAttributeValue.builder()
                    .dataType("String")
                    .stringValue(event.getSource())
                    .build()
            ))
            .build();

        PublishResponse response = snsClient.publish(request);
        return response.messageId();
    }

    public String publishFifo(DomainEvent event, String messageGroupId) {
        PublishRequest request = PublishRequest.builder()
            .topicArn(topicArn)
            .message(serialize(event))
            .messageGroupId(messageGroupId)
            .messageDeduplicationId(event.getEventId())
            .build();
        return snsClient.publish(request).messageId();
    }
}
```

### Reglas SNS

- Usar message attributes para filtrado en suscriptores.
- Configurar filtros en suscriptores para reducir costos.
- Usar `MessageDeduplicationId` para topics FIFO.
- Considerar Dead Letter Queues para mensajes no procesados.

---

## 4. Amazon EventBridge

### Dependencias

```groovy
implementation 'software.amazon.awssdk:eventbridge'
```

### Configuración y Publisher

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
@RequiredArgsConstructor
public class EventBridgePublisher {
    private final EventBridgeClient eventBridgeClient;
    private final ObjectMapper objectMapper;

    @Value("${eventbridge.bus.name}")
    private String eventBusName;

    @Value("${eventbridge.source}")
    private String source;

    public String publish(DomainEvent event) {
        PutEventsRequestEntry entry = PutEventsRequestEntry.builder()
            .eventBusName(eventBusName)
            .source(source)
            .detailType(event.getEventType())
            .detail(serialize(event))
            .time(Instant.now())
            .build();

        PutEventsResponse response = eventBridgeClient.putEvents(
            PutEventsRequest.builder().entries(entry).build());

        if (response.failedEntryCount() > 0) {
            throw new EventPublishException(
                response.entries().get(0).errorMessage());
        }
        return response.entries().get(0).eventId();
    }
}
```

### Estructura del Evento

```json
{
  "version": "0",
  "detail-type": "OrderCreated",
  "source": "com.pragma.orders",
  "detail": {
    "eventId": "evt-123",
    "aggregateId": "order-123",
    "payload": { "customerId": "cust-456", "amount": 100.00 }
  }
}
```

### Reglas EventBridge

- Diseñar consumidores idempotentes (eventos pueden duplicarse).
- Configurar Dead Letter Queues para eventos fallidos.
- Particionar batches en grupos de 10 eventos (límite del servicio).
- Validar response para entradas fallidas.
- Usar buses personalizados para separar dominios.
- Tamaño máximo de evento: 256 KB.

---

## Error Handling General para Mensajería

```java
@Component
@RequiredArgsConstructor
public class ResilientPublisher {
    private final EventBridgePublisher publisher;

    public String publishWithRetry(DomainEvent event) {
        int attempts = 0;
        int maxRetries = 3;
        while (attempts < maxRetries) {
            try {
                return publisher.publish(event);
            } catch (EventBridgeException e) {
                attempts++;
                if (attempts >= maxRetries) throw e;
                try {
                    Thread.sleep((long) Math.pow(2, attempts) * 100);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(ie);
                }
            }
        }
        throw new EventPublishException("Falló después de " + maxRetries + " intentos");
    }
}
```
