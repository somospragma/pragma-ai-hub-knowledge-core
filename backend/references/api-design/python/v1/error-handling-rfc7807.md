<!-- keywords: rfc7807, error handling, problem details, http error, rest api errors, fastapi, exception handler, python -->
# RFC 7807 Error Handling - Python Implementation

## Purpose

Implement the RFC 7807 standard for error handling in Python applications with FastAPI.

## Scope of Application

- When implementing exception handlers in FastAPI
- When creating consistent error responses in REST APIs
- When integrating Pydantic validation with RFC 7807 responses

## Main content

### Dependencies

```txt
# requirements.txt
fastapi>=0.109.0
pydantic>=2.5.0
uvicorn>=0.27.0
```

### RFC 7807 Error Model

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ErrorType(Enum):
    VALIDATION_ERROR = ("validation-error", "Validation Error", 400)
    RESOURCE_NOT_FOUND = ("resource-not-found", "Resource Not Found", 404)
    CONFLICT = ("conflict", "Resource Conflict", 409)
    UNAUTHORIZED = ("unauthorized", "Unauthorized", 401)
    FORBIDDEN = ("forbidden", "Forbidden", 403)
    INTERNAL_ERROR = ("internal-error", "Internal Server Error", 500)
    SERVICE_UNAVAILABLE = ("service-unavailable", "Service Unavailable", 503)
    
    @property
    def code(self) -> str:
        return self.value[0]
    
    @property
    def title(self) -> str:
        return self.value[1]
    
    @property
    def status(self) -> int:
        return self.value[2]
    
    @property
    def type_uri(self) -> str:
        return f"https://api.example.com/errors/{self.code}"


@dataclass
class FieldError:
    field: str
    message: str


@dataclass
class ProblemDetail:
    type: str
    title: str
    status: int
    detail: Optional[str] = None
    instance: Optional[str] = None
    trace_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    errors: Optional[List[FieldError]] = None
    
    @classmethod
    def from_error_type(
        cls,
        error_type: ErrorType,
        detail: Optional[str] = None,
        instance: Optional[str] = None,
        errors: Optional[List[FieldError]] = None
    ) -> "ProblemDetail":
        return cls(
            type=error_type.type_uri,
            title=error_type.title,
            status=error_type.status,
            detail=detail,
            instance=instance,
            errors=errors
        )
    
    def to_dict(self) -> dict:
        result = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "timestamp": self.timestamp
        }
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        if self.trace_id:
            result["traceId"] = self.trace_id
        if self.errors:
            result["errors"] = [
                {"field": e.field, "message": e.message} 
                for e in self.errors
            ]
        return result
```

### Custom Exceptions

```python
class AppException(Exception):
    def __init__(
        self,
        error_type: ErrorType,
        detail: str,
        errors: Optional[List[FieldError]] = None
    ):
        self.error_type = error_type
        self.detail = detail
        self.errors = errors
        super().__init__(detail)


class ResourceNotFoundException(AppException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            ErrorType.RESOURCE_NOT_FOUND,
            f"{resource_type} with id '{resource_id}' not found"
        )


class ValidationException(AppException):
    def __init__(self, errors: List[FieldError]):
        super().__init__(
            ErrorType.VALIDATION_ERROR,
            "Request validation failed",
            errors
        )
```

### FastAPI Exception Handlers

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    errors = [
        FieldError(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"]
        )
        for error in exc.errors()
    ]
    
    problem = ProblemDetail.from_error_type(
        ErrorType.VALIDATION_ERROR,
        detail="Request validation failed",
        instance=str(request.url.path),
        errors=errors
    )
    problem.trace_id = request.headers.get("x-trace-id")
    
    return JSONResponse(
        status_code=problem.status,
        content=problem.to_dict(),
        media_type="application/problem+json"
    )


@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request, 
    exc: AppException
) -> JSONResponse:
    problem = ProblemDetail.from_error_type(
        exc.error_type,
        detail=exc.detail,
        instance=str(request.url.path),
        errors=exc.errors
    )
    problem.trace_id = request.headers.get("x-trace-id")
    
    return JSONResponse(
        status_code=problem.status,
        content=problem.to_dict(),
        media_type="application/problem+json"
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    import logging
    logging.exception("Unexpected error")
    
    problem = ProblemDetail.from_error_type(
        ErrorType.INTERNAL_ERROR,
        detail="An unexpected error occurred",
        instance=str(request.url.path)
    )
    problem.trace_id = request.headers.get("x-trace-id")
    
    return JSONResponse(
        status_code=500,
        content=problem.to_dict(),
        media_type="application/problem+json"
    )
```

## Important Rules

- Use `application/problem+json` as media_type
- Get trace_id from headers for correlation
- Do not expose internal details in production errors
- Map Pydantic errors to RFC 7807 format

## Example

```python
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr

app = FastAPI()

class CreateCustomerRequest(BaseModel):
    email: EmailStr
    name: str

@app.post("/api/v1/customers")
async def create_customer(request: CreateCustomerRequest):
    # If validation fails, the exception handler handles the error
    customer = await customer_service.create(request)
    return customer

@app.get("/api/v1/customers/{customer_id}")
async def get_customer(customer_id: str):
    customer = await customer_service.find_by_id(customer_id)
    if not customer:
        raise ResourceNotFoundException("Customer", customer_id)
    return customer
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
