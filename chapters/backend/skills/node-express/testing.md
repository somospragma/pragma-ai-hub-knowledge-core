---
id: backend-skill-node-express-testing
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Testing — Node Express

## Propósito

Guía de implementación de testing en microservicios Node.js/Express con TypeScript: unit testing con Jest, integration testing con Testcontainers y Supertest, y configuración de coverage.

---

## 1. Configuración de Jest

### Dependencias

```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1",
    "@types/jest": "^29.5.8",
    "typescript": "^5.2.2",
    "supertest": "^6.3.3",
    "@types/supertest": "^2.0.14",
    "testcontainers": "^10.2.1",
    "@testcontainers/localstack": "^10.2.1",
    "@testcontainers/postgresql": "^10.2.1"
  }
}
```

### jest.config.js (Unit Tests)

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.dto.ts',
    '!src/**/*.config.ts',
    '!src/**/index.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
```

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

---

## 2. Unit Testing con Jest

### Test básico con mocks

```typescript
import { CustomerService } from './customer.service';
import { CustomerRepository } from './customer.repository';
import { NotificationService } from './notification.service';

jest.mock('./customer.repository');
jest.mock('./notification.service');

describe('CustomerService', () => {
  let customerService: CustomerService;
  let mockRepository: jest.Mocked<CustomerRepository>;
  let mockNotification: jest.Mocked<NotificationService>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockRepository = new CustomerRepository() as jest.Mocked<CustomerRepository>;
    mockNotification = new NotificationService() as jest.Mocked<NotificationService>;
    customerService = new CustomerService(mockRepository, mockNotification);
  });

  describe('create', () => {
    it('should create customer successfully', async () => {
      const request = { name: 'John Doe', email: 'john@example.com' };
      const savedCustomer = { id: 'cust-123', ...request, status: 'ACTIVE' };

      mockRepository.save.mockResolvedValue(savedCustomer);
      mockNotification.sendWelcomeEmail.mockResolvedValue(undefined);

      const result = await customerService.create(request);

      expect(result).toEqual(savedCustomer);
      expect(mockRepository.save).toHaveBeenCalledWith(expect.objectContaining({ name: 'John Doe' }));
      expect(mockNotification.sendWelcomeEmail).toHaveBeenCalledWith('john@example.com');
    });

    it('should throw error when name is empty', async () => {
      await expect(customerService.create({ name: '', email: 'john@example.com' }))
        .rejects.toThrow('Name is required');
      expect(mockRepository.save).not.toHaveBeenCalled();
    });
  });

  describe('findById', () => {
    it('should return customer when found', async () => {
      const customer = { id: 'cust-123', name: 'John Doe' };
      mockRepository.findById.mockResolvedValue(customer);

      const result = await customerService.findById('cust-123');
      expect(result).toEqual(customer);
    });

    it('should throw CustomerNotFoundError when not found', async () => {
      mockRepository.findById.mockResolvedValue(null);
      await expect(customerService.findById('non-existent')).rejects.toThrow('Customer not found');
    });
  });
});
```

### Tests parametrizados

```typescript
describe('validateEmail', () => {
  it.each([
    ['john@example.com', true],
    ['invalid-email', false],
    ['', false],
    ['test@domain.co.uk', true]
  ])('should validate email %s as %s', (email, isValid) => {
    if (isValid) {
      expect(() => customerService.validateEmail(email)).not.toThrow();
    } else {
      expect(() => customerService.validateEmail(email)).toThrow();
    }
  });
});
```

### Tests con timers y spies

```typescript
describe('CacheService', () => {
  beforeEach(() => jest.useFakeTimers());
  afterEach(() => jest.useRealTimers());

  it('should expire cached items after TTL', () => {
    const cacheService = new CacheService({ ttlMs: 5000 });
    cacheService.set('key', 'value');
    expect(cacheService.get('key')).toBe('value');

    jest.advanceTimersByTime(6000);
    expect(cacheService.get('key')).toBeUndefined();
  });
});
```

### Fixtures reutilizables

```typescript
// __fixtures__/customer.fixtures.ts
export const CustomerFixtures = {
  validCustomer: () => ({
    id: 'cust-123', name: 'John Doe', email: 'john@example.com', status: 'ACTIVE', createdAt: new Date()
  }),
  validRequest: () => ({ name: 'John Doe', email: 'john@example.com' }),
  customerList: (count: number) =>
    Array.from({ length: count }, (_, i) => ({
      id: `cust-${i}`, name: `Customer ${i}`, email: `customer${i}@example.com`, status: 'ACTIVE'
    }))
};
```

---

## 3. Integration Testing

### Test con PostgreSQL Testcontainer

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
      .withEnvironment({ POSTGRES_DB: 'testdb', POSTGRES_USER: 'test', POSTGRES_PASSWORD: 'test' })
      .withExposedPorts(5432)
      .start();

    pool = new Pool({
      host: container.getHost(),
      port: container.getMappedPort(5432),
      database: 'testdb', user: 'test', password: 'test'
    });
    await runMigrations(pool);
    repository = new OrderRepository(pool);
  }, 60000);

  afterAll(async () => { await pool.end(); await container.stop(); });
  beforeEach(async () => { await pool.query('DELETE FROM orders'); });

  it('should save and retrieve order', async () => {
    const order = { customerId: 'cust-123', status: 'PENDING', totalAmount: 100.00 };
    const saved = await repository.save(order);
    const found = await repository.findById(saved.id);
    expect(found).toBeDefined();
    expect(found?.customerId).toBe('cust-123');
  });
});
```

### Test con LocalStack (SQS)

```typescript
import { LocalstackContainer, StartedLocalStackContainer } from '@testcontainers/localstack';
import { SQSClient, CreateQueueCommand, SendMessageCommand, ReceiveMessageCommand } from '@aws-sdk/client-sqs';

describe('SQS Integration', () => {
  let localstack: StartedLocalStackContainer;
  let sqsClient: SQSClient;
  let queueUrl: string;

  beforeAll(async () => {
    localstack = await new LocalstackContainer('localstack/localstack:3.0').start();
    sqsClient = new SQSClient({
      endpoint: localstack.getConnectionUri(),
      region: 'us-east-1',
      credentials: { accessKeyId: 'test', secretAccessKey: 'test' }
    });
    const result = await sqsClient.send(new CreateQueueCommand({ QueueName: 'order-events' }));
    queueUrl = result.QueueUrl!;
  }, 60000);

  afterAll(async () => { await localstack.stop(); });

  it('should send and receive message from SQS', async () => {
    const event = { orderId: 'ord-123', type: 'CREATED' };
    await sqsClient.send(new SendMessageCommand({ QueueUrl: queueUrl, MessageBody: JSON.stringify(event) }));

    const response = await sqsClient.send(new ReceiveMessageCommand({ QueueUrl: queueUrl, MaxNumberOfMessages: 1, WaitTimeSeconds: 5 }));
    expect(response.Messages).toHaveLength(1);
    expect(JSON.parse(response.Messages![0].Body!)).toEqual(event);
  });
});
```

### API Integration Test con Supertest

```typescript
import request from 'supertest';
import { app } from '../app';

describe('Order API Integration', () => {
  it('POST /orders should create order', async () => {
    const response = await request(app)
      .post('/api/v1/orders')
      .send({ customerId: 'cust-123', items: [{ productId: 'prod-1', quantity: 2, unitPrice: 25.00 }], currency: 'USD' })
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

---

## 4. Coverage y Scripts

### package.json scripts

```json
{
  "scripts": {
    "test": "jest --coverage",
    "test:unit": "jest --config jest.config.js --coverage",
    "test:integration": "jest --config jest.integration.config.js",
    "test:watch": "jest --watch"
  }
}
```

---

## Reglas Importantes

- **Coverage mínimo**: 80% en branches, functions, lines y statements
- **Arrange-Act-Assert**: Seguir patrón AAA en todos los tests
- **Mocks**: Usar `jest.clearAllMocks()` en `beforeEach`
- **Integration tests**: Usar Testcontainers para bases de datos reales
- **Timeout**: Configurar `testTimeout: 60000` para integration tests
- **Fixtures**: Crear factories reutilizables para datos de prueba
- **Aislamiento**: Limpiar datos entre tests con `beforeEach`
