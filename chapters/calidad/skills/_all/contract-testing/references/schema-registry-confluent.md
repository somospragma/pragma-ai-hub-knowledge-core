# Confluent Schema Registry — Contratos en Kafka

Para arquitecturas Kafka, **Confluent Schema Registry** centraliza los schemas (Avro, Protobuf, JSON Schema) usados por topics. Garantiza que producers y consumers hablen el mismo lenguaje y permite evolución controlada.

## Componentes

- **Subject**: identificador único por topic (típicamente `<topic>-value` y `<topic>-key`).
- **Schema**: definición Avro/Proto/JSON Schema versionada por subject.
- **Compatibility mode**: regla que rige qué cambios se aceptan al registrar una nueva versión.

## Compatibility modes

| Modo                       | Permite cambio                                                       | Use case                                                  |
| -------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------- |
| `BACKWARD`                 | Consumers nuevos pueden leer datos viejos                            | Default. Upgrade consumers primero, luego producers.      |
| `BACKWARD_TRANSITIVE`      | Igual + chequea contra TODAS las versiones anteriores                | Compliance estricto.                                      |
| `FORWARD`                  | Consumers viejos pueden leer datos nuevos                            | Upgrade producers primero, luego consumers.               |
| `FORWARD_TRANSITIVE`       | Igual + todas las versiones                                          | Compliance estricto.                                      |
| `FULL`                     | Ambos: nuevos leen viejos Y viejos leen nuevos                       | Deploys descoordinados.                                   |
| `FULL_TRANSITIVE`          | Igual + todas las versiones                                          | Máxima seguridad, mínima flexibilidad.                    |
| `NONE`                     | Cualquier cambio                                                     | NUNCA en produccion. Solo experimentación.                |

**Recomendación Pragma:** `BACKWARD` por defecto. `FULL` para topics mission-critical donde no se puede coordinar deploy de N consumers (procesamiento financiero, telemetría safety-critical, plataformas multi-tenant con SLAs contractuales).

## Configurar compatibility mode

```bash
# Global default
curl -X PUT http://schema-registry:8081/config \
  -H "Content-Type: application/json" \
  -d '{"compatibility": "BACKWARD"}'

# Por subject específico
curl -X PUT http://schema-registry:8081/config/users.events.created-value \
  -H "Content-Type: application/json" \
  -d '{"compatibility": "FULL"}'
```

## Cambios permitidos por modo (Avro)

| Cambio                                     | BACKWARD | FORWARD | FULL |
| ------------------------------------------ | -------- | ------- | ---- |
| Agregar campo opcional (con default)       | Si       | Si      | Si   |
| Agregar campo requerido (sin default)      | NO       | NO      | NO   |
| Eliminar campo opcional                    | NO       | Si      | NO   |
| Eliminar campo requerido                   | NO       | Si      | NO   |
| Cambiar tipo de campo                      | NO       | NO      | NO   |
| Renombrar campo (sin alias)                | NO       | NO      | NO   |
| Renombrar campo (con alias)                | Si       | NO      | NO   |
| Agregar enum value                         | Si       | NO      | NO   |
| Eliminar enum value                        | NO       | Si      | NO   |

## Validación en CI antes de publicar producer

Antes de que un producer publique mensajes con un schema nuevo, validar contra el Schema Registry:

```bash
# Usando confluent CLI
confluent schema-registry schema validate \
  --subject users.events.created-value \
  --schema avro/UserCreated.avsc

# Output: Schema is compatible with the latest version
```

CI step:

```yaml
- name: Validate schema compatibility
  run: |
    RESPONSE=$(curl -s -X POST \
      -H "Content-Type: application/vnd.schemaregistry.v1+json" \
      --data @<(jq -n --arg schema "$(cat avro/UserCreated.avsc)" '{schema: $schema}') \
      "$SCHEMA_REGISTRY_URL/compatibility/subjects/users.events.created-value/versions/latest")

    IS_COMPAT=$(echo $RESPONSE | jq -r '.is_compatible')
    if [ "$IS_COMPAT" != "true" ]; then
      echo "FAIL: schema incompatible"
      echo $RESPONSE | jq
      exit 1
    fi
```

## Snippet kafka-avro-console-producer test

Para validar end-to-end que el producer respeta el schema:

```bash
kafka-avro-console-producer \
  --broker-list kafka:9092 \
  --topic users.events.created \
  --property schema.registry.url=http://schema-registry:8081 \
  --property value.schema='{"type":"record","name":"UserCreated","fields":[{"name":"eventId","type":"string"},{"name":"userId","type":"long"},{"name":"email","type":"string"},{"name":"createdAt","type":"long","logicalType":"timestamp-millis"}]}'

# Pega un mensaje JSON
{"eventId":"abc-123","userId":42,"email":"alice@example.com","createdAt":1735689600000}
```

Si el mensaje no respeta el schema, falla con `SerializationException`.

## Avro vs Protobuf vs JSON Schema

| Formato      | Pros                                                | Contras                              | Use case                       |
| ------------ | --------------------------------------------------- | ------------------------------------ | ------------------------------ |
| **Avro**     | Compacto, schema embebido, soporte oficial Confluent| Curva de aprendizaje, GenRec verboso | Default Confluent              |
| **Protobuf** | Muy compacto, gRPC-friendly, typed clients          | Setup más complejo                   | Polyglot, alto throughput      |
| **JSON Schema**| Human-readable, web-friendly                       | Más grande, menos performance        | Compatibilidad con web/HTTP    |

**Recomendación Pragma:** Avro como default; Protobuf si el cliente ya usa gRPC; JSON Schema solo para integraciones con APIs HTTP existentes.

## Integración con consumers en tests

```java
// Karate o JUnit consumer test contra Schema Registry
Properties props = new Properties();
props.put("bootstrap.servers", "kafka:9092");
props.put("schema.registry.url", "http://schema-registry:8081");
props.put("key.deserializer", "io.confluent.kafka.serializers.KafkaAvroDeserializer");
props.put("value.deserializer", "io.confluent.kafka.serializers.KafkaAvroDeserializer");
props.put("specific.avro.reader", "true");
props.put("group.id", "test-consumer");

KafkaConsumer<String, UserCreated> consumer = new KafkaConsumer<>(props);
consumer.subscribe(List.of("users.events.created"));
ConsumerRecords<String, UserCreated> records = consumer.poll(Duration.ofSeconds(5));

assertFalse(records.isEmpty());
UserCreated event = records.iterator().next().value();
assertEquals(42L, event.getUserId());
```

## Anti-patterns

- Compatibility mode `NONE` en producción — cualquier cambio se acepta sin validar.
- Schema Registry sin auth — cualquiera puede registrar schemas (especialmente con `NONE` mode).
- No versionar los `.avsc`/`.proto` en Git junto al código del producer.
- Producir mensajes sin schema (RAW JSON en topics Avro) — rompe consumers tipados.
- Eliminar topics sin validar consumers activos — Schema Registry NO valida consumer presence.

## Cross-link

- Para detección de breaking changes complementaria, ver `openapi-diff-breaking-changes.md`.
- Para validación de contrato por consumer (en lugar de runtime), combinar con `asyncapi-event-contracts.md` (Pact Messaging).
