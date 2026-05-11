---
id: backend-skill-node-lambda-testing
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Testing — Node Lambda

## Propósito

Guía de implementación de testing en funciones Lambda con TypeScript: unit testing con Jest, integration testing con SAM local y LocalStack, Lambda test events, y configuración de coverage.

---

## 1. Configuración de Jest

### Dependencias

```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1",
    "@types/jest": "^29.5.8",
    "@types/aws-lambda": "^8.10.0",
    "typescript": "^5.2.2",
    "testcontainers": "^10.2.1",
    "@testcontainers/localstack": "^10.2.1"
  }
}
```

### jest.config.js

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/test'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/index.ts'
  ],
  coverageThreshold: {
    global: { branches: 80, functions: 80, lines: 80, statements: 80 }
  },
  setupFiles: ['./test/setup.ts']
};
```

### test/setup.ts

```typescript
// Variables de entorno para tests
process.env.TABLE_NAME = 'test-table';
process.env.QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue';
process.env.AWS_REGION = 'us-east-1';
```

---

## 2. Unit Testing de Handlers

### Test de handler Lambda

```typescript
import { APIGatewayProxyEvent, Context } from 'aws-lambda';
import { handler } from '../../src/functions/create-order/handler';

// Mock de dependencias
jest.mock('../../src/functions/create-order/application/create-order.usecase');

describe('CreateOrder Handler', () => {
  const mockContext: Context = {
    functionName: 'create-order',
    functionVersion: '1',
    invokedFunctionArn: 'arn:aws:lambda:us-east-1:123456789:function:create-order',
    memoryLimitInMB: '256',
    awsRequestId: 'test-request-id',
    logGroupName: '/aws/lambda/create-order',
    logStreamName: '2024/01/01/[$LATEST]abc123',
    getRemainingTimeInMillis: () => 30000,
    done: jest.fn(),
    fail: jest.fn(),
    succeed: jest.fn(),
    callbackWaitsForEmptyEventLoop: true
  };

  const createEvent = (body: any, pathParams?: any): APIGatewayProxyEvent => ({
    body: JSON.stringify(body),
    pathParameters: pathParams || null,
    queryStringParameters: null,
    headers: { 'Content-Type': 'application/json' },
    httpMethod: 'POST',
    isBase64Encoded: false,
    path: '/orders',
    multiValueHeaders: {},
    multiValueQueryStringParameters: null,
    stageVariables: null,
    requestContext: {} as any,
    resource: ''
  });

  beforeEach(() => jest.clearAllMocks());

  it('should create order successfully', async () => {
    const event = createEvent({
      customerId: 'cust-123',
      items: [{ productId: 'prod-1', quantity: 2, unitPrice: 25.00 }]
    });

    const result = await handler(event, mockContext, jest.fn());

    expect(result.statusCode).toBe(201);
    const body = JSON.parse(result.body);
    expect(body.customerId).toBe('cust-123');
  });

  it('should return 400 for invalid body', async () => {
    const event = createEvent({ customerId: '', items: [] });

    const result = await handler(event, mockContext, jest.fn());

    expect(result.statusCode).toBe(400);
    const body = JSON.parse(result.body);
    expect(body.title).toBe('Validation Error');
  });

  it('should return 400 for missing body', async () => {
    const event = createEvent(null);
    event.body = null;

    const result = await handler(event, mockContext, jest.fn());

    expect(result.statusCode).toBe(400);
  });
});
```

### Test de Use Case

```typescript
import { CreateOrderUseCase } from '../../src/functions/create-order/application/create-order.usecase';
import { OrderGateway } from '../../src/domain/ports/OrderGateway';

describe('CreateOrderUseCase', () => {
  let useCase: CreateOrderUseCase;
  let mockGateway: jest.Mocked<OrderGateway>;

  beforeEach(() => {
    mockGateway = { save: jest.fn(), findById: jest.fn(), findByCustomerId: jest.fn() };
    useCase = new CreateOrderUseCase(mockGateway);
  });

  it('should create order with correct total', async () => {
    const request = {
      customerId: 'cust-123',
      items: [
        { productId: 'prod-1', quantity: 2, unitPrice: 25.00 },
        { productId: 'prod-2', quantity: 1, unitPrice: 50.00 }
      ]
    };

    mockGateway.save.mockResolvedValue({ id: 'order-123', ...request, totalAmount: 100, status: 'PENDING' });

    const result = await useCase.execute(request);

    expect(result.totalAmount).toBe(100);
    expect(result.status).toBe('PENDING');
    expect(mockGateway.save).toHaveBeenCalledWith(expect.objectContaining({ customerId: 'cust-123' }));
  });

  it('should throw error for empty items', async () => {
    await expect(useCase.execute({ customerId: 'cust-123', items: [] }))
      .rejects.toThrow('Order must have at least one item');
  });
});
```

### Test de Adapter (DynamoDB mock)

```typescript
import { DynamoDBDocumentClient, GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb';
import { mockClient } from 'aws-sdk-client-mock';
import { CustomerDynamoAdapter } from '../../src/infrastructure/driven_adapters/dynamodb/CustomerDynamoAdapter';

const ddbMock = mockClient(DynamoDBDocumentClient);

describe('CustomerDynamoAdapter', () => {
  let adapter: CustomerDynamoAdapter;

  beforeEach(() => {
    ddbMock.reset();
    adapter = new CustomerDynamoAdapter();
  });

  it('should find customer by id', async () => {
    ddbMock.on(GetCommand).resolves({
      Item: { pk: 'CUSTOMER#123', sk: 'PROFILE', name: 'John', email: 'john@test.com', status: 'ACTIVE' }
    });

    const result = await adapter.findById('123');

    expect(result).toBeDefined();
    expect(result?.name).toBe('John');
  });

  it('should return null when customer not found', async () => {
    ddbMock.on(GetCommand).resolves({ Item: undefined });

    const result = await adapter.findById('non-existent');

    expect(result).toBeNull();
  });

  it('should save customer', async () => {
    ddbMock.on(PutCommand).resolves({});

    const customer = { name: 'John', email: 'john@test.com', status: 'ACTIVE' };
    await expect(adapter.create(customer)).resolves.toBeDefined();
  });
});
```

---

## 3. Test de SQS Handler

```typescript
import { SQSEvent } from 'aws-lambda';
import { handler } from '../../src/functions/process-order/handler';

describe('SQS Process Order Handler', () => {
  const createSQSEvent = (messages: any[]): SQSEvent => ({
    Records: messages.map((msg, i) => ({
      messageId: `msg-${i}`,
      receiptHandle: `receipt-${i}`,
      body: JSON.stringify(msg),
      attributes: {} as any,
      messageAttributes: {},
      md5OfBody: '',
      eventSource: 'aws:sqs',
      eventSourceARN: 'arn:aws:sqs:us-east-1:123456789:queue',
      awsRegion: 'us-east-1'
    }))
  });

  it('should process all messages successfully', async () => {
    const event = createSQSEvent([
      { orderId: 'order-1', amount: 100 },
      { orderId: 'order-2', amount: 200 }
    ]);

    const result = await handler(event);

    expect(result.batchItemFailures).toHaveLength(0);
  });

  it('should report failed messages', async () => {
    const event = createSQSEvent([
      { orderId: 'order-1', amount: 100 },
      { orderId: 'invalid', amount: -1 }  // Causará error
    ]);

    const result = await handler(event);

    expect(result.batchItemFailures.length).toBeGreaterThan(0);
  });
});
```

---

## 4. Integration Testing con LocalStack

```typescript
import { LocalstackContainer, StartedLocalStackContainer } from '@testcontainers/localstack';
import { DynamoDBClient, CreateTableCommand } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, GetCommand } from '@aws-sdk/lib-dynamodb';

describe('DynamoDB Integration', () => {
  let localstack: StartedLocalStackContainer;
  let docClient: DynamoDBDocumentClient;

  beforeAll(async () => {
    localstack = await new LocalstackContainer('localstack/localstack:3.0').start();

    const dynamoClient = new DynamoDBClient({
      endpoint: localstack.getConnectionUri(),
      region: 'us-east-1',
      credentials: { accessKeyId: 'test', secretAccessKey: 'test' }
    });
    docClient = DynamoDBDocumentClient.from(dynamoClient);

    // Crear tabla
    await dynamoClient.send(new CreateTableCommand({
      TableName: 'test-table',
      KeySchema: [{ AttributeName: 'pk', KeyType: 'HASH' }, { AttributeName: 'sk', KeyType: 'RANGE' }],
      AttributeDefinitions: [{ AttributeName: 'pk', AttributeType: 'S' }, { AttributeName: 'sk', AttributeType: 'S' }],
      BillingMode: 'PAY_PER_REQUEST'
    }));
  }, 60000);

  afterAll(async () => { await localstack.stop(); });

  it('should save and retrieve item', async () => {
    await docClient.send(new PutCommand({
      TableName: 'test-table',
      Item: { pk: 'CUSTOMER#123', sk: 'PROFILE', name: 'John', email: 'john@test.com' }
    }));

    const response = await docClient.send(new GetCommand({
      TableName: 'test-table',
      Key: { pk: 'CUSTOMER#123', sk: 'PROFILE' }
    }));

    expect(response.Item?.name).toBe('John');
  });
});
```

---

## 5. SAM Local Testing

### Invocación local con eventos

```bash
# Invocar función con evento de prueba
sam local invoke CreateOrderFunction --event events/create-order.json --env-vars env.json

# Iniciar API local
sam local start-api --env-vars env.json

# Generar evento de prueba
sam local generate-event apigateway aws-proxy --method POST --path /orders --body '{"customerId":"123"}'
```

### Evento de prueba (events/create-order.json)

```json
{
  "httpMethod": "POST",
  "path": "/orders",
  "headers": { "Content-Type": "application/json" },
  "body": "{\"customerId\":\"cust-123\",\"items\":[{\"productId\":\"prod-1\",\"quantity\":2,\"unitPrice\":25.00}]}",
  "pathParameters": null,
  "queryStringParameters": null,
  "requestContext": { "requestId": "test-123" }
}
```

### Evento SQS de prueba (events/sqs-order.json)

```json
{
  "Records": [
    {
      "messageId": "msg-001",
      "receiptHandle": "receipt-001",
      "body": "{\"orderId\":\"order-123\",\"customerId\":\"cust-456\",\"amount\":100}",
      "attributes": { "ApproximateReceiveCount": "1" },
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:123456789:order-queue"
    }
  ]
}
```

---

## 6. Scripts de Testing

### package.json

```json
{
  "scripts": {
    "test": "jest --coverage",
    "test:unit": "jest --testPathPattern=test/unit",
    "test:integration": "jest --testPathPattern=test/integration --testTimeout=60000",
    "test:watch": "jest --watch",
    "test:local": "sam local invoke --env-vars env.json"
  }
}
```

---

## Reglas Importantes para Lambda Testing

- **Mock de AWS SDK**: Usar `aws-sdk-client-mock` para mockear clientes AWS
- **Context mock**: Siempre proveer un mock de `Context` con `getRemainingTimeInMillis`
- **Event factories**: Crear helpers para generar eventos (APIGateway, SQS, SNS, EventBridge)
- **LocalStack**: Usar para integration tests con servicios AWS reales
- **SAM local**: Usar para testing end-to-end local antes de deploy
- **Coverage**: Mínimo 80% en branches, functions, lines y statements
- **Aislamiento**: Cada test debe ser independiente; limpiar mocks con `jest.clearAllMocks()`
- **Test events**: Mantener archivos JSON de eventos en carpeta `events/` para SAM local
