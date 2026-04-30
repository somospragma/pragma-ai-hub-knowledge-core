<!-- keywords: bulkhead, rate limiting, bottleneck, express-rate-limit, resource isolation, overload protection, typescript, nodejs -->
# Bulkhead and Rate Limiting - TypeScript Implementation

## Purpose

Implement bulkhead and rate limiting patterns in Node.js/TypeScript applications using bottleneck and express-rate-limit.

## Scope of Application

- When configuring bulkheads with bottleneck
- When implementing rate limiting in Express
- When protecting services from overload

## Main content

### Dependencies

```json
{
  "dependencies": {
    "bottleneck": "^2.19.5",
    "express-rate-limit": "^7.1.0",
    "rate-limit-redis": "^4.2.0",
    "redis": "^4.6.0"
  }
}
```

### Bulkhead Configuration

```typescript
import Bottleneck from 'bottleneck';

interface BulkheadConfig {
  maxConcurrent: number;
  minTime?: number;
  reservoir?: number;
  reservoirRefreshInterval?: number;
  reservoirRefreshAmount?: number;
}

class BulkheadManager {
  private limiters: Map<string, Bottleneck> = new Map();
  
  createBulkhead(name: string, config: BulkheadConfig): Bottleneck {
    const limiter = new Bottleneck({
      maxConcurrent: config.maxConcurrent,
      minTime: config.minTime || 0,
      reservoir: config.reservoir,
      reservoirRefreshInterval: config.reservoirRefreshInterval,
      reservoirRefreshAmount: config.reservoirRefreshAmount
    });
    
    limiter.on('failed', (error, jobInfo) => {
      console.error(`Job ${jobInfo.options.id} failed:`, error);
    });
    
    limiter.on('dropped', (dropped) => {
      console.warn(`Job dropped due to bulkhead full`);
    });
    
    this.limiters.set(name, limiter);
    return limiter;
  }
  
  get(name: string): Bottleneck | undefined {
    return this.limiters.get(name);
  }
}

export const bulkheadManager = new BulkheadManager();
```

### Service with Bulkhead

```typescript
class PaymentService {
  private bulkhead: Bottleneck;
  
  constructor() {
    this.bulkhead = bulkheadManager.createBulkhead('payment', {
      maxConcurrent: 10,
      minTime: 100
    });
  }
  
  async processPayment(request: PaymentRequest): Promise<PaymentResult> {
    return this.bulkhead.schedule(
      { id: request.id, priority: 5 },
      () => this.paymentGateway.process(request)
    );
  }
}
```

### Sliding Window Rate Limiter

```typescript
interface RateLimitConfig {
  windowMs: number;
  maxRequests: number;
}

class SlidingWindowRateLimiter {
  private windows: Map<string, number[]> = new Map();
  private config: RateLimitConfig;
  
  constructor(config: RateLimitConfig) {
    this.config = config;
  }
  
  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;
    
    let timestamps = this.windows.get(key) || [];
    timestamps = timestamps.filter(ts => ts > windowStart);
    
    if (timestamps.length >= this.config.maxRequests) {
      return false;
    }
    
    timestamps.push(now);
    this.windows.set(key, timestamps);
    return true;
  }
  
  getRemainingRequests(key: string): number {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;
    const timestamps = this.windows.get(key) || [];
    const validTimestamps = timestamps.filter(ts => ts > windowStart);
    return Math.max(0, this.config.maxRequests - validTimestamps.length);
  }
}
```

### Express Middleware with Redis

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });

const apiLimiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args: string[]) => redisClient.sendCommand(args)
  }),
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

// Usage
app.use('/api', apiLimiter);
```

### Multi-tenant Rate Limiter

```typescript
class TenantRateLimiter {
  private limiters: Map<string, SlidingWindowRateLimiter> = new Map();
  private tenantConfigs: Map<string, RateLimitConfig>;
  
  constructor(defaultConfig: RateLimitConfig) {
    this.tenantConfigs = new Map();
    this.tenantConfigs.set('default', defaultConfig);
  }
  
  setTenantConfig(tenantId: string, config: RateLimitConfig): void {
    this.tenantConfigs.set(tenantId, config);
  }
  
  checkRateLimit(tenantId: string): { allowed: boolean; remaining: number } {
    const config = this.tenantConfigs.get(tenantId) || 
                   this.tenantConfigs.get('default')!;
    
    if (!this.limiters.has(tenantId)) {
      this.limiters.set(tenantId, new SlidingWindowRateLimiter(config));
    }
    
    const limiter = this.limiters.get(tenantId)!;
    return {
      allowed: limiter.isAllowed(tenantId),
      remaining: limiter.getRemainingRequests(tenantId)
    };
  }
}

// Middleware
function tenantRateLimitMiddleware(limiter: TenantRateLimiter) {
  return (req: Request, res: Response, next: NextFunction) => {
    const tenantId = req.headers['x-tenant-id'] as string || 'default';
    const result = limiter.checkRateLimit(tenantId);
    
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    
    if (!result.allowed) {
      res.status(429).json({
        error: 'Rate limit exceeded',
        retryAfter: 60
      });
      return;
    }
    
    next();
  };
}
```

## Important Rules

- Use `schedule()` from bottleneck for bulkhead operations
- Configure `standardHeaders: true` for RFC 6585 headers
- Use Redis for distributed rate limiting
- Implement `keyGenerator` to identify tenants

## Example

```typescript
import express from 'express';

const app = express();
const tenantLimiter = new TenantRateLimiter({
  windowMs: 60000,
  maxRequests: 100
});

// Configure limits per tier
tenantLimiter.setTenantConfig('premium', { windowMs: 60000, maxRequests: 1000 });
tenantLimiter.setTenantConfig('standard', { windowMs: 60000, maxRequests: 100 });

app.use('/api', tenantRateLimitMiddleware(tenantLimiter));

app.get('/api/resource', async (req, res) => {
  const result = await paymentService.processPayment(req.body);
  res.json(result);
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
