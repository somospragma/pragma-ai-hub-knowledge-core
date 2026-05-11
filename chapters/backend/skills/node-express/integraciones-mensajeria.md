---
id: backend-skill-node-express-integraciones-mensajeria
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Integraciones de Mensajería — Node Express

## Propósito

Guía de implementación para integrar sistemas de mensajería en microservicios Node.js/Express con TypeScript: Kafka (kafkajs), SQS, SNS y EventBridge con AWS SDK v3.

---

## 1. Apache Kafka con KafkaJS

### Dependencias

```json
{
  "dependencies": {
    "kafkajs": "^2.2.4"
  }
}
```

### Cliente Kafka

```typescript
import { Kafka, Producer, Consumer, EachMessagePayload } from 'kafkajs';

interface KafkaConfig {
  brokers: string[];
  clientId: string;
  ssl?: boolean;
  sasl?: { mechanism: 'scram-sha-512'; username: string; password: string };
}

interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  payload: Record<string, unknown>;
}

export class KafkaClient {
  private kafka: Kafka;
  private producer: Producer | null = null;

  constructor(config: KafkaConfig) {
    this.kafka = new Kafka({ clientId: config.clientId, brokers: config.brokers, ssl: config.ssl, sasl: config.sasl });
  }

  async initProducer(): Promise<void> {
    this.producer = this.kafka.producer({ idempotent: true, maxInFlightRequests: 5 });
    await this.producer.connect();
  }

  async send(topic: string, event: DomainEvent): Promise<void> {
    if (!this.producer) throw new Error('Producer not initialized');
    await this.producer.send({
      topic,
      messages: [{
        key: event.aggregateId,
        value: JSON.stringify(event),
        headers: { 'event-type': event.eventType, 'correlation-id': event.eventId }
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
          headers: { 'event-type': event.eventType }
        }))
      }]
    });
  }

  async disconnect(): Promise<void> {
    await this.producer?.disconnect();
  }
}
```

### Productor transaccional

```typescript
export class TransactionalKafkaProducer {
  private producer: Producer;

  constructor(config: KafkaConfig) {
    const kafka = new Kafka({ clientId: config.clientId, brokers: config.brokers });
    this.producer = kafka.producer({ idempotent: true, transactionalId: 'order-producer-tx' });
  }

  async sendTransactional(topic: string, events: DomainEvent[]): Promise<void> {
    const transaction = await this.producer.transaction();
    try {
      for (const event of events) {
        await transaction.send({ topic, messages: [{ key: event.aggregateId, value: JSON.stringify(event) }] });
      }
      await transaction.commit();
    } catch (error) {
      await transaction.abort();
      throw error;
    }
  }
}
```

### Consumidor con DLQ

```typescript
export class ResilientKafkaConsumer {
  private consumer: Consumer;
  private kafka: Kafka;

  constructor(config: KafkaConfig, groupId: string) {
    this.kafka = new Kafka({ clientId: config.clientId, brokers: config.brokers });
    this.consumer = this.kafka.consumer({ groupId, sessionTimeout: 30000, heartbeatInterval: 3000 });
  }

  async start(topic: string, handler: (event: DomainEvent) => Promise<void>, dlqTopic?: string): Promise<void> {
    await this.consumer.connect();
    await this.consumer.subscribe({ topic });
    await this.consumer.run({
      eachMessage: async ({ message }) => {
        try {
          const event = JSON.parse(message.value!.toString());
          await handler(event);
        } catch (error) {
          if (dlqTopic) await this.sendToDlq(dlqTopic, message, error as Error);
        }
      }
    });
  }

  private async sendToDlq(dlqTopic: string, message: any, error: Error): Promise<void> {
    const producer = this.kafka.producer();
    await producer.connect();
    await producer.send({
      topic: dlqTopic,
      messages: [{ key: message.key, value: message.value, headers: { 'error-message': error.message } }]
    });
    await producer.disconnect();
  }
}
```

---

## 2. Amazon SQS

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-sqs": "^3.400.0"
  }
}
```

### Productor

```typescript
import { SQSClient, SendMessageCommand, SendMessageBatchCommand } from '@aws-sdk/client-sqs';

export class SqsProducer {
  private client: SQSClient;

  constructor(private queueUrl: string) {
    this.client = new SQSClient({});
  }

  async sendMessage<T>(message: T, options: { delaySeconds?: number; messageGroupId?: string; messageDeduplicationId?: string } = {}): Promise<string> {
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
    const entries = messages.map((msg, index) => ({ Id: String(index), MessageBody: JSON.stringify(msg) }));
    for (let i = 0; i < entries.length; i += 10) {
      const batch = entries.slice(i, i + 10);
      await this.client.send(new SendMessageBatchCommand({ QueueUrl: this.queueUrl, Entries: batch }));
    }
  }
}
```

### Consumidor Express (polling)

```typescript
import { SQSClient, ReceiveMessageCommand, DeleteMessageCommand } from '@aws-sdk/client-sqs';

export class SqsConsumer {
  private client: SQSClient;
  private running = false;

  constructor(private queueUrl: string) {
    this.client = new SQSClient({});
  }

  async start(handler: (message: any) => Promise<void>): Promise<void> {
    this.running = true;
    while (this.running) {
      const response = await this.client.send(new ReceiveMessageCommand({
        QueueUrl: this.queueUrl,
        MaxNumberOfMessages: 10,
        WaitTimeSeconds: 20
      }));
      for (const msg of response.Messages || []) {
        try {
          await handler(JSON.parse(msg.Body!));
          await this.client.send(new DeleteMessageCommand({ QueueUrl: this.queueUrl, ReceiptHandle: msg.ReceiptHandle! }));
        } catch (error) {
          console.error('Error processing message:', error);
        }
      }
    }
  }

  stop(): void { this.running = false; }
}
```

---

## 3. Amazon SNS

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-sns": "^3.400.0"
  }
}
```

### Publicador

```typescript
import { SNSClient, PublishCommand, PublishBatchCommand, MessageAttributeValue } from '@aws-sdk/client-sns';

export class SnsPublisher {
  private client: SNSClient;

  constructor(private topicArn: string) {
    this.client = new SNSClient({ region: process.env.AWS_REGION });
  }

  async publish(event: DomainEvent): Promise<string> {
    const command = new PublishCommand({
      TopicArn: this.topicArn,
      Message: JSON.stringify(event),
      MessageAttributes: {
        eventType: { DataType: 'String', StringValue: event.eventType },
        source: { DataType: 'String', StringValue: 'order-service' }
      }
    });
    const response = await this.client.send(command);
    return response.MessageId!;
  }

  async publishBatch(events: DomainEvent[]): Promise<void> {
    for (let i = 0; i < events.length; i += 10) {
      const batch = events.slice(i, i + 10);
      await this.client.send(new PublishBatchCommand({
        TopicArn: this.topicArn,
        PublishBatchRequestEntries: batch.map((event, index) => ({
          Id: `${i + index}`,
          Message: JSON.stringify(event),
          MessageAttributes: { eventType: { DataType: 'String', StringValue: event.eventType } }
        }))
      }));
    }
  }

  async publishFifo(event: DomainEvent, messageGroupId: string): Promise<string> {
    const command = new PublishCommand({
      TopicArn: this.topicArn,
      Message: JSON.stringify(event),
      MessageGroupId: messageGroupId,
      MessageDeduplicationId: event.eventId
    });
    const response = await this.client.send(command);
    return response.MessageId!;
  }
}
```

---

## 4. Amazon EventBridge

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-eventbridge": "^3.400.0"
  }
}
```

### Publicador

```typescript
import { EventBridgeClient, PutEventsCommand, PutEventsRequestEntry } from '@aws-sdk/client-eventbridge';

export class EventBridgePublisher {
  private client: EventBridgeClient;

  constructor(private eventBusName: string, private source: string) {
    this.client = new EventBridgeClient({ region: process.env.AWS_REGION });
  }

  async publish(event: DomainEvent): Promise<string> {
    const entry: PutEventsRequestEntry = {
      EventBusName: this.eventBusName,
      Source: this.source,
      DetailType: event.eventType,
      Detail: JSON.stringify(event),
      Time: new Date()
    };
    const response = await this.client.send(new PutEventsCommand({ Entries: [entry] }));
    if (response.FailedEntryCount && response.FailedEntryCount > 0) {
      throw new Error(`Failed to publish: ${response.Entries![0].ErrorMessage}`);
    }
    return response.Entries![0].EventId!;
  }

  async publishBatch(events: DomainEvent[]): Promise<void> {
    for (let i = 0; i < events.length; i += 10) {
      const batch = events.slice(i, i + 10);
      const entries = batch.map(event => ({
        EventBusName: this.eventBusName,
        Source: this.source,
        DetailType: event.eventType,
        Detail: JSON.stringify(event),
        Time: new Date()
      }));
      await this.client.send(new PutEventsCommand({ Entries: entries }));
    }
  }
}
```

---

## Reglas Importantes

- **Kafka**: Usar `idempotent: true` para exactly-once delivery
- **SQS**: Lotes máximos de 10 mensajes; implementar idempotencia en consumidores
- **SNS**: Reutilizar instancia de `SNSClient` entre invocaciones
- **EventBridge**: Lotes máximos de 10 eventos
- **Retry**: Implementar backoff exponencial con jitter para errores transitorios
- **DLQ**: Siempre configurar Dead Letter Queue para mensajes fallidos
- **Graceful shutdown**: Desconectar productores/consumidores en `SIGTERM`
