<!-- keywords: retry, timeout, exponential backoff, fault tolerance, typescript, nodejs -->
# Retry and Timeout - TypeScript Implementation

## Purpose

Implement retry patterns with exponential backoff and timeout in Node.js/TypeScript applications.

## Scope of Application

- When configuring retries on HTTP calls with axios
- When implementing timeouts on async operations
- When creating reusable retry utilities

## Main content

### Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "axios-retry": "^4.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0"
  }
}
```

### Retry Utilities

```typescript
interface RetryConfig {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  multiplier: number;
  jitterFactor: number;
  retryableErrors?: (error: Error) => boolean;
}

const defaultConfig: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 500,
  maxDelayMs: 10000,
  multiplier: 2,
  jitterFactor: 0.5,
  retryableErrors: (error) => {
    if (error instanceof Error) {
      const message = error.message.toLowerCase();
      return message.includes('timeout') ||
             message.includes('econnrefused') ||
             message.includes('econnreset') ||
             message.includes('503');
    }
    return false;
  }
};

function calculateDelay(attempt: number, config: RetryConfig): number {
  const exponentialDelay = Math.min(
    config.initialDelayMs * Math.pow(config.multiplier, attempt),
    config.maxDelayMs
  );
  
  const jitter = exponentialDelay * config.jitterFactor * (Math.random() * 2 - 1);
  return Math.max(0, exponentialDelay + jitter);
}

async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const finalConfig = { ...defaultConfig, ...config };
  let lastError: Error;
  
  for (let attempt = 0; attempt < finalConfig.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      
      if (!finalConfig.retryableErrors?.(lastError)) {
        throw lastError;
      }
      
      if (attempt < finalConfig.maxAttempts - 1) {
        const delay = calculateDelay(attempt, finalConfig);
        console.log(`Retry attempt ${attempt + 1} after ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  throw lastError!;
}
```

### Timeout Utility

```typescript
async function withTimeout<T>(
  operation: () => Promise<T>,
  timeoutMs: number
): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('Operation timed out')), timeoutMs);
  });
  
  return Promise.race([operation(), timeoutPromise]);
}

// Combining retry + timeout
async function resilientCall<T>(
  operation: () => Promise<T>,
  options: { timeoutMs: number; retryConfig?: Partial<RetryConfig> }
): Promise<T> {
  return withRetry(
    () => withTimeout(operation, options.timeoutMs),
    options.retryConfig
  );
}
```

### Configuration with axios-retry

```typescript
import axios from 'axios';
import axiosRetry from 'axios-retry';

const client = axios.create({
  baseURL: 'https://api.external.com',
  timeout: 5000
});

axiosRetry(client, {
  retries: 3,
  retryDelay: (retryCount) => {
    const delay = Math.min(500 * Math.pow(2, retryCount), 10000);
    const jitter = delay * 0.5 * (Math.random() * 2 - 1);
    return Math.max(0, delay + jitter);
  },
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
           error.response?.status === 503 ||
           error.response?.status === 429;
  },
  onRetry: (retryCount, error, requestConfig) => {
    console.log(`Retry attempt ${retryCount} for ${requestConfig.url}`);
  }
});
```

### Service with Retry

```typescript
class PaymentService {
  private client = axios.create({
    baseURL: 'https://api.payments.com',
    timeout: 5000
  });

  constructor() {
    axiosRetry(this.client, {
      retries: 3,
      retryDelay: axiosRetry.exponentialDelay,
      retryCondition: (error) => {
        return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
               error.response?.status === 503;
      }
    });
  }

  async processPayment(request: PaymentRequest): Promise<PaymentResult> {
    try {
      const response = await this.client.post('/payments', request);
      return response.data;
    } catch (error) {
      console.error('Payment failed after retries:', error);
      throw error;
    }
  }
}

// Usage with custom utilities
class OrderService {
  async createOrder(order: Order): Promise<OrderResult> {
    return resilientCall(
      () => this.orderApi.create(order),
      {
        timeoutMs: 10000,
        retryConfig: {
          maxAttempts: 3,
          initialDelayMs: 1000
        }
      }
    );
  }
}
```

## Important Rules

- Use `exponentialDelay` from axios-retry or implement with jitter
- Configure `retryCondition` to only retry transient errors
- Combine timeout with retry for resilient operations
- Use `onRetry` for logging and metrics

## Example

```typescript
// Complete resilient HTTP client
function createResilientClient(baseURL: string) {
  const client = axios.create({
    baseURL,
    timeout: 5000,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  axiosRetry(client, {
    retries: 3,
    retryDelay: (retryCount) => {
      const delay = 500 * Math.pow(2, retryCount);
      const jitter = delay * 0.5 * Math.random();
      return delay + jitter;
    },
    retryCondition: (error) => {
      const status = error.response?.status;
      return !status || status >= 500 || status === 429;
    }
  });

  return client;
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
