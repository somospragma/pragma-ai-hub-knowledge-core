<!-- keywords: sns, aws, pub/sub, notification, sdk v3, typescript, nodejs -->
# Amazon SNS Integration - TypeScript

## Purpose

Implement integration with Amazon SNS in TypeScript/Node.js projects using AWS SDK v3.

## Scope of Application

- TypeScript projects that require publishing messages to SNS
- Lambdas that publish events to SNS topics
- Implementation of handlers for SNS subscriptions

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-sns": "^3.x.x"
  },
  "devDependencies": {
    "@types/aws-lambda": "^8.x.x"
  }
}
```

```bash
npm install @aws-sdk/client-sns
npm install -D @types/aws-lambda
```

### SNS Client

```typescript
import { 
  SNSClient, 
  PublishCommand, 
  PublishBatchCommand,
  MessageAttributeValue 
} from '@aws-sdk/client-sns';

interface DomainEvent {
  eventId: string;
  eventType: string;
  source: string;
  version: number;
  payload: Record<string, unknown>;
  timestamp: string;
}

interface PublishResult {
  messageId: string;
  success: boolean;
}

class SnsPublisher {
  private client: SNSClient;
  private topicArn: string;
  
  constructor(topicArn: string) {
    this.client = new SNSClient({
      region: process.env.AWS_REGION
    });
    this.topicArn = topicArn;
  }
  
  async publish(event: DomainEvent): Promise<string> {
    const command = new PublishCommand({
      TopicArn: this.topicArn,
      Message: JSON.stringify(event),
      MessageAttributes: this.buildAttributes(event)
    });
    
    const response = await this.client.send(command);
    return response.MessageId!;
  }
  
  async publishBatch(events: DomainEvent[]): Promise<PublishResult[]> {
    const results: PublishResult[] = [];
    
    for (let i = 0; i < events.length; i += 10) {
      const batch = events.slice(i, i + 10);
      
      const command = new PublishBatchCommand({
        TopicArn: this.topicArn,
        PublishBatchRequestEntries: batch.map((event, index) => ({
          Id: `${i + index}`,
          Message: JSON.stringify(event),
          MessageAttributes: this.buildAttributes(event)
        }))
      });
      
      const response = await this.client.send(command);
      
      response.Successful?.forEach(entry => {
        results.push({ messageId: entry.MessageId!, success: true });
      });
      
      response.Failed?.forEach(entry => {
        console.error(`Failed to publish: ${entry.Code} - ${entry.Message}`);
        results.push({ messageId: entry.Id!, success: false });
      });
    }
    
    return results;
  }
  
  async publishFifo(
    event: DomainEvent, 
    messageGroupId: string
  ): Promise<string> {
    const command = new PublishCommand({
      TopicArn: this.topicArn,
      Message: JSON.stringify(event),
      MessageGroupId: messageGroupId,
      MessageDeduplicationId: event.eventId,
      MessageAttributes: this.buildAttributes(event)
    });
    
    const response = await this.client.send(command);
    return response.MessageId!;
  }
  
  private buildAttributes(
    event: DomainEvent
  ): Record<string, MessageAttributeValue> {
    return {
      eventType: {
        DataType: 'String',
        StringValue: event.eventType
      },
      source: {
        DataType: 'String',
        StringValue: event.source
      },
      version: {
        DataType: 'Number',
        StringValue: String(event.version)
      }
    };
  }
}

export { SnsPublisher, DomainEvent, PublishResult };
```

### Handler for SNS subscription

```typescript
import { SNSEvent, SNSHandler } from 'aws-lambda';

interface OrderEvent {
  eventId: string;
  eventType: string;
  payload: {
    orderId: string;
    customerId: string;
    amount: number;
  };
}

export const handler: SNSHandler = async (event: SNSEvent): Promise<void> => {
  for (const record of event.Records) {
    const message = JSON.parse(record.Sns.Message) as OrderEvent;
    const attributes = record.Sns.MessageAttributes;
    
    console.log('Processing event:', {
      eventType: attributes.eventType?.Value,
      messageId: record.Sns.MessageId
    });
    
    await processEvent(message);
  }
};

async function processEvent(event: OrderEvent): Promise<void> {
  switch (event.eventType) {
    case 'ORDER_CREATED':
      await handleOrderCreated(event.payload);
      break;
    case 'ORDER_UPDATED':
      await handleOrderUpdated(event.payload);
      break;
    default:
      console.log('Unknown event type:', event.eventType);
  }
}
```

### Error handling

```typescript
import { SNSServiceException } from '@aws-sdk/client-sns';

async function publishWithRetry(
  publisher: SnsPublisher,
  event: DomainEvent,
  maxRetries: number = 3
): Promise<string> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await publisher.publish(event);
    } catch (error) {
      lastError = error as Error;
      
      if (error instanceof SNSServiceException) {
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

- Reuse `SNSClient` instance between Lambda invocations
- Partition batches into groups of maximum 10 messages
- Implement retry with exponential backoff for transient errors
- Validate `MessageId` in successful responses
- Use strict types for domain events

## Example

```typescript
// Usage in Lambda
const publisher = new SnsPublisher(process.env.TOPIC_ARN!);

export const handler = async (event: APIGatewayEvent): Promise<APIGatewayProxyResult> => {
  const order = JSON.parse(event.body!);
  
  const domainEvent: DomainEvent = {
    eventId: crypto.randomUUID(),
    eventType: 'ORDER_CREATED',
    source: 'order-service',
    version: 1,
    payload: order,
    timestamp: new Date().toISOString()
  };
  
  const messageId = await publisher.publish(domainEvent);
  
  return {
    statusCode: 200,
    body: JSON.stringify({ messageId })
  };
};
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
