<!-- keywords: circuit breaker, pybreaker, cascading failure, fault tolerance, python -->
# Circuit Breaker - Python Implementation

## Purpose

Implement the Circuit Breaker pattern in Python applications using pybreaker.

## Scope of Application

- When implementing calls to external services in Python
- When configuring circuit breakers with pybreaker
- When implementing fallbacks for unavailable services

## Main content

### Dependencies

```txt
# requirements.txt
pybreaker>=1.0.0
httpx>=0.26.0
```

### Circuit Breaker Configuration

```python
import pybreaker
from functools import wraps
from typing import Callable, TypeVar, Any
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb: pybreaker.CircuitBreaker, old_state, new_state):
        logger.info(f"Circuit breaker {cb.name} changed from {old_state} to {new_state}")
    
    def failure(self, cb: pybreaker.CircuitBreaker, exc: Exception):
        logger.warning(f"Circuit breaker {cb.name} recorded failure: {exc}")
    
    def success(self, cb: pybreaker.CircuitBreaker):
        logger.debug(f"Circuit breaker {cb.name} recorded success")


def create_circuit_breaker(
    name: str,
    fail_max: int = 5,
    reset_timeout: int = 30,
    exclude: tuple = ()
) -> pybreaker.CircuitBreaker:
    return pybreaker.CircuitBreaker(
        name=name,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        exclude=exclude,
        listeners=[CircuitBreakerListener()]
    )
```

### Service with Circuit Breaker

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
class PaymentResponse:
    transaction_id: str
    status: str
    message: Optional[str] = None
    
    @classmethod
    def fallback(cls, message: str) -> "PaymentResponse":
        return cls(
            transaction_id="FALLBACK",
            status="PENDING",
            message=message
        )


class PaymentService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=5.0)
        self.circuit_breaker = create_circuit_breaker(
            name="payment_service",
            fail_max=5,
            reset_timeout=30
        )
    
    async def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        try:
            return await self._call_with_circuit_breaker(request)
        except pybreaker.CircuitBreakerError:
            logger.warning("Circuit breaker is open, returning fallback")
            return PaymentResponse.fallback("Service temporarily unavailable")
    
    async def _call_with_circuit_breaker(
        self, 
        request: PaymentRequest
    ) -> PaymentResponse:
        def sync_call():
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                self._call_payment_api(request)
            )
        
        return self.circuit_breaker.call(sync_call)
    
    async def _call_payment_api(self, request: PaymentRequest) -> PaymentResponse:
        response = await self.client.post(
            f"{self.base_url}/payments",
            json={
                "orderId": request.order_id,
                "amount": request.amount,
                "currency": request.currency
            }
        )
        response.raise_for_status()
        data = response.json()
        return PaymentResponse(**data)
```

### Decorator with Fallback

```python
from typing import Callable, TypeVar, ParamSpec, Awaitable

P = ParamSpec('P')
R = TypeVar('R')

def with_circuit_breaker(
    circuit_breaker: pybreaker.CircuitBreaker,
    fallback: Callable[P, R]
):
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return circuit_breaker.call(func, *args, **kwargs)
            except pybreaker.CircuitBreakerError:
                return fallback(*args, **kwargs)
        return wrapper
    return decorator


def async_with_circuit_breaker(
    circuit_breaker: pybreaker.CircuitBreaker,
    fallback: Callable[P, Awaitable[R]]
):
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                # pybreaker does not natively support async
                return await func(*args, **kwargs)
            except (IOError, TimeoutError) as e:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(e))
                return await fallback(*args, **kwargs)
            except pybreaker.CircuitBreakerError:
                return await fallback(*args, **kwargs)
        return wrapper
    return decorator
```

### Usage with FastAPI

```python
from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

payment_service: PaymentService

@asynccontextmanager
async def lifespan(app: FastAPI):
    global payment_service
    payment_service = PaymentService("https://api.payments.com")
    yield
    await payment_service.client.aclose()

app = FastAPI(lifespan=lifespan)

@app.post("/api/orders")
async def create_order(order: dict):
    payment = await payment_service.process_payment(
        PaymentRequest(
            order_id=order["orderId"],
            amount=order["amount"],
            currency="USD"
        )
    )
    
    return {
        "orderId": order["orderId"],
        "payment": {
            "transactionId": payment.transaction_id,
            "status": payment.status,
            "message": payment.message
        }
    }

@app.get("/health/circuit-breakers")
async def circuit_breaker_health():
    cb = payment_service.circuit_breaker
    return {
        "payment_service": {
            "state": cb.current_state,
            "fail_counter": cb.fail_counter,
            "fail_max": cb.fail_max
        }
    }
```

## Important Rules

- pybreaker does not natively support async, use wrappers
- Configure `exclude` for exceptions that should not count as failures
- Use listeners for monitoring and alerts
- Implement meaningful business fallbacks

## Example

```python
# Simple usage with decorator
payment_breaker = create_circuit_breaker("payments")

def payment_fallback(request: PaymentRequest) -> PaymentResponse:
    return PaymentResponse.fallback("Circuit open")

@with_circuit_breaker(payment_breaker, payment_fallback)
def process_payment(request: PaymentRequest) -> PaymentResponse:
    # Call to external service
    response = httpx.post(
        "https://api.payments.com/payments",
        json={"orderId": request.order_id, "amount": request.amount}
    )
    response.raise_for_status()
    return PaymentResponse(**response.json())
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
