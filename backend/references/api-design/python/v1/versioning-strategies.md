<!-- keywords: api versioning, url versioning, header versioning, fastapi routers, pydantic models, backward compatibility, python -->
# API Versioning Strategies - Python Implementation

## Purpose

Implementation of REST API versioning in Python with FastAPI, including routers per version, versioned Pydantic models, and header-based versioning.

## Reference

Main language-agnostic document: [../versioning-strategies.md](../versioning-strategies.md)

## Versioned Routers and Models with FastAPI

```python
# versioned_api.py
from fastapi import FastAPI, APIRouter, Header, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Routers per version
v1_router = APIRouter(prefix="/v1", tags=["v1"])
v2_router = APIRouter(prefix="/v2", tags=["v2"])

# V1 Models
class OrderResponseV1(BaseModel):
    id: str
    customer_id: str
    total: float
    status: str

# V2 Models (extended)
class OrderItemV2(BaseModel):
    product_id: str
    quantity: int
    unit_price: float

class OrderResponseV2(BaseModel):
    id: str
    customer_id: str
    items: List[OrderItemV2]
    total_amount: float
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

# V1 Endpoints (deprecated)
@v1_router.get("/orders", response_model=List[OrderResponseV1], deprecated=True)
async def list_orders_v1():
    """
    **DEPRECATED**: Use /v2/orders instead.
    Sunset: 2024-06-01
    """
    orders = await order_service.list_orders_v1()
    return JSONResponse(
        content=[order.dict() for order in orders],
        headers={
            "Deprecation": "true",
            "Sunset": "Sat, 01 Jun 2024 00:00:00 GMT",
            "Link": '</v2/orders>; rel="successor-version"'
        }
    )

# V2 Endpoints (current)
@v2_router.get("/orders", response_model=List[OrderResponseV2])
async def list_orders_v2(
    page: int = 0,
    size: int = 20,
    status: Optional[str] = None
):
    """List orders with pagination and filters."""
    return await order_service.list_orders_v2(page, size, status)

# Mount routers
app.include_router(v1_router)
app.include_router(v2_router)

# Header-based versioning (alternative)
async def get_api_version(
    api_version: Optional[str] = Header(None, alias="Api-Version")
) -> int:
    if api_version is None:
        return 2  # Default to latest version
    try:
        return int(api_version)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Api-Version header")

@app.get("/orders")
async def list_orders(version: int = Depends(get_api_version)):
    if version == 1:
        return await order_service.list_orders_v1()
    return await order_service.list_orders_v2()
```

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
