<!-- keywords: asyncapi, message validation, ajv, event consumer, event producer, schema validation, typescript, nodejs -->
# AsyncAPI - Message Validation in TypeScript

## Purpose

Implementation of AsyncAPI message validation in Node.js/TypeScript using Ajv, applicable to event consumers and producers.

## Reference

Main language-agnostic document: [../asyncapi-standards.md](../asyncapi-standards.md)

## Message Validation

```typescript
// asyncapi-validator.ts
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

const orderCreatedSchema = {
  type: 'object',
  required: ['eventId', 'eventType', 'timestamp', 'data'],
  properties: {
    eventId: { type: 'string', format: 'uuid' },
    eventType: { const: 'OrderCreated' },
    timestamp: { type: 'string', format: 'date-time' },
    data: { $ref: '#/definitions/OrderData' }
  },
  definitions: {
    OrderData: {
      type: 'object',
      required: ['orderId', 'customerId', 'items', 'totalAmount'],
      properties: {
        orderId: { type: 'string' },
        customerId: { type: 'string' },
        items: { type: 'array', items: { $ref: '#/definitions/OrderItem' } },
        totalAmount: { type: 'number', minimum: 0 }
      }
    },
    OrderItem: {
      type: 'object',
      required: ['productId', 'quantity', 'unitPrice'],
      properties: {
        productId: { type: 'string' },
        quantity: { type: 'integer', minimum: 1 },
        unitPrice: { type: 'number', minimum: 0 }
      }
    }
  }
};

const validateOrderCreated = ajv.compile(orderCreatedSchema);

export function validateMessage(message: unknown): { valid: boolean; errors?: string[] } {
  const valid = validateOrderCreated(message);
  if (valid) {
    return { valid: true };
  }
  return {
    valid: false,
    errors: validateOrderCreated.errors?.map(e => `${e.instancePath} ${e.message}`)
  };
}
```

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
