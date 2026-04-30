<!-- keywords: eventbridge, aws, event-driven, sdk v3, typescript, nodejs -->
# Amazon EventBridge Integration - TypeScript

## Purpose

Implement integration with Amazon EventBridge in TypeScript/Node.js projects using AWS SDK v3.

## Scope of Application

- TypeScript projects that require publishing events to EventBridge
- Lambdas that publish domain events
- Implementation of handlers for EventBridge rules

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-eventbridge": "^3.x.x"
  },
  "devDependencies": {
    "@types/aws-lambda": "^8.x.x"
  }
}
```

```bash
npm install @aws-sdk/client-eventbridge
npm install -D @types/aws-lambda
```

### EventBridge Client

```typescript
import { 
  EventBridgeClient, 
  PutEventsCommand,
  PutEventsRequestEntry 
} from '@aws-sdk/client-eventbridge';

interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  version: number;
  payload: Record<string, unknown>;
  resources?: string[];
  metadata?: Record<string, string>;
}

interface PublishResult {
  eventId?: string;
  success: boolean;
  errorCode?: string;
  errorMessage?: string;
}

class EventBridgePublisher {
  private client: EventBridgeClient;
  private eventBusName: string;
  private source: string;
  
  constructor(eventBusName: string, source: string) {
    this.client = new EventBridgeClient({
      region: process.env.AWS_REGION
    });
    this.eventBusName = eventBusName;
    this.source = source;
  }
  
  async publish(event: DomainEvent): Promise<string> {
    const entry = this.buildEntry(event);
    
    const command = new PutEventsCommand({
      Entries: [entry]
    });
    
    const response = await this.client.send(command);
    
    if (response.FailedEntryCount && response.FailedEntryCount > 0) {
      const failed = response.Entries![0];
      throw new Error(
        `Failed to publish: ${failed.ErrorCode} - ${failed.ErrorMessage}`
      );
    }
    
    return response.Entries![0].EventId!;
  }
  
  async publishBatch(events: DomainEvent[]): Promise<PublishResult[]> {
    const results: PublishResult[] = [];
    
    for (let i = 0; i < events.length; i += 10) {
      const batch = events.slice(i, i + 10);
      const entries = batch.map(event => this.buildEntry(event));
      
      const command = new PutEventsCommand({
        Entries: entries
      });
      
      const response = await this.client.send(command);
      
      response.Entries?.forEach(entry => {
        if (entry.EventId) {
          results.push({ eventId: entry.EventId, success: true });
        } else {
          results.push({
            success: false,
            errorCode: entry.ErrorCode,
            errorMessage: entry.ErrorMessage
          });
        }
      });
    }
    
    return results;
  }
  
  private buildEntry(event: DomainEvent): PutEventsRequestEntry {
    return {
      EventBusName: this.eventBusName,
      Source: this.source,
      DetailType: event.eventType,
      Detail: JSON.stringify(event),
      Time: new Date(),
      Resources: event.resources
    };
  }
}

export { EventBridgePublisher, DomainEvent, PublishResult };
```

### Handler for EventBridge rules

```typescript
import { EventBridgeEvent, Handler } from 'aws-lambda';

interface OrderPayload {
  orderId: string;
  customerId: string;
  amount: number;
  orderType: string;
}

interface OrderEvent extends DomainEvent {
  payload: OrderPayload;
}

export const handler: Handler<EventBridgeEvent<string, OrderEvent>> = async (
  event
): Promise<void> => {
  console.log('Received event:', {
    source: event.source,
    detailType: event['detail-type'],
    eventId: event.id
  });
  
  const domainEvent = event.detail;
  
  switch (event['detail-type']) {
    case 'OrderCreated':
      await handleOrderCreated(domainEvent);
      break;
    case 'PaymentProcessed':
      await handlePaymentProcessed(domainEvent);
      break;
    default:
      console.log('Unknown event type:', event['detail-type']);
  }
};

async function handleOrderCreated(event: OrderEvent): Promise<void> {
  console.log('Processing order:', event.payload.orderId);
  // Business logic
}

async function handlePaymentProcessed(event: OrderEvent): Promise<void> {
  console.log('Processing payment for order:', event.payload.orderId);
  // Business logic
}
```

### Error handling

```typescript
import { EventBridgeServiceException } from '@aws-sdk/client-eventbridge';

async function publishWithRetry(
  publisher: EventBridgePublisher,
  event: DomainEvent,
  maxRetries: number = 3
): Promise<string> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await publisher.publish(event);
    } catch (error) {
      lastError = error as Error;
      
      if (error instanceof EventBridgeServiceException) {
        if (error.$retryable) {
          const delay = Math.pow(2, attempt) * 100;
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }
      throw error;
    }
  }
  
  throw lastError;
}
```

## Important Rules

- Reuse `EventBridgeClient` instance between Lambda invocations
- Partition batches into groups of maximum 10 events
- Implement retry with exponential backoff
- Validate `EventId` in successful responses
- Use strict types for domain events

## Example

```typescript
// Usage in Lambda
const publisher = new EventBridgePublisher(
  process.env.EVENT_BUS_NAME!,
  'com.company.orders'
);

export const handler = async (
  event: APIGatewayEvent
): Promise<APIGatewayProxyResult> => {
  const order = JSON.parse(event.body!);
  
  const domainEvent: DomainEvent = {
    eventId: crypto.randomUUID(),
    eventType: 'OrderCreated',
    aggregateId: order.id,
    aggregateType: 'Order',
    version: 1,
    payload: order,
    resources: [`arn:aws:orders:${order.id}`]
  };
  
  const eventId = await publisher.publish(domainEvent);
  
  return {
    statusCode: 200,
    body: JSON.stringify({ eventId })
  };
};
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
