---
id: backend-skill-node-express-resiliencia
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Resiliencia — Node Express

## Propósito

Guía de implementación de patrones de resiliencia en microservicios Node.js/Express con TypeScript: Circuit Breaker (opossum), Retry con backoff exponencial, Timeouts y Bulkhead (bottleneck).

---

## 1. Circuit Breaker con Opossum

### Dependencias

```json
{
  "dependencies": {
    "opossum": "^8.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0"
  }
}
```

### Configuración del Circuit Breaker

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
  const breaker = new CircuitBreaker(action, { ...defaultOptions, ...options });

  breaker.on('open', () => console.log('Circuit breaker OPEN'));
  breaker.on('halfOpen', () => console.log('Circuit breaker HALF-OPEN'));
  breaker.on('close', () => console.log('Circuit breaker CLOSED'));
  breaker.on('fallback', (result) => console.log('Fallback called:', result));

  return breaker;
}
```

### Servicio con Circuit Breaker y Fallback

```typescript
import axios from 'axios';
import CircuitBreaker from 'opossum';

interface PaymentRequest { orderId: string; amount: number; currency: string; }
interface PaymentResponse { transactionId: string; status: string; message?: string; }

export class PaymentService {
  private circuitBreaker: CircuitBreaker<[PaymentRequest], PaymentResponse>;

  constructor(private baseUrl: string) {
    this.circuitBreaker = createCircuitBreaker(
      this.callPaymentApi.bind(this),
      { timeout: 5000, errorThresholdPercentage: 50, resetTimeout: 30000 }
    );

    this.circuitBreaker.fallback((request: PaymentRequest) => ({
      transactionId: 'FALLBACK',
      status: 'PENDING',
      message: 'Payment queued for retry'
    }));
  }

  private async callPaymentApi(request: PaymentRequest): Promise<PaymentResponse> {
    const response = await axios.post<PaymentResponse>(`${this.baseUrl}/payments`, request, { timeout: 5000 });
    return response.data;
  }

  async processPayment(request: PaymentRequest): Promise<PaymentResponse> {
    return this.circuitBreaker.fire(request);
  }

  isOpen(): boolean { return this.circuitBreaker.opened; }
  getStats() { return this.circuitBreaker.stats; }
}
```

### Factory para múltiples servicios

```typescript
class CircuitBreakerFactory {
  private breakers: Map<string, CircuitBreaker<any[], any>> = new Map();

  create<T>(name: string, action: (...args: any[]) => Promise<T>, options?: Partial<CircuitBreakerOptions>): CircuitBreaker<any[], T> {
    if (this.breakers.has(name)) return this.breakers.get(name)!;
    const breaker = createCircuitBreaker(action, options);
    this.breakers.set(name, breaker);
    return breaker;
  }

  getStats(): Record<string, any> {
    const stats: Record<string, any> = {};
    this.breakers.forEach((breaker, name) => {
      stats[name] = { state: breaker.opened ? 'OPEN' : 'CLOSED', stats: breaker.stats };
    });
    return stats;
  }
}

export const circuitBreakerFactory = new CircuitBreakerFactory();
```

### Middleware Express

```typescript
import { Request, Response, NextFunction } from 'express';

export function circuitBreakerMiddleware(breaker: CircuitBreaker<any[], any>) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (breaker.opened) {
      return res.status(503).json({
        error: 'Service temporarily unavailable',
        retryAfter: Math.ceil(breaker.options.resetTimeout / 1000)
      });
    }
    next();
  };
}
```

---

## 2. Retry con Backoff Exponencial

### Dependencias

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "axios-retry": "^4.0.0"
  }
}
```

### Utilidad de retry genérica

```typescript
interface RetryConfig {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  multiplier: number;
  jitterFactor: number;
  retryableErrors?: (error: Error) => boolean;
}

const defaultRetryConfig: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 500,
  maxDelayMs: 10000,
  multiplier: 2,
  jitterFactor: 0.5,
  retryableErrors: (error) => {
    const msg = error.message.toLowerCase();
    return msg.includes('timeout') || msg.includes('econnrefused') || msg.includes('503');
  }
};

export async function withRetry<T>(operation: () => Promise<T>, config: Partial<RetryConfig> = {}): Promise<T> {
  const cfg = { ...defaultRetryConfig, ...config };
  let lastError: Error;

  for (let attempt = 0; attempt < cfg.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (!cfg.retryableErrors?.(lastError)) throw lastError;
      if (attempt < cfg.maxAttempts - 1) {
        const delay = Math.min(cfg.initialDelayMs * Math.pow(cfg.multiplier, attempt), cfg.maxDelayMs);
        const jitter = delay * cfg.jitterFactor * (Math.random() * 2 - 1);
        await new Promise(resolve => setTimeout(resolve, Math.max(0, delay + jitter)));
      }
    }
  }
  throw lastError!;
}
```

### Timeout utility

```typescript
export async function withTimeout<T>(operation: () => Promise<T>, timeoutMs: number): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('Operation timed out')), timeoutMs);
  });
  return Promise.race([operation(), timeoutPromise]);
}

// Combinación retry + timeout
export async function resilientCall<T>(
  operation: () => Promise<T>,
  options: { timeoutMs: number; retryConfig?: Partial<RetryConfig> }
): Promise<T> {
  return withRetry(() => withTimeout(operation, options.timeoutMs), options.retryConfig);
}
```

### Configuración con axios-retry

```typescript
import axios from 'axios';
import axiosRetry from 'axios-retry';

const client = axios.create({ baseURL: 'https://api.external.com', timeout: 5000 });

axiosRetry(client, {
  retries: 3,
  retryDelay: (retryCount) => {
    const delay = Math.min(500 * Math.pow(2, retryCount), 10000);
    const jitter = delay * 0.5 * Math.random();
    return delay + jitter;
  },
  retryCondition: (error) => {
    return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
           error.response?.status === 503 ||
           error.response?.status === 429;
  },
  onRetry: (retryCount, error, requestConfig) => {
    console.log(`Retry ${retryCount} for ${requestConfig.url}`);
  }
});
```

---

## 3. Bulkhead con Bottleneck

### Dependencias

```json
{
  "dependencies": {
    "bottleneck": "^2.19.5",
    "express-rate-limit": "^7.1.0",
    "rate-limit-redis": "^4.2.0"
  }
}
```

### Configuración del Bulkhead

```typescript
import Bottleneck from 'bottleneck';

class BulkheadManager {
  private limiters: Map<string, Bottleneck> = new Map();

  createBulkhead(name: string, config: { maxConcurrent: number; minTime?: number }): Bottleneck {
    const limiter = new Bottleneck({ maxConcurrent: config.maxConcurrent, minTime: config.minTime || 0 });
    limiter.on('failed', (error, jobInfo) => console.error(`Job ${jobInfo.options.id} failed:`, error));
    limiter.on('dropped', () => console.warn('Job dropped: bulkhead full'));
    this.limiters.set(name, limiter);
    return limiter;
  }

  get(name: string): Bottleneck | undefined { return this.limiters.get(name); }
}

export const bulkheadManager = new BulkheadManager();
```

### Servicio con Bulkhead

```typescript
class PaymentServiceWithBulkhead {
  private bulkhead: Bottleneck;

  constructor() {
    this.bulkhead = bulkheadManager.createBulkhead('payment', { maxConcurrent: 10, minTime: 100 });
  }

  async processPayment(request: PaymentRequest): Promise<PaymentResult> {
    return this.bulkhead.schedule({ id: request.orderId, priority: 5 }, () => this.paymentGateway.process(request));
  }
}
```

### Rate Limiting con Express y Redis

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });

const apiLimiter = rateLimit({
  store: new RedisStore({ sendCommand: (...args: string[]) => redisClient.sendCommand(args) }),
  windowMs: 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.headers['x-tenant-id'] as string || req.ip,
  handler: (req, res) => {
    res.status(429).json({
      type: 'https://api.company.com/errors/rate-limit-exceeded',
      title: 'Too Many Requests',
      status: 429,
      detail: 'Rate limit exceeded. Please retry after some time.',
      retryAfter: res.getHeader('Retry-After')
    });
  }
});

app.use('/api', apiLimiter);
```

---

## Health Check para Circuit Breakers

```typescript
app.get('/health/circuit-breakers', (req, res) => {
  res.json(circuitBreakerFactory.getStats());
});
```

---

## Reglas Importantes

- **Circuit Breaker**: Usar `fire()` para ejecutar operaciones protegidas; configurar fallbacks significativos
- **Retry**: Siempre usar jitter para evitar thundering herd; solo reintentar errores transitorios
- **Timeout**: Combinar con retry para operaciones resilientes
- **Bulkhead**: Usar `schedule()` de bottleneck; configurar `maxConcurrent` según capacidad del servicio downstream
- **Rate Limiting**: Usar Redis para rate limiting distribuido; implementar `keyGenerator` por tenant
- **Monitoreo**: Exponer métricas de circuit breakers en endpoint de health
