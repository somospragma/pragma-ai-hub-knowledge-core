<!-- keywords: retry, timeout, exponential backoff, tenacity, fault tolerance, python -->
# Retry and Timeout - Python Implementation

## Purpose

Implement retry patterns with exponential backoff and timeout in Python applications using tenacity.

## Scope of Application

- When configuring retries on calls to external services
- When implementing timeouts with asyncio
- When using tenacity decorators

## Main content

### Dependencies

```txt
# requirements.txt
tenacity>=8.2.0
httpx>=0.26.0
```

### Retry Utilities

```python
import asyncio
import random
from typing import TypeVar, Callable, Awaitable, Optional
from functools import wraps
from dataclasses import dataclass
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)

@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 0.5
    max_delay: float = 10.0
    multiplier: float = 2.0
    jitter_factor: float = 0.5
    retryable_exceptions: tuple = (IOError, TimeoutError, ConnectionError)


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    exponential_delay = min(
        config.initial_delay * (config.multiplier ** attempt),
        config.max_delay
    )
    jitter = exponential_delay * config.jitter_factor * (random.random() * 2 - 1)
    return max(0, exponential_delay + jitter)


def retry(config: Optional[RetryConfig] = None):
    """Decorator for synchronous retry"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"Retry attempt {attempt + 1} after {delay:.2f}s: {e}"
                        )
                        import time
                        time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def async_retry(config: Optional[RetryConfig] = None):
    """Decorator for asynchronous retry"""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = calculate_delay(attempt, config)
                        logger.warning(
                            f"Retry attempt {attempt + 1} after {delay:.2f}s: {e}"
                        )
                        await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator
```

### Timeout Utility

```python
async def with_timeout(
    coro: Awaitable[T],
    timeout_seconds: float
) -> T:
    """Execute coroutine with timeout"""
    return await asyncio.wait_for(coro, timeout=timeout_seconds)


async def resilient_call(
    operation: Callable[..., Awaitable[T]],
    *args,
    timeout_seconds: float = 5.0,
    retry_config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """Combine retry + timeout"""
    config = retry_config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await asyncio.wait_for(
                operation(*args, **kwargs),
                timeout=timeout_seconds
            )
        except (asyncio.TimeoutError, *config.retryable_exceptions) as e:
            last_exception = e
            if attempt < config.max_attempts - 1:
                delay = calculate_delay(attempt, config)
                logger.warning(f"Retry {attempt + 1} after {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
    
    raise last_exception
```

### Usage with tenacity

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
    before_sleep_log
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=0.5, max=10, jitter=5),
    retry=retry_if_exception_type((IOError, TimeoutError, ConnectionError)),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
async def call_external_service(request: dict) -> dict:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(
            "https://api.external.com/endpoint",
            json=request
        )
        response.raise_for_status()
        return response.json()
```

### Service with Retry

```python
import httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class PaymentRequest:
    order_id: str
    amount: float
    currency: str

@dataclass
class PaymentResult:
    transaction_id: str
    status: str
    message: Optional[str] = None


class PaymentService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.retry_config = RetryConfig(
            max_attempts=3,
            initial_delay=1.0,
            retryable_exceptions=(IOError, TimeoutError, httpx.HTTPStatusError)
        )
    
    @async_retry(RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        retryable_exceptions=(IOError, TimeoutError)
    ))
    async def process_payment(self, request: PaymentRequest) -> PaymentResult:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{self.base_url}/payments",
                json={
                    "orderId": request.order_id,
                    "amount": request.amount,
                    "currency": request.currency
                }
            )
            response.raise_for_status()
            data = response.json()
            return PaymentResult(**data)
```

### Usage with FastAPI

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()
payment_service = PaymentService("https://api.payments.com")

@app.post("/api/orders")
async def create_order(order: dict):
    try:
        payment = await payment_service.process_payment(
            PaymentRequest(
                order_id=order["orderId"],
                amount=order["amount"],
                currency="USD"
            )
        )
        return {"orderId": order["orderId"], "payment": payment}
    except Exception as e:
        logger.error(f"Order creation failed: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")
```

## Important Rules

- Use `wait_exponential_jitter` from tenacity for backoff with jitter
- Configure `retry_if_exception_type` to only retry transient errors
- Combine `asyncio.wait_for` with retry for timeout + retries
- Use `before_sleep_log` for retry logging

## Example

```python
# Complete resilient HTTP client
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential_jitter

async def resilient_http_call(url: str, data: dict) -> dict:
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.5, max=10)
    ):
        with attempt:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
