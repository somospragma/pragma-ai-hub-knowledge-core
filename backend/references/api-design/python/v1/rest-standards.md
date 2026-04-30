<!-- keywords: rest api, api design, http methods, status codes, resource naming, fastapi, pydantic, python -->
# REST Standards — Python Implementation

## Conceptual reference

For the conceptual REST design standards (naming, HTTP methods, status codes, response structure, and OpenAPI), see [`../rest-standards.md`](../rest-standards.md).

## Technology Stack

- **Framework:** FastAPI
- **Validation and models:** Pydantic v2 (`BaseModel`, `Field`, `EmailStr`)
- **Typing:** Native Python type hints (`Optional`, `List`)
- **Documentation:** Automatic OpenAPI generation by FastAPI

## Controller with FastAPI

```python
from fastapi import APIRouter, HTTPException, Query, Path, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])

class CreateCustomerRequest(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$")

class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    data: List[CustomerResponse]
    pagination: dict
    links: dict

@router.get("", response_model=PaginatedResponse)
async def list_customers(
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, pattern="^(ACTIVE|INACTIVE)$")
):
    """List customers with pagination."""
    result = await customer_service.find_all(page=page, size=size, status=status)

    return PaginatedResponse(
        data=result.items,
        pagination={
            "page": page,
            "pageSize": size,
            "totalItems": result.total,
            "totalPages": (result.total + size - 1) // size
        },
        links=build_pagination_links(page, size, result.total)
    )

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str = Path(...)):
    """Get customer by ID."""
    customer = await customer_service.find_by_id(customer_id)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )

    return customer

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(request: CreateCustomerRequest):
    """Create a new customer."""
    customer = await customer_service.create(request)
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: CreateCustomerRequest
):
    """Update customer."""
    customer = await customer_service.update(customer_id, request)

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )

    return customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str):
    """Delete customer."""
    deleted = await customer_service.delete(customer_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {customer_id} not found"
        )
```

## Tools and Resources

REST standards and best practices from the backend team — Python implementation with FastAPI.

## Purpose

_(No additional information required for this section.)_

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_
