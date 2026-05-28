# AsyncAPI y Pact Messaging — Contratos para Eventos Asíncronos

Pact HTTP y SCC asumen request/response síncrono. Para arquitecturas event-driven (Kafka, RabbitMQ, SNS/SQS, EventBridge), el modelo cambia: el "contrato" es la **estructura del mensaje**, no una interacción.

## Dos enfoques

### 1. AsyncAPI — equivalente a OpenAPI pero para eventos

[AsyncAPI](https://www.asyncapi.com/) es una especificación que describe topics, channels, mensajes y operations. Versión actual: 3.0.

```yaml
# asyncapi.yaml
asyncapi: 3.0.0
info:
  title: Users Events API
  version: 1.0.0

servers:
  production:
    host: kafka.cliente.com:9092
    protocol: kafka

channels:
  userCreated:
    address: users.events.created
    messages:
      userCreatedEvent:
        $ref: '#/components/messages/UserCreated'

operations:
  publishUserCreated:
    action: send
    channel:
      $ref: '#/channels/userCreated'

components:
  messages:
    UserCreated:
      payload:
        type: object
        required: [eventId, userId, email, createdAt]
        properties:
          eventId:
            type: string
            format: uuid
          userId:
            type: integer
          email:
            type: string
            format: email
          createdAt:
            type: string
            format: date-time
```

**Detección de breaking changes:** usar `asyncapi-diff` (similar a oasdiff):

```bash
npm i -g @asyncapi/diff
asyncapi-diff base.yaml new.yaml --output json
```

CI gate:
```yaml
- run: |
    asyncapi-diff base.yaml asyncapi.yaml --output json > diff.json
    BREAKING=$(jq '[.[] | select(.type == "breaking")] | length' diff.json)
    [ "$BREAKING" -eq 0 ] || exit 1
```

### 2. Pact Messaging — CDC para eventos

Pact soporta el patrón "message pact": el consumer declara qué mensajes espera consumir; el provider verifica que los publica con la estructura esperada.

```typescript
// Consumer test
import { MessageConsumerPact, Matchers } from '@pact-foundation/pact';

const { like, integer, iso8601DateTime, uuid } = Matchers;

const messagePact = new MessageConsumerPact({
  consumer: 'notifications-service',
  provider: 'users-service-messaging',
  dir: './pacts',
});

describe('UserCreated event consumer', () => {
  it('handles UserCreated event', async () => {
    await messagePact
      .given('a user was created')
      .expectsToReceive('a UserCreated event')
      .withContent({
        eventId: uuid(),
        userId: integer(42),
        email: like('alice@example.com'),
        createdAt: iso8601DateTime(),
      })
      .withMetadata({
        'content-type': 'application/json',
        'topic': 'users.events.created',
      })
      .verify(async (message) => {
        // Handler real del consumer
        const result = await handleUserCreated(message.contents);
        expect(result.notificationSent).toBe(true);
      });
  });
});
```

```java
// Provider verification (Java)
@Provider("users-service-messaging")
@PactBroker
class UserEventsProviderTest {

    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verify(PactVerificationContext context) {
        context.verifyInteraction();
    }

    @PactVerifyProvider("a UserCreated event")
    public MessageAndMetadata userCreatedEvent() {
        UserCreatedEvent event = new UserCreatedEvent(
            UUID.randomUUID().toString(),
            42L,
            "alice@example.com",
            Instant.now()
        );

        Map<String, Object> metadata = Map.of(
            "content-type", "application/json",
            "topic", "users.events.created"
        );

        return new MessageAndMetadata(toJson(event).getBytes(), metadata);
    }
}
```

## Cuándo usar cada enfoque

| Criterio                              | AsyncAPI          | Pact Messaging          |
| ------------------------------------- | ----------------- | ----------------------- |
| Spec compartida y documentación       | Excelente         | Limitada                |
| Consumers desconocidos / externos     | Si (es spec)      | No                      |
| Per-consumer contract verification    | No                | Si                      |
| Generación de codigo (typed clients)  | Si (asyncapi-gen) | No                      |
| Gate can-i-deploy                     | No nativo         | Si (via broker)         |
| Multi-broker (Kafka, RabbitMQ, etc.)  | Si                | Si                      |
| Curva de aprendizaje                  | Baja-Media        | Media-Alta              |

**Recomendación Pragma:**
- **AsyncAPI** como source of truth de la topología event-driven + documentación.
- **Pact Messaging** para los consumers críticos que necesitan gate per-consumer.
- Combinar ambos en sistemas event-driven críticos (procesamiento de transacciones financieras, plataformas streaming de eventos en vivo, sistemas de pago, healthcare HL7/FHIR eventos para integración web/mobile).

## Schema Registry como alternativa (Kafka específico)

Si el cliente usa Kafka, **Confluent Schema Registry** con Avro/Protobuf/JSON Schema valida la estructura del mensaje en **producer** y **consumer** en runtime. Ver `schema-registry-confluent.md`.

Schema Registry NO es contract testing puro — es validación runtime. Pero combinado con compatibility modes (BACKWARD, FORWARD, FULL), garantiza que un schema nuevo no rompa consumers existentes.

**Stack recomendado para Kafka:**
- Schema Registry (Avro/Proto) para validación runtime + compatibility check.
- AsyncAPI para documentación.
- Pact Messaging opcional para consumers que necesitan gate per-consumer.

## Anti-patterns

- Usar Pact HTTP para eventos asíncronos — el modelo request/response no aplica.
- AsyncAPI sin schema validation en runtime — el spec se desincroniza de la realidad.
- Schema Registry sin compatibility mode — cualquier cambio se acepta y rompe consumers.
- Eventos sin `eventId` o `correlationId` — imposible de trazar entre servicios.
- No versionar el topic/channel — breaking changes obligan a coordinar deploy de todos los consumers al mismo tiempo.

## Cross-link

- Para Kafka específico, ver `schema-registry-confluent.md`.
- Para integración con suite Karate (validación de eventos consumidos), usar Karate KafkaSteps + match schema; documentado en docs Karate de la chapter.
