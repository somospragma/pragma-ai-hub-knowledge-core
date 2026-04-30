<!-- keywords: bulkhead, rate limiting, asyncio, limits, resource isolation, overload protection, python -->
# Bulkhead and Rate Limiting - Python Implementation

## Purpose

Implement bulkhead and rate limiting patterns in Python applications using asyncio and limits.

## Scope of Application

- When configuring bulkheads with asyncio.Semaphore
- When implementing rate limiting in FastAPI
- When protecting services from overload

## Main content

### Dependencies

```txt
# requirements.txt
fastapi>=0.109.0
limits>=3.7.0
redis>=5.0.0
```

### Bulkhead with asyncio

```python
import asyncio
from dataclasses import dataclass
from typing import TypeVar, Callable, Awaitable

T = TypeVar('T')

@dataclass
class BulkheadConfig:
    max_concurrent: int = 10
    max_wait_time: float = 1.0

class AsyncBulkhead:
    def __init__(self, config: BulkheadConfig):
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.max_wait_time = config.max_wait_time
    
    async def execute(self, operation: Callable[[], Awaitable[T]]) -> T:
        try:
            await asyncio.wait_for(
                self.semaphore.acquire(),
                timeout=self.max_wait_time
            )
        except asyncio.TimeoutError:
            raise BulkheadFullException("Bulkhead is full")
        
        try:
            return await operation()
        finally:
            self.semaphore.release()

class BulkheadFullException(Exception):
    pass
```


### Token Bucket Rate Limiter

```python
import asyncio
import time
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    requests_per_second: int = 100
    burst_size: int = 10

class TokenBucketRateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.rate = config.requests_per_second
        self.burst_size = config.burst_size
        self.tokens = config.burst_size
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(
                self.burst_size,
                self.tokens + elapsed * self.rate
            )
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False

class TenantRateLimiter:
    def __init__(self, default_config: RateLimitConfig):
        self.default_config = default_config
        self.limiters: dict[str, TokenBucketRateLimiter] = {}
    
    def get_limiter(self, tenant_id: str) -> TokenBucketRateLimiter:
        if tenant_id not in self.limiters:
            self.limiters[tenant_id] = TokenBucketRateLimiter(self.default_config)
        return self.limiters[tenant_id]
    
    async def check_rate_limit(self, tenant_id: str) -> bool:
        limiter = self.get_limiter(tenant_id)
        return await limiter.acquire()
```

### FastAPI Middleware

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: TenantRateLimiter):
        super().__init__(app)
        self.limiter = limiter
    
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get('X-Tenant-ID', 'default')
        
        if not await self.limiter.check_rate_limit(tenant_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "1"}
            )
        
        return await call_next(request)
```

### Service with Bulkhead

```python
class PaymentService:
    def __init__(self):
        self.bulkhead = AsyncBulkhead(BulkheadConfig(max_concurrent=10))
    
    async def process_payment(self, request: dict) -> dict:
        try:
            return await self.bulkhead.execute(
                lambda: self._call_payment_api(request)
            )
        except BulkheadFullException:
            return {"status": "QUEUED", "message": "Service busy"}
    
    async def _call_payment_api(self, request: dict) -> dict:
        # Call to external service
        pass
```

## Important Rules

- Use `asyncio.Semaphore` for async bulkhead
- Implement Token Bucket for flexible rate limiting
- Use middleware to apply limits globally
- Return 429 with Retry-After header

## Example

```python
from fastapi import FastAPI

app = FastAPI()
tenant_limiter = TenantRateLimiter(RateLimitConfig(requests_per_second=100))
app.add_middleware(RateLimitMiddleware, limiter=tenant_limiter)

payment_service = PaymentService()

@app.post("/api/payments")
async def create_payment(request: dict):
    return await payment_service.process_payment(request)
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
