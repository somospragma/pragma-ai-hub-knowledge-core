<!-- keywords: input validation, pydantic, data validation, sanitization, python -->
# Input Validation — Python Implementation

## Purpose

Implementation guide for input validation in Python using Pydantic, with functional examples.

## Libraries and dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.5.0"
bleach = "^6.1.0"
```

```txt
# requirements.txt
pydantic>=2.5.0
bleach>=6.1.0
```

## Step by Step / Guidelines

### Validation schemas with Pydantic

```python
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional
from datetime import date
from decimal import Decimal
import re

class OrderItemRequest(BaseModel):
    product_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9-]+$',
        description="Product identifier"
    )
    quantity: int = Field(
        ...,
        ge=1,
        le=1000,
        description="Quantity to order"
    )
    unit_price: Decimal = Field(
        ...,
        gt=0,
        le=Decimal('999999.99'),
        decimal_places=2,
        description="Price per unit"
    )

```python
class OrderRequest(BaseModel):
    customer_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[a-zA-Z0-9-]+$'
    )
    items: List[OrderItemRequest] = Field(
        ...,
        min_length=1,
        max_length=100
    )
    currency: str = Field(
        ...,
        pattern=r'^[A-Z]{3}$',
        description="3-letter ISO currency code"
    )
    notification_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    delivery_date: Optional[date] = None
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('delivery_date')
    @classmethod
    def validate_delivery_date(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        if v <= date.today():
            raise ValueError('Delivery date must be in the future')
        return v
    
    class Config:
        str_strip_whitespace = True
```

### Validation error handler (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = [
        {
            'field': '.'.join(str(loc) for loc in error['loc']),
            'message': error['msg']
        }
        for error in exc.errors()
    ]
    
    return JSONResponse(
        status_code=400,
        content={
            'type': 'https://api.company.com/errors/validation-error',
            'title': 'Validation Error',
            'status': 400,
            'detail': 'Request validation failed',
            'errors': errors
        }
    )

@app.post('/orders')
async def create_order(order: OrderRequest):
    # order is already validated
    return {'status': 'created', 'customer_id': order.customer_id}
```

### Sanitization

```python
import html
import re
from typing import Optional
import bleach

def sanitize_html(input_str: str, allowed_tags: list = None) -> str:
    if allowed_tags is None:
        allowed_tags = ['b', 'i', 'u', 'br']
    return bleach.clean(input_str, tags=allowed_tags, strip=True)

def sanitize_for_log(input_str: str) -> str:
    return re.sub(r'[\r\n\x00-\x1f\x7f-\x9f]', ' ', input_str)

def escape_html(input_str: str) -> str:
    return html.escape(input_str)
```

## Mocks and fixtures

### Validation test

```python
import pytest
from pydantic import ValidationError

def test_valid_order_request():
    request = OrderRequest(
        customer_id="cust-123",
        items=[
            OrderItemRequest(product_id="prod-1", quantity=2, unit_price=Decimal("25.00"))
        ],
        currency="USD"
    )
    assert request.customer_id == "cust-123"

def test_invalid_order_request():
    with pytest.raises(ValidationError) as exc_info:
        OrderRequest(
            customer_id="",
            items=[],
            currency="INVALID"
        )
    
    errors = exc_info.value.errors()
    assert len(errors) > 0
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
