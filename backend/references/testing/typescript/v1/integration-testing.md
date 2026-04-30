<!-- keywords: integration testing, testcontainers, localstack, supertest, typescript, nodejs -->
# Integration Testing — TypeScript Implementation

## Purpose

Implementation guide for integration tests in TypeScript/Node.js using Testcontainers, LocalStack, and Supertest.

## Libraries and dependencies

```json
{
  "devDependencies": {
    "testcontainers": "^10.2.1",
    "@testcontainers/localstack": "^10.2.1",
    "@testcontainers/postgresql": "^10.2.1",
    "supertest": "^6.3.3",
    "@types/supertest": "^2.0.14",
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1"
  }
}
```

## Configuration

### jest.integration.config.js

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  testMatch: ['**/*.integration.test.ts'],
  testTimeout: 60000,
  setupFilesAfterEnv: ['./jest.integration.setup.ts']
};
```

## Step by Step / Guidelines

### Test with PostgreSQL Testcontainer

```typescript
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { Pool } from 'pg';
import { OrderRepository } from '../order-repository';

describe('OrderRepository Integration', () => {
  let container: StartedTestContainer;
  let pool: Pool;
  let repository: OrderRepository;
  
  beforeAll(async () => {
    container = await new GenericContainer('postgres:15')
      .withEnvironment({
        POSTGRES_DB: 'testdb',
        POSTGRES_USER: 'test',
        POSTGRES_PASSWORD: 'test'
      })
      .withExposedPorts(5432)
      .start();
    
    pool = new Pool({
      host: container.getHost(),
      port: container.getMappedPort(5432),
      database: 'testdb',
      user: 'test',
      password: 'test'
    });
    
    await runMigrations(pool);
    repository = new OrderRepository(pool);
  }, 60000);
  
  afterAll(async () => {
    await pool.end();
    await container.stop();
  });
  
  beforeEach(async () => {
    await pool.query('DELETE FROM orders');
  });
  
  it('should save and retrieve order', async () => {
    const order = {
      customerId: 'cust-123',
      status: 'PENDING',
      totalAmount: 100.00
    };
    
    const saved = await repository.save(order);
    const found = await repository.findById(saved.id);
    
    expect(found).toBeDefined();
    expect(found?.customerId).toBe('cust-123');
  });
});
```

### Test with LocalStack (SQS)

```typescript
import { LocalstackContainer, StartedLocalStackContainer } from '@testcontainers/localstack';
import { SQSClient, CreateQueueCommand, SendMessageCommand, ReceiveMessageCommand } from '@aws-sdk/client-sqs';

describe('SQS Integration', () => {
  let localstack: StartedLocalStackContainer;
  let sqsClient: SQSClient;
  let queueUrl: string;
  
  beforeAll(async () => {
    localstack = await new LocalstackContainer('localstack/localstack:3.0')
      .start();
    
    sqsClient = new SQSClient({
      endpoint: localstack.getConnectionUri(),
      region: 'us-east-1',
      credentials: {
        accessKeyId: 'test',
        secretAccessKey: 'test'
      }
    });
    
    const createResult = await sqsClient.send(new CreateQueueCommand({
      QueueName: 'order-events'
    }));
    queueUrl = createResult.QueueUrl!;
  }, 60000);
  
  afterAll(async () => {
    await localstack.stop();
  });
  
  it('should send and receive message from SQS', async () => {
    const event = { orderId: 'ord-123', type: 'CREATED' };
    
    await sqsClient.send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify(event)
    }));
    
    const response = await sqsClient.send(new ReceiveMessageCommand({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: 1,
      WaitTimeSeconds: 5
    }));
    
    expect(response.Messages).toHaveLength(1);
    expect(JSON.parse(response.Messages![0].Body!)).toEqual(event);
  });
});
```

### API Integration Test with Supertest

```typescript
import request from 'supertest';
import { app } from '../app';
import { GenericContainer, StartedTestContainer } from 'testcontainers';

describe('Order API Integration', () => {
  let container: StartedTestContainer;
  
  beforeAll(async () => {
    container = await new GenericContainer('postgres:15')
      .withEnvironment({
        POSTGRES_DB: 'testdb',
        POSTGRES_USER: 'test',
        POSTGRES_PASSWORD: 'test'
      })
      .withExposedPorts(5432)
      .start();
    
    process.env.DATABASE_URL = `postgresql://test:test@${container.getHost()}:${container.getMappedPort(5432)}/testdb`;
  }, 60000);
  
  afterAll(async () => {
    await container.stop();
  });
  
  it('POST /orders should create order', async () => {
    const response = await request(app)
      .post('/api/v1/orders')
      .send({
        customerId: 'cust-123',
        items: [{ productId: 'prod-1', quantity: 2, unitPrice: 25.00 }],
        currency: 'USD'
      })
      .expect(201);
    
    expect(response.body.customerId).toBe('cust-123');
    expect(response.body.totalAmount).toBe(50.00);
  });
  
  it('POST /orders should return validation error', async () => {
    const response = await request(app)
      .post('/api/v1/orders')
      .send({ customerId: '', items: [] })
      .expect(400);
    
    expect(response.body.title).toBe('Validation Error');
  });
});
```

## Mocks and fixtures

### Test Utilities

```typescript
// test-utils.ts
import { GenericContainer, StartedTestContainer } from 'testcontainers';
import { Pool } from 'pg';

export async function createPostgresContainer(): Promise<{
  container: StartedTestContainer;
  pool: Pool;
}> {
  const container = await new GenericContainer('postgres:15')
    .withEnvironment({
      POSTGRES_DB: 'testdb',
      POSTGRES_USER: 'test',
      POSTGRES_PASSWORD: 'test'
    })
    .withExposedPorts(5432)
    .start();
  
  const pool = new Pool({
    host: container.getHost(),
    port: container.getMappedPort(5432),
    database: 'testdb',
    user: 'test',
    password: 'test'
  });
  
  return { container, pool };
}
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
