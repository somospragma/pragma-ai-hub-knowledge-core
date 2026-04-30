<!-- keywords: dto, entity, mapping, pydantic, data transformation, python -->
# DTO-Entity Mapping — Python Implementation

## Purpose

Implementation guide for DTO-Entity mapping in Python using Pydantic, with functional examples.

## Libraries and dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
pydantic = "^2.5.0"
```

```txt
# requirements.txt
pydantic>=2.5.0
```

## Step by Step / Guidelines

### Domain entities

```python
# entities.py
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import uuid4

@dataclass
class OrderItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    id: str = field(default_factory=lambda: str(uuid4()))

@dataclass
class Order:
    customer_id: str
    items: List[OrderItem]
    total_amount: Decimal
    status: str = "PENDING"
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
```

### DTOs with Pydantic

```python
# dtos.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class OrderItemRequest(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price: Decimal = Field(..., gt=0, decimal_places=2)

class OrderRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    items: List[OrderItemRequest] = Field(..., min_length=1)
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    customer_id: str
    items: List[OrderItemResponse]
    total_amount: Decimal
    status: str
    created_date: datetime
    
    class Config:
        from_attributes = True
```

### Mapper class

```python
# mapper.py
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class OrderMapper:
    
    def to_entity(self, request: OrderRequest) -> Order:
        items = [
            OrderItem(
                product_id=item.product_id,
                product_name="",  # Will be resolved
                quantity=item.quantity,
                unit_price=item.unit_price
            )
            for item in request.items
        ]
        
        total_amount = sum(
            item.unit_price * item.quantity 
            for item in items
        )
        
        return Order(
            customer_id=request.customer_id,
            items=items,
            total_amount=total_amount
        )
    
    def to_response(self, entity: Order) -> OrderResponse:
        return OrderResponse(
            id=entity.id,
            customer_id=entity.customer_id,
            items=[
                OrderItemResponse(
                    product_id=item.product_id,
                    product_name=item.product_name,
                    quantity=item.quantity,
                    unit_price=item.unit_price
                )
                for item in entity.items
            ],
            total_amount=entity.total_amount,
            status=entity.status,
            created_date=entity.created_at
        )
    
    def to_response_list(self, entities: List[Order]) -> List[OrderResponse]:
        return [self.to_response(entity) for entity in entities]
    
    def update_entity(self, entity: Order, request: dict) -> Order:
        if 'customer_id' in request and request['customer_id']:
            entity.customer_id = request['customer_id']
        if 'items' in request and request['items']:
            entity.items = [
                OrderItem(
                    product_id=item['product_id'],
                    product_name="",
                    quantity=item['quantity'],
                    unit_price=Decimal(str(item['unit_price']))
                )
                for item in request['items']
            ]
            entity.total_amount = sum(
                item.unit_price * item.quantity 
                for item in entity.items
            )
        return entity

order_mapper = OrderMapper()
```

### Usage in Service

```python
# order_service.py
class OrderService:
    def __init__(
        self,
        order_repository: OrderRepository,
        order_mapper: OrderMapper
    ):
        self._repository = order_repository
        self._mapper = order_mapper
    
    def create_order(self, request: OrderRequest) -> OrderResponse:
        entity = self._mapper.to_entity(request)
        saved = self._repository.save(entity)
        return self._mapper.to_response(saved)
    
    def update_order(self, id: str, request: dict) -> OrderResponse:
        entity = self._repository.find_by_id(id)
        if not entity:
            raise OrderNotFoundError(id)
        updated = self._mapper.update_entity(entity, request)
        saved = self._repository.save(updated)
        return self._mapper.to_response(saved)
```

## Mocks and fixtures

### Mapper test

```python
import pytest
from decimal import Decimal

class TestOrderMapper:
    
    def test_to_entity(self):
        request = OrderRequest(
            customer_id="cust-123",
            items=[
                OrderItemRequest(product_id="prod-1", quantity=2, unit_price=Decimal("25.00"))
            ],
            currency="USD"
        )
        mapper = OrderMapper()
        
        entity = mapper.to_entity(request)
        
        assert entity.status == "PENDING"
        assert entity.total_amount == Decimal("50.00")
        assert entity.created_at is not None
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
