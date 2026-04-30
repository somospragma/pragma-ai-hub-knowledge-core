<!-- keywords: soc2, audit logging, event traceability, dynamodb, kinesis, compliance, typescript, nodejs -->
# SOC2 Audit Logging - TypeScript Implementation

## Purpose

Implement SOC2-compliant audit logging in Node.js/TypeScript using AWS SDK, DynamoDB, and Kinesis for immutable storage.

## Scope of Application

- When developing Node.js systems that require SOC2 certification.
- When audit decorators need to be implemented.
- To configure immutable event storage.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-kinesis": "^3.400.0",
    "@aws-sdk/client-dynamodb": "^3.400.0",
    "uuid": "^9.0.0"
  }
}
```

### Implementation

```typescript
// Audit event model
interface AuditEvent {
  eventId: string;
  timestamp: string;
  eventType: AuditEventType;
  category: AuditCategory;
  actor: Actor;
  resource: Resource;
  action: Action;
  context: AuditContext;
  metadata?: Record<string, unknown>;
}

interface Actor {
  userId: string;
  userType: 'EMPLOYEE' | 'CUSTOMER' | 'SYSTEM' | 'API';
  ipAddress: string;
  sessionId?: string;
}

enum AuditEventType {
  DATA_ACCESS = 'DATA_ACCESS',
  DATA_MODIFICATION = 'DATA_MODIFICATION',
  AUTHENTICATION = 'AUTHENTICATION',
  AUTHORIZATION = 'AUTHORIZATION',
  CONFIGURATION_CHANGE = 'CONFIGURATION_CHANGE'
}
```

```typescript
// Audit service
import { v4 as uuidv4 } from 'uuid';
import { KinesisClient, PutRecordCommand } from '@aws-sdk/client-kinesis';
import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';

export class AuditService {
  private kinesis: KinesisClient;
  private dynamodb: DynamoDBClient;
  private streamName: string;
  private tableName: string;

  constructor(config: { streamName: string; tableName: string }) {
    this.kinesis = new KinesisClient({});
    this.dynamodb = new DynamoDBClient({});
    this.streamName = config.streamName;
    this.tableName = config.tableName;
  }

  async logEvent(params: Omit<AuditEvent, 'eventId' | 'timestamp'>): Promise<void> {
    const event: AuditEvent = {
      eventId: uuidv4(),
      timestamp: new Date().toISOString(),
      ...params
    };

    await Promise.all([
      this.persistToDynamoDB(event),
      this.sendToKinesis(event)
    ]);
  }

  private async persistToDynamoDB(event: AuditEvent): Promise<void> {
    const command = new PutItemCommand({
      TableName: this.tableName,
      Item: {
        pk: { S: `EVENT#${event.eventId}` },
        sk: { S: event.timestamp },
        data: { S: JSON.stringify(event) },
        ttl: { N: String(this.calculateTTL()) }
      },
      ConditionExpression: 'attribute_not_exists(pk)'
    });
    await this.dynamodb.send(command);
  }

  private calculateTTL(): number {
    const sevenYears = 7 * 365 * 24 * 60 * 60;
    return Math.floor(Date.now() / 1000) + sevenYears;
  }
}
```

```typescript
// Decorator for automatic auditing
export function Auditable(config: {
  eventType: AuditEventType;
  resourceType: string;
  actionType: string;
}) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const auditService = (this as any).auditService as AuditService;
      
      try {
        const result = await originalMethod.apply(this, args);
        await auditService.logEvent({
          eventType: config.eventType,
          category: 'SECURITY',
          actor: extractActor(args),
          resource: { type: config.resourceType, id: args[0], name: propertyKey },
          action: { type: config.actionType, status: 'SUCCESS', details: null },
          context: extractContext(args)
        });
        return result;
      } catch (error) {
        await auditService.logEvent({
          eventType: config.eventType,
          category: 'SECURITY',
          actor: extractActor(args),
          resource: { type: config.resourceType, id: args[0], name: propertyKey },
          action: { type: config.actionType, status: 'FAILURE', details: error.message },
          context: extractContext(args)
        });
        throw error;
      }
    };
    return descriptor;
  };
}
```

### Configuration

```typescript
export const auditConfig = {
  streamName: process.env.AUDIT_STREAM_NAME!,
  tableName: process.env.AUDIT_TABLE_NAME!,
  retentionYears: 7
};
```

## Important Rules

- Use `Promise.all` for parallel persistence.
- Implement 7-year TTL for compliance.
- Use `ConditionExpression` for immutability.

## Example

```typescript
class CustomerService {
  @Auditable({ eventType: AuditEventType.DATA_ACCESS, resourceType: 'CUSTOMER', actionType: 'READ' })
  async getCustomer(customerId: string): Promise<Customer> {
    return this.repository.findById(customerId);
  }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
