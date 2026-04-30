<!-- keywords: unit testing, jest, test patterns, mocking, typescript, nodejs -->
# Unit Testing — TypeScript Implementation

## Purpose

Implementation guide for unit tests in TypeScript/Node.js using Jest, with functional examples and project configuration.

## Libraries and dependencies

```json
{
  "devDependencies": {
    "jest": "^29.7.0",
    "ts-jest": "^29.1.1",
    "@types/jest": "^29.5.8",
    "typescript": "^5.2.2"
  }
}
```

## Configuration

### jest.config.js

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

## Step by Step / Guidelines

### Basic test with mocks

```typescript
// customer.service.test.ts
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
      // Arrange
      const request = { name: 'John Doe', email: 'john@example.com' };
      const savedCustomer = {
        id: 'cust-123',
        name: 'John Doe',
        email: 'john@example.com',
        status: 'ACTIVE'
      };

      mockRepository.save.mockResolvedValue(savedCustomer);
      mockNotification.sendWelcomeEmail.mockResolvedValue(undefined);

      // Act
      const result = await customerService.create(request);

      // Assert
      expect(result).toEqual(savedCustomer);
      expect(mockRepository.save).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'John Doe',
          email: 'john@example.com'
        })
      );
      expect(mockNotification.sendWelcomeEmail).toHaveBeenCalledWith('john@example.com');
    });

    it('should throw error when name is empty', async () => {
      const request = { name: '', email: 'john@example.com' };

      await expect(customerService.create(request))
        .rejects
        .toThrow('Name is required');

      expect(mockRepository.save).not.toHaveBeenCalled();
    });
  });

  describe('findById', () => {
    it('should return customer when found', async () => {
      const customer = { id: 'cust-123', name: 'John Doe' };
      mockRepository.findById.mockResolvedValue(customer);

      const result = await customerService.findById('cust-123');

      expect(result).toEqual(customer);
      expect(mockRepository.findById).toHaveBeenCalledWith('cust-123');
    });

    it('should throw CustomerNotFoundError when not found', async () => {
      mockRepository.findById.mockResolvedValue(null);

      await expect(customerService.findById('non-existent'))
        .rejects
        .toThrow('Customer not found');
    });
  });
});
```

### Parameterized tests

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

### Test with timers and spies

```typescript
describe('CacheService', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should expire cached items after TTL', async () => {
    const cacheService = new CacheService({ ttlMs: 5000 });
    
    cacheService.set('key', 'value');
    expect(cacheService.get('key')).toBe('value');

    jest.advanceTimersByTime(6000);

    expect(cacheService.get('key')).toBeUndefined();
  });

  it('should call refresh callback on expiry', () => {
    const refreshCallback = jest.fn();
    const cacheService = new CacheService({ 
      ttlMs: 5000,
      onExpire: refreshCallback 
    });

    cacheService.set('key', 'value');
    jest.advanceTimersByTime(6000);

    expect(refreshCallback).toHaveBeenCalledWith('key');
  });
});
```

### Async function tests

```typescript
describe('AsyncOrderService', () => {
  it('should process order asynchronously', async () => {
    const mockProcessor = jest.fn().mockResolvedValue({ status: 'processed' });
    const service = new AsyncOrderService(mockProcessor);

    const result = await service.processOrder({ id: 'order-1' });

    expect(result.status).toBe('processed');
    expect(mockProcessor).toHaveBeenCalledTimes(1);
  });

  it('should retry on failure', async () => {
    const mockProcessor = jest.fn()
      .mockRejectedValueOnce(new Error('Temporary failure'))
      .mockResolvedValue({ status: 'processed' });
    
    const service = new AsyncOrderService(mockProcessor, { retries: 3 });

    const result = await service.processOrder({ id: 'order-1' });

    expect(result.status).toBe('processed');
    expect(mockProcessor).toHaveBeenCalledTimes(2);
  });
});
```

## Code examples

### Reusable fixtures

```typescript
// __fixtures__/customer.fixtures.ts
export const CustomerFixtures = {
  validCustomer: () => ({
    id: 'cust-123',
    name: 'John Doe',
    email: 'john@example.com',
    status: 'ACTIVE',
    createdAt: new Date()
  }),

  validRequest: () => ({
    name: 'John Doe',
    email: 'john@example.com'
  }),

  customerList: (count: number) => 
    Array.from({ length: count }, (_, i) => ({
      id: `cust-${i}`,
      name: `Customer ${i}`,
      email: `customer${i}@example.com`,
      status: 'ACTIVE'
    }))
};
```

### External module mocking

```typescript
// __mocks__/axios.ts
export default {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn()
  }))
};

// In the test
import axios from 'axios';
jest.mock('axios');

const mockedAxios = axios as jest.Mocked<typeof axios>;
mockedAxios.get.mockResolvedValue({ data: { id: '123' } });
```

## Mocks and fixtures

### Global setup

```typescript
// jest.setup.ts
beforeAll(() => {
  // Global configuration before all tests
});

afterAll(() => {
  // Global cleanup after all tests
});

// Custom matcher
expect.extend({
  toBeValidEmail(received: string) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const pass = emailRegex.test(received);
    return {
      pass,
      message: () => `expected ${received} ${pass ? 'not ' : ''}to be a valid email`
    };
  }
});
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
