<!-- keywords: kafka, msk, event streaming, kafkajs, consumer, producer, typescript, nodejs -->
# Apache Kafka / Amazon MSK Integration - TypeScript

## Purpose

Implement integration with Apache Kafka and Amazon MSK in TypeScript/Node.js projects using KafkaJS.

## Scope of Application

- TypeScript projects that require Kafka producers and consumers
- Node.js applications connecting to MSK
- Implementation of handlers for Kafka messages

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "kafkajs": "^2.x.x"
  }
}
```

```bash
npm install kafkajs
```

### Kafka Client

```typescript
import { Kafka, Producer, Consumer, EachMessagePayload } from 'kafkajs';

interface KafkaConfig {
  brokers: string[];
  clientId: string;
  ssl?: boolean;
  sasl?: {
    mechanism: 'plain' | 'scram-sha-256' | 'scram-sha-512';
    username: string;
    password: string;
  };
}

interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  payload: Record<string, unknown>;
}

class KafkaClient {
  private kafka: Kafka;
  private producer: Producer | null = null;
  private consumer: Consumer | null = null;
  
  constructor(config: KafkaConfig) {
    this.kafka = new Kafka({
      clientId: config.clientId,
      brokers: config.brokers,
      ssl: config.ssl,
      sasl: config.sasl
    });
  }
  
  async initProducer(): Promise<void> {
    this.producer = this.kafka.producer({
      idempotent: true,
      maxInFlightRequests: 5
    });
    await this.producer.connect();
  }
  
  async initConsumer(groupId: string): Promise<void> {
    this.consumer = this.kafka.consumer({ groupId });
    await this.consumer.connect();
  }
  
  async send(topic: string, event: DomainEvent): Promise<void> {
    if (!this.producer) throw new Error('Producer not initialized');
    
    await this.producer.send({
      topic,
      messages: [{
        key: event.aggregateId,
        value: JSON.stringify(event),
        headers: {
          'event-type': event.eventType,
          'correlation-id': event.eventId
        }
      }]
    });
  }
  
  async sendBatch(topic: string, events: DomainEvent[]): Promise<void> {
    if (!this.producer) throw new Error('Producer not initialized');
    
    await this.producer.sendBatch({
      topicMessages: [{
        topic,
        messages: events.map(event => ({
          key: event.aggregateId,
          value: JSON.stringify(event),
          headers: {
            'event-type': event.eventType
          }
        }))
      }]
    });
  }
  
  async subscribe(
    topic: string, 
    handler: (event: DomainEvent) => Promise<void>
  ): Promise<void> {
    if (!this.consumer) throw new Error('Consumer not initialized');
    
    await this.consumer.subscribe({ topic, fromBeginning: false });
    
    await this.consumer.run({
      eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
        try {
          const event = JSON.parse(message.value!.toString()) as DomainEvent;
          await handler(event);
        } catch (error) {
          console.error(`Error processing message: ${error}`);
        }
      }
    });
  }
  
  async disconnect(): Promise<void> {
    await this.producer?.disconnect();
    await this.consumer?.disconnect();
  }
}

export { KafkaClient, KafkaConfig, DomainEvent };
```

### Producer with transactions

```typescript
class TransactionalKafkaProducer {
  private kafka: Kafka;
  private producer: Producer;
  
  constructor(config: KafkaConfig) {
    this.kafka = new Kafka({
      clientId: config.clientId,
      brokers: config.brokers
    });
    
    this.producer = this.kafka.producer({
      idempotent: true,
      transactionalId: 'order-producer-tx'
    });
  }
  
  async connect(): Promise<void> {
    await this.producer.connect();
  }
  
  async sendTransactional(
    topic: string, 
    events: DomainEvent[]
  ): Promise<void> {
    const transaction = await this.producer.transaction();
    
    try {
      for (const event of events) {
        await transaction.send({
          topic,
          messages: [{
            key: event.aggregateId,
            value: JSON.stringify(event)
          }]
        });
      }
      
      await transaction.commit();
    } catch (error) {
      await transaction.abort();
      throw error;
    }
  }
}
```

### Consumer with error handling

```typescript
class ResilientKafkaConsumer {
  private kafka: Kafka;
  private consumer: Consumer;
  
  constructor(config: KafkaConfig, groupId: string) {
    this.kafka = new Kafka({
      clientId: config.clientId,
      brokers: config.brokers
    });
    
    this.consumer = this.kafka.consumer({
      groupId,
      sessionTimeout: 30000,
      heartbeatInterval: 3000
    });
  }
  
  async start(
    topic: string,
    handler: (event: DomainEvent) => Promise<void>,
    dlqTopic?: string
  ): Promise<void> {
    await this.consumer.connect();
    await this.consumer.subscribe({ topic });
    
    await this.consumer.run({
      eachMessage: async ({ message, partition, topic }) => {
        try {
          const event = JSON.parse(message.value!.toString());
          await handler(event);
        } catch (error) {
          console.error(`Error processing: ${error}`);
          
          if (dlqTopic) {
            await this.sendToDlq(dlqTopic, message, error as Error);
          }
        }
      }
    });
  }
  
  private async sendToDlq(
    dlqTopic: string, 
    message: any, 
    error: Error
  ): Promise<void> {
    const producer = this.kafka.producer();
    await producer.connect();
    
    await producer.send({
      topic: dlqTopic,
      messages: [{
        key: message.key,
        value: message.value,
        headers: {
          'original-topic': message.topic,
          'error-message': error.message
        }
      }]
    });
    
    await producer.disconnect();
  }
}
```

### Error handling

```typescript
async function sendWithRetry(
  client: KafkaClient,
  topic: string,
  event: DomainEvent,
  maxRetries: number = 3
): Promise<void> {
  let lastError: Error | undefined;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      await client.send(topic, event);
      return;
    } catch (error) {
      lastError = error as Error;
      const delay = Math.pow(2, attempt) * 100;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}
```

## Important Rules

- Use `idempotent: true` for exactly-once
- Configure `maxInFlightRequests` for concurrency control
- Implement Dead Letter Queue for failed messages
- Use transactions for atomic operations
- Close connections properly on shutdown

## Example

```typescript
// Usage in application
const config: KafkaConfig = {
  clientId: 'order-service',
  brokers: process.env.KAFKA_BROKERS!.split(','),
  ssl: true,
  sasl: {
    mechanism: 'scram-sha-512',
    username: process.env.KAFKA_USERNAME!,
    password: process.env.KAFKA_PASSWORD!
  }
};

const client = new KafkaClient(config);

async function main() {
  await client.initProducer();
  
  const event: DomainEvent = {
    eventId: crypto.randomUUID(),
    eventType: 'ORDER_CREATED',
    aggregateId: 'order-123',
    payload: { customerId: 'cust-456', amount: 100 }
  };
  
  await client.send('orders-topic', event);
  await client.disconnect();
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
