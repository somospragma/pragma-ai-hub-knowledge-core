<!-- keywords: circuit breaker, opossum, cascading failure, fault tolerance, typescript, nodejs -->
# Circuit Breaker - TypeScript Implementation

## Purpose

Implement the Circuit Breaker pattern in Node.js/TypeScript applications using opossum.

## Scope of Application

- When implementing calls to external services in Node.js
- When configuring circuit breakers with opossum
- When implementing fallbacks for unavailable services

## Main content

### Dependencies

```json
{
  "dependencies": {
    "opossum": "^8.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "typescript": "^5.3.0"
  }
}
```

### Circuit Breaker Configuration

```typescript
import CircuitBreaker from 'opossum';

interface CircuitBreakerOptions {
  timeout: number;
  errorThresholdPercentage: number;
  resetTimeout: number;
  volumeThreshold: number;
}

const defaultOptions: CircuitBreakerOptions = {
  timeout: 3000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
  volumeThreshold: 5
};

export function createCircuitBreaker<T>(
  action: (...args: any[]) => Promise<T>,
  options: Partial<CircuitBreakerOptions> = {}
): CircuitBreaker<any[], T> {
  const breaker = new CircuitBreaker(action, {
    ...defaultOptions,
    ...options
  });

  // Event listeners
  breaker.on('open', () => console.log('Circuit breaker opened'));
  breaker.on('halfOpen', () => console.log('Circuit breaker half-open'));
  breaker.on('close', () => console.log('Circuit breaker closed'));
  breaker.on('fallback', (result) => console.log('Fallback called:', result));

  return breaker;
}
```

### Service with Circuit Breaker

```typescript
import axios from 'axios';
import CircuitBreaker from 'opossum';

interface PaymentRequest {
  orderId: string;
  amount: number;
  currency: string;
}

interface PaymentResponse {
  transactionId: string;
  status: string;
  message?: string;
}

export class PaymentService {
  private circuitBreaker: CircuitBreaker<[PaymentRequest], PaymentResponse>;

  constructor(private baseUrl: string) {
    this.circuitBreaker = createCircuitBreaker(
      this.callPaymentApi.bind(this),
      {
        timeout: 5000,
        errorThresholdPercentage: 50,
        resetTimeout: 30000
      }
    );

    // Configure fallback
    this.circuitBreaker.fallback((request: PaymentRequest) => ({
      transactionId: 'FALLBACK',
      status: 'PENDING',
      message: 'Payment queued for retry'
    }));
  }

  private async callPaymentApi(request: PaymentRequest): Promise<PaymentResponse> {
    const response = await axios.post<PaymentResponse>(
      `${this.baseUrl}/payments`,
      request,
      { timeout: 5000 }
    );
    return response.data;
  }

  async processPayment(request: PaymentRequest): Promise<PaymentResponse> {
    return this.circuitBreaker.fire(request);
  }

  getStats() {
    return this.circuitBreaker.stats;
  }

  isOpen(): boolean {
    return this.circuitBreaker.opened;
  }
}
```

### Express Middleware

```typescript
import { Request, Response, NextFunction } from 'express';
import CircuitBreaker from 'opossum';

export function circuitBreakerMiddleware(
  breaker: CircuitBreaker<any[], any>
) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (breaker.opened) {
      res.status(503).json({
        error: 'Service temporarily unavailable',
        retryAfter: Math.ceil(breaker.options.resetTimeout / 1000)
      });
      return;
    }
    next();
  };
}
```

### Factory for Multiple Services

```typescript
class CircuitBreakerFactory {
  private breakers: Map<string, CircuitBreaker<any[], any>> = new Map();

  create<T>(
    name: string,
    action: (...args: any[]) => Promise<T>,
    options?: Partial<CircuitBreakerOptions>
  ): CircuitBreaker<any[], T> {
    if (this.breakers.has(name)) {
      return this.breakers.get(name)!;
    }

    const breaker = createCircuitBreaker(action, options);
    this.breakers.set(name, breaker);
    return breaker;
  }

  get(name: string): CircuitBreaker<any[], any> | undefined {
    return this.breakers.get(name);
  }

  getStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    this.breakers.forEach((breaker, name) => {
      stats[name] = {
        state: breaker.opened ? 'OPEN' : 'CLOSED',
        stats: breaker.stats
      };
    });
    return stats;
  }
}

export const circuitBreakerFactory = new CircuitBreakerFactory();
```

## Important Rules

- Use `fire()` to execute protected operations
- Configure meaningful fallbacks with `fallback()`
- Monitor events for observability
- Adjust `volumeThreshold` based on expected traffic

## Example

```typescript
import express from 'express';

const app = express();
const paymentService = new PaymentService('https://api.payments.com');

app.post('/api/orders', async (req, res) => {
  try {
    const payment = await paymentService.processPayment({
      orderId: req.body.orderId,
      amount: req.body.amount,
      currency: 'USD'
    });
    
    res.json({
      orderId: req.body.orderId,
      payment,
      circuitBreakerOpen: paymentService.isOpen()
    });
  } catch (error) {
    res.status(500).json({ error: 'Order processing failed' });
  }
});

// Health check endpoint
app.get('/health/circuit-breakers', (req, res) => {
  res.json(circuitBreakerFactory.getStats());
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
