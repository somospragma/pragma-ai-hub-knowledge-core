<!-- keywords: sqs, aws, queue, sdk v3, messaging, typescript, nodejs -->
# Amazon SQS Integration - TypeScript

## Purpose

Implement integration with Amazon SQS in TypeScript using AWS SDK v3.

## Scope of Application

- Node.js/TypeScript projects that require SQS
- Serverless applications with Lambda
- APIs with Express, Fastify, or NestJS

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-sqs": "^3.400.0"
  }
}
```

### Message Producer

```typescript
import { SQSClient, SendMessageCommand, SendMessageBatchCommand } from '@aws-sdk/client-sqs';

interface MessageOptions {
  delaySeconds?: number;
  messageGroupId?: string;
  messageDeduplicationId?: string;
}

export class SqsProducer {
  private client: SQSClient;
  
  constructor(private queueUrl: string) {
    this.client = new SQSClient({});
  }

  async sendMessage<T>(message: T, options: MessageOptions = {}): Promise<string> {
    const command = new SendMessageCommand({
      QueueUrl: this.queueUrl,
      MessageBody: JSON.stringify(message),
      DelaySeconds: options.delaySeconds,
      MessageGroupId: options.messageGroupId,
      MessageDeduplicationId: options.messageDeduplicationId
    });

    const response = await this.client.send(command);
    return response.MessageId!;
  }

  async sendBatch<T>(messages: T[]): Promise<void> {
    const entries = messages.map((msg, index) => ({
      Id: String(index),
      MessageBody: JSON.stringify(msg)
    }));

    for (let i = 0; i < entries.length; i += 10) {
      const batch = entries.slice(i, i + 10);
      const command = new SendMessageBatchCommand({
        QueueUrl: this.queueUrl,
        Entries: batch
      });
      await this.client.send(command);
    }
  }
}
```


### Lambda Handler with Partial Batch Response

```typescript
import { SQSEvent, SQSBatchResponse, SQSRecord } from 'aws-lambda';

interface OrderMessage {
  orderId: string;
  customerId: string;
  amount: number;
}

export const handler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  const batchItemFailures: SQSBatchResponse['batchItemFailures'] = [];

  const processPromises = event.Records.map(async (record: SQSRecord) => {
    try {
      const message: OrderMessage = JSON.parse(record.body);
      await processOrder(message);
    } catch (error) {
      console.error(`Failed to process message ${record.messageId}:`, error);
      batchItemFailures.push({ itemIdentifier: record.messageId });
    }
  });

  await Promise.all(processPromises);

  return { batchItemFailures };
};

async function processOrder(order: OrderMessage): Promise<void> {
  console.log(`Processing order ${order.orderId}`);
  // Processing logic
}
```

## Important Rules

- Use batch operations for better throughput (max 10 messages)
- Implement partial batch response in Lambda
- Use MessageGroupId for FIFO queues
- Implement idempotency in consumers

## Example

```typescript
// Producer usage
const producer = new SqsProducer(process.env.QUEUE_URL!);

// Simple message
await producer.sendMessage({ orderId: '123', amount: 100 });

// FIFO message
await producer.sendMessage(
  { orderId: '123', amount: 100 },
  { messageGroupId: 'customer-456', messageDeduplicationId: 'order-123' }
);

// Batch
await producer.sendBatch([
  { orderId: '1', amount: 100 },
  { orderId: '2', amount: 200 }
]);
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
