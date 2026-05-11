---
id: backend-skill-node-lambda-integraciones-mensajeria
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Integraciones de Mensajería — Node Lambda

## Propósito

Guía de implementación para integrar sistemas de mensajería como event sources de Lambda con TypeScript: SQS, SNS, EventBridge y Kafka (MSK) como triggers de funciones Lambda.

---

## 1. SQS como Event Source de Lambda

### Handler con Partial Batch Response

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
  console.log(`Processing order ${order.orderId} for customer ${order.customerId}`);
  // Lógica de negocio
}
```

### Productor SQS desde Lambda

```typescript
import { SQSClient, SendMessageCommand, SendMessageBatchCommand } from '@aws-sdk/client-sqs';

// Inicializar fuera del handler
const sqsClient = new SQSClient({});
const QUEUE_URL = process.env.QUEUE_URL!;

export class SqsProducer {
  async sendMessage<T>(message: T, options: { delaySeconds?: number; messageGroupId?: string; messageDeduplicationId?: string } = {}): Promise<string> {
    const command = new SendMessageCommand({
      QueueUrl: QUEUE_URL,
      MessageBody: JSON.stringify(message),
      DelaySeconds: options.delaySeconds,
      MessageGroupId: options.messageGroupId,
      MessageDeduplicationId: options.messageDeduplicationId
    });
    const response = await sqsClient.send(command);
    return response.MessageId!;
  }

  async sendBatch<T>(messages: T[]): Promise<void> {
    const entries = messages.map((msg, index) => ({ Id: String(index), MessageBody: JSON.stringify(msg) }));
    for (let i = 0; i < entries.length; i += 10) {
      await sqsClient.send(new SendMessageBatchCommand({ QueueUrl: QUEUE_URL, Entries: entries.slice(i, i + 10) }));
    }
  }
}
```

### template.yaml para SQS trigger

```yaml
Resources:
  OrderProcessorFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/functions/process-order/handler.handler
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt OrderQueue.Arn
            BatchSize: 10
            FunctionResponseTypes:
              - ReportBatchItemFailures

  OrderQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: order-queue
      VisibilityTimeout: 180
      RedrivePolicy:
        deadLetterTargetArn: !GetAtt OrderDLQ.Arn
        maxReceiveCount: 3

  OrderDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: order-dlq
```

---

## 2. SNS como Event Source de Lambda

### Handler para suscripción SNS

```typescript
import { SNSEvent, SNSHandler } from 'aws-lambda';

interface OrderEvent {
  eventId: string;
  eventType: string;
  payload: { orderId: string; customerId: string; amount: number };
}

export const handler: SNSHandler = async (event: SNSEvent): Promise<void> => {
  for (const record of event.Records) {
    const message = JSON.parse(record.Sns.Message) as OrderEvent;
    const attributes = record.Sns.MessageAttributes;

    console.log('Processing event:', {
      eventType: attributes.eventType?.Value,
      messageId: record.Sns.MessageId
    });

    switch (message.eventType) {
      case 'ORDER_CREATED':
        await handleOrderCreated(message.payload);
        break;
      case 'ORDER_UPDATED':
        await handleOrderUpdated(message.payload);
        break;
      default:
        console.log('Unknown event type:', message.eventType);
    }
  }
};
```

### Publicador SNS desde Lambda

```typescript
import { SNSClient, PublishCommand, PublishBatchCommand } from '@aws-sdk/client-sns';

const snsClient = new SNSClient({ region: process.env.AWS_REGION });
const TOPIC_ARN = process.env.TOPIC_ARN!;

export class SnsPublisher {
  async publish(event: DomainEvent): Promise<string> {
    const command = new PublishCommand({
      TopicArn: TOPIC_ARN,
      Message: JSON.stringify(event),
      MessageAttributes: {
        eventType: { DataType: 'String', StringValue: event.eventType },
        source: { DataType: 'String', StringValue: 'order-service' }
      }
    });
    const response = await snsClient.send(command);
    return response.MessageId!;
  }

  async publishFifo(event: DomainEvent, messageGroupId: string): Promise<string> {
    const command = new PublishCommand({
      TopicArn: TOPIC_ARN,
      Message: JSON.stringify(event),
      MessageGroupId: messageGroupId,
      MessageDeduplicationId: event.eventId
    });
    const response = await snsClient.send(command);
    return response.MessageId!;
  }
}
```

---

## 3. EventBridge como Event Source de Lambda

### Handler para reglas EventBridge

```typescript
import { EventBridgeEvent, Handler } from 'aws-lambda';

interface OrderPayload {
  orderId: string;
  customerId: string;
  amount: number;
}

export const handler: Handler<EventBridgeEvent<string, any>> = async (event): Promise<void> => {
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
```

### Publicador EventBridge desde Lambda

```typescript
import { EventBridgeClient, PutEventsCommand } from '@aws-sdk/client-eventbridge';

const ebClient = new EventBridgeClient({ region: process.env.AWS_REGION });
const EVENT_BUS_NAME = process.env.EVENT_BUS_NAME!;

export class EventBridgePublisher {
  async publish(event: DomainEvent): Promise<string> {
    const response = await ebClient.send(new PutEventsCommand({
      Entries: [{
        EventBusName: EVENT_BUS_NAME,
        Source: 'com.company.orders',
        DetailType: event.eventType,
        Detail: JSON.stringify(event),
        Time: new Date()
      }]
    }));
    if (response.FailedEntryCount && response.FailedEntryCount > 0) {
      throw new Error(`Failed to publish: ${response.Entries![0].ErrorMessage}`);
    }
    return response.Entries![0].EventId!;
  }

  async publishBatch(events: DomainEvent[]): Promise<void> {
    for (let i = 0; i < events.length; i += 10) {
      const batch = events.slice(i, i + 10);
      await ebClient.send(new PutEventsCommand({
        Entries: batch.map(event => ({
          EventBusName: EVENT_BUS_NAME,
          Source: 'com.company.orders',
          DetailType: event.eventType,
          Detail: JSON.stringify(event),
          Time: new Date()
        }))
      }));
    }
  }
}
```

### template.yaml para EventBridge

```yaml
Resources:
  OrderEventRule:
    Type: AWS::Events::Rule
    Properties:
      EventBusName: !Ref OrderEventBus
      EventPattern:
        source: ["com.company.orders"]
        detail-type: ["OrderCreated", "PaymentProcessed"]
      Targets:
        - Arn: !GetAtt ProcessOrderFunction.Arn
          Id: ProcessOrderTarget
```

---

## 4. Kafka (MSK) como Event Source de Lambda

### Handler para eventos Kafka

```typescript
import { MSKEvent, MSKHandler } from 'aws-lambda';

interface DomainEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  payload: Record<string, unknown>;
}

export const handler: MSKHandler = async (event: MSKEvent): Promise<void> => {
  for (const [topic, partitions] of Object.entries(event.records)) {
    for (const record of partitions) {
      const value = Buffer.from(record.value, 'base64').toString('utf-8');
      const domainEvent: DomainEvent = JSON.parse(value);

      console.log(`Processing event from ${topic}:`, {
        eventType: domainEvent.eventType,
        aggregateId: domainEvent.aggregateId,
        partition: record.partition,
        offset: record.offset
      });

      await processEvent(domainEvent);
    }
  }
};

async function processEvent(event: DomainEvent): Promise<void> {
  switch (event.eventType) {
    case 'ORDER_CREATED':
      // Procesar orden creada
      break;
    case 'PAYMENT_RECEIVED':
      // Procesar pago recibido
      break;
  }
}
```

### template.yaml para MSK trigger

```yaml
Resources:
  KafkaConsumerFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/functions/kafka-consumer/handler.handler
      Events:
        MSKEvent:
          Type: MSK
          Properties:
            Stream: !Ref MSKClusterArn
            Topics:
              - orders-topic
            StartingPosition: LATEST
            BatchSize: 100
```

---

## Reglas Importantes para Lambda

- **Partial Batch Response**: Siempre usar `ReportBatchItemFailures` en SQS para no reprocesar mensajes exitosos
- **Idempotencia**: Implementar idempotencia en handlers (los mensajes pueden llegar más de una vez)
- **DLQ**: Configurar Dead Letter Queue con `maxReceiveCount: 3`
- **Clientes fuera del handler**: Inicializar `SQSClient`, `SNSClient`, `EventBridgeClient` fuera del handler
- **Timeout**: El `VisibilityTimeout` de SQS debe ser >= 6x el timeout de Lambda
- **Batch size**: Ajustar según la duración del procesamiento por mensaje
- **EventBridge**: Lotes máximos de 10 eventos por `PutEvents`
- **Kafka**: Los records vienen en base64; decodificar antes de parsear
