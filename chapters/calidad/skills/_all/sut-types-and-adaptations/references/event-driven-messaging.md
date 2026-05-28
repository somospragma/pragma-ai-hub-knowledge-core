# Event-Driven Messaging — Patrones y Adaptación

## Patrones canónicos

- **Consumer-driven contract testing**: Pact Messaging permite que el consumer defina los mensajes que espera, y el producer valida que los emita correctamente. Sin esto, los cambios en el producer rompen consumers sin aviso.
- **AsyncAPI**: equivalente a OpenAPI para eventos. Documenta channels, mensajes, schemas, bindings (Kafka, SNS, MQTT, AMQP). Generadores de tests: `asyncapi-validator`, `microcks`.
- **Schema Registry**: Confluent Schema Registry, AWS Glue Schema Registry, Apicurio. Validar **compatibility mode** (`BACKWARD`, `FORWARD`, `FULL`, `NONE`) — un schema FORWARD-compatible nuevo no debe romper consumers viejos.
- **Idempotent consumers**: el mismo mensaje puede llegar más de una vez (at-least-once). El consumer debe deduplicar por `messageId` o por una key de negocio.
- **Exactly-once vs at-least-once**: Kafka soporta exactly-once con transacciones (`enable.idempotence=true`, `transactional.id`). SQS estándar es at-least-once; SQS FIFO con `MessageDeduplicationId` es exactly-once dentro de 5 min.
- **Eventual consistency**: el side-effect ocurre asíncronamente. Los tests deben usar polling con timeout (`eventually` pattern), nunca `sleep` arbitrario.
- **Dead-letter queues (DLQ)**: validar que mensajes inválidos terminen en DLQ y no bloqueen el flujo principal.
- **Ordering**: Kafka ordena por partition key, SQS FIFO por `MessageGroupId`. Validar que mensajes de la misma key se procesen en orden.

## Framework primario

**Pact Messaging** para contratos consumer/producer + tests de integración usando containers de los brokers (Testcontainers Kafka, ElasticMQ para SQS, RabbitMQ image).

## Complementarios

- **k6 con producer plugins** (`xk6-kafka`, `xk6-amqp`, `xk6-sqs`) para perf de producer y consumer lag.
- **Confluent CLI / kcat (kafkacat)** para inspección manual de topics.
- **Microcks** como mock server desde AsyncAPI.
- **Conduktor / AKHQ** para observabilidad de Kafka en QA.

## Patrón canónico: validar eventual consistency

```java
// Pseudocódigo: publicar evento y esperar side-effect en DB
producer.send(orderCreatedEvent);

await().atMost(10, SECONDS).pollInterval(500, MILLIS).until(() -> {
    return orderRepository.findById(orderId).isPresent();
});
```

## Antipatrones

- Usar `sleep(5000)` para esperar el side-effect — frágil, lento, no escala.
- Probar producer y consumer en aislamiento total sin contract — pasan los tests, falla la integración.
- Ignorar el schema registry y publicar Avro/Protobuf serializado a mano — el primer cambio incompatible rompe todo downstream.
- No probar el DLQ — el sistema entra en silent failure cuando llega un mensaje inválido.
- Tratar at-least-once como exactly-once — duplicados en producción que no se ven en QA con bajo volumen.
