<!-- keywords: asyncapi, async api, event-driven api, message schema, channels, operations, message validation, java, asynchronous api documentation -->
# AsyncAPI Design Standards — Java Implementation

## Purpose

Define the standards for documenting asynchronous and event-driven APIs using the AsyncAPI specification, including document structure, message schemas, channels, operations, and message validation in Java.

## Scope of Application

- When documenting event-based APIs
- When designing messaging contracts between services
- When configuring code generation from AsyncAPI
- When implementing message validation in Java
- When publishing event documentation

## Main content

### AsyncAPI Document Structure

```yaml
asyncapi: '2.6.0'
info:
  title: Order Events API
  version: '1.0.0'
  description: |
    Event API for the orders domain.
    Publishes events when orders are created, updated, or completed.
  contact:
    name: Backend team
    email: backend-team@company.com
  license:
    name: Apache 2.0
    url: https://www.apache.org/licenses/LICENSE-2.0

servers:
  production:
    url: kafka.production.company.com:9092
    protocol: kafka
    description: Production MSK cluster
    security:
      - saslScram: []
  development:
    url: localhost:9092
    protocol: kafka
    description: Local Kafka for development

defaultContentType: application/json

channels:
  orders/created:
    description: Channel for order created events
    publish:
      operationId: publishOrderCreated
      summary: Publish order created event
      message:
        $ref: '#/components/messages/OrderCreated'
    subscribe:
      operationId: onOrderCreated
      summary: Receive order created event
      message:
        $ref: '#/components/messages/OrderCreated'

  orders/updated:
    description: Channel for order updated events
    publish:
      operationId: publishOrderUpdated
      message:
        $ref: '#/components/messages/OrderUpdated'
    subscribe:
      operationId: onOrderUpdated
      message:
        $ref: '#/components/messages/OrderUpdated'

  orders/{orderId}/status:
    description: Channel for status changes of a specific order
    parameters:
      orderId:
        description: Unique order identifier
        schema:
          type: string
          format: uuid
    subscribe:
      operationId: onOrderStatusChanged
      message:
        $ref: '#/components/messages/OrderStatusChanged'

components:
  messages:
    OrderCreated:
      name: OrderCreated
      title: Order Created
      summary: Event emitted when a new order is created
      contentType: application/json
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: '#/components/schemas/OrderCreatedPayload'
      examples:
        - name: Standard order
          summary: Example of a standard order created
          payload:
            eventId: "evt-123e4567-e89b-12d3-a456-426614174000"
            eventType: "OrderCreated"
            timestamp: "2024-01-15T10:30:00Z"
            data:
              orderId: "ord-123456"
              customerId: "cust-789"
              items:
                - productId: "prod-001"
                  quantity: 2
                  unitPrice: 29.99
              totalAmount: 59.98
              currency: "USD"

    OrderUpdated:
      name: OrderUpdated
      title: Order Updated
      contentType: application/json
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: '#/components/schemas/OrderUpdatedPayload'

    OrderStatusChanged:
      name: OrderStatusChanged
      title: Order Status Changed
      contentType: application/json
      traits:
        - $ref: '#/components/messageTraits/commonHeaders'
      payload:
        $ref: '#/components/schemas/OrderStatusChangedPayload'

  schemas:
    OrderCreatedPayload:
      type: object
      required:
        - eventId
        - eventType
        - timestamp
        - data
      properties:
        eventId:
          type: string
          format: uuid
          description: Unique event identifier
        eventType:
          type: string
          const: OrderCreated
        timestamp:
          type: string
          format: date-time
        correlationId:
          type: string
          description: ID for traceability
        data:
          $ref: '#/components/schemas/OrderData'

    OrderData:
      type: object
      required:
        - orderId
        - customerId
        - items
        - totalAmount
        - currency
      properties:
        orderId:
          type: string
        customerId:
          type: string
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
        totalAmount:
          type: number
          format: decimal
          minimum: 0
        currency:
          type: string
          pattern: '^[A-Z]{3}$'
          example: USD
        status:
          $ref: '#/components/schemas/OrderStatus'

    OrderItem:
      type: object
      required:
        - productId
        - quantity
        - unitPrice
      properties:
        productId:
          type: string
        quantity:
          type: integer
          minimum: 1
        unitPrice:
          type: number
          format: decimal
          minimum: 0

    OrderStatus:
      type: string
      enum:
        - PENDING
        - CONFIRMED
        - PROCESSING
        - SHIPPED
        - DELIVERED
        - CANCELLED

    OrderUpdatedPayload:
      type: object
      required:
        - eventId
        - eventType
        - timestamp
        - data
      properties:
        eventId:
          type: string
          format: uuid
        eventType:
          type: string
          const: OrderUpdated
        timestamp:
          type: string
          format: date-time
        data:
          type: object
          properties:
            orderId:
              type: string
            changes:
              type: object
              additionalProperties: true
            previousValues:
              type: object
              additionalProperties: true

    OrderStatusChangedPayload:
      type: object
      required:
        - eventId
        - eventType
        - timestamp
        - data
      properties:
        eventId:
          type: string
          format: uuid
        eventType:
          type: string
          const: OrderStatusChanged
        timestamp:
          type: string
          format: date-time
        data:
          type: object
          required:
            - orderId
            - previousStatus
            - newStatus
          properties:
            orderId:
              type: string
            previousStatus:
              $ref: '#/components/schemas/OrderStatus'
            newStatus:
              $ref: '#/components/schemas/OrderStatus'
            reason:
              type: string

  messageTraits:
    commonHeaders:
      headers:
        type: object
        properties:
          correlationId:
            type: string
            description: Correlation ID for traceability
          messageId:
            type: string
            format: uuid
          timestamp:
            type: string
            format: date-time
          source:
            type: string
            description: Service that originated the event
          version:
            type: string
            description: Message schema version

  securitySchemes:
    saslScram:
      type: scramSha256
      description: SASL/SCRAM-SHA-256 authentication
    apiKey:
      type: apiKey
      in: user
      description: API Key for authentication
```

### Domain Event with CloudEvents

```yaml
components:
  schemas:
    CloudEventEnvelope:
      type: object
      required:
        - specversion
        - id
        - source
        - type
        - time
        - data
      properties:
        specversion:
          type: string
          const: "1.0"
        id:
          type: string
          format: uuid
        source:
          type: string
          format: uri
          example: "/orders/order-service"
        type:
          type: string
          example: "com.company.orders.OrderCreated"
        time:
          type: string
          format: date-time
        datacontenttype:
          type: string
          default: "application/json"
        data:
          type: object
```

### Message Validation in Java

```java
// AsyncApiValidator.java
@Component
public class AsyncApiValidator {

    private final JsonSchema orderCreatedSchema;

    public AsyncApiValidator() {
        JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
        this.orderCreatedSchema = factory.getSchema(
            getClass().getResourceAsStream("/schemas/order-created.json")
        );
    }

    public ValidationResult validate(String message, String eventType) {
        try {
            JsonNode jsonNode = objectMapper.readTree(message);
            Set<ValidationMessage> errors = getSchemaFor(eventType).validate(jsonNode);

            if (errors.isEmpty()) {
                return ValidationResult.valid();
            }
            return ValidationResult.invalid(errors);
        } catch (Exception e) {
            return ValidationResult.invalid(e.getMessage());
        }
    }
}
```

## Important Rules

1. **Versioning**: Include version in info and in message schemas
2. **Examples**: Provide examples for each message
3. **Description**: Document the purpose of channels and messages
4. **Headers**: Define common headers as reusable traits
5. **Security**: Specify authentication mechanisms
6. **Validation**: Implement runtime schema validation with JSON Schema in Java
7. **Evolution**: Use additionalProperties for extensibility

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
