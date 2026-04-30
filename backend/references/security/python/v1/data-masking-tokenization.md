<!-- keywords: data masking, tokenization, pii, pci, sensitive data, pydantic, fastapi middleware, python -->
# Data Masking and Tokenization - Python Implementation

## Purpose

Implement PII/PCI data masking in Python using configurable strategies, Pydantic, and FastAPI middleware.

## Scope of Application

- When developing Python services that handle sensitive data.
- When automatic masking with Pydantic is needed.
- To configure masking middleware in FastAPI.

## Main Content

### Dependencies

```txt
pydantic>=2.0.0
fastapi>=0.104.0
```

### Implementation

```python
# Masking service
from enum import Enum
from typing import Any, Callable, Dict, Optional
import re

class DataType(Enum):
    PAN = "PAN"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    NAME = "NAME"

class DataMaskingService:
    def __init__(self):
        self._strategies: Dict[DataType, Callable[[str], str]] = {
            DataType.PAN: self._mask_pan,
            DataType.EMAIL: self._mask_email,
            DataType.PHONE: self._mask_phone,
            DataType.SSN: self._mask_ssn,
            DataType.NAME: self._mask_name,
        }
    
    def mask(self, value: Optional[str], data_type: DataType) -> str:
        if not value:
            return ""
        strategy = self._strategies.get(data_type)
        return strategy(value) if strategy else value
    
    def mask_dict(
        self, 
        data: Dict[str, Any], 
        fields: Dict[str, DataType]
    ) -> Dict[str, Any]:
        masked = data.copy()
        for field, data_type in fields.items():
            if field in masked and isinstance(masked[field], str):
                masked[field] = self.mask(masked[field], data_type)
        return masked

    def _mask_pan(self, pan: str) -> str:
        if len(pan) < 4:
            return "****"
        return "*" * (len(pan) - 4) + pan[-4:]
    
    def _mask_email(self, email: str) -> str:
        if "@" not in email:
            return "***@***"
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"***@{domain}"
        return f"{local[0]}***{local[-1]}@{domain}"
    
    def _mask_phone(self, phone: str) -> str:
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 4:
            return "****"
        return f"***-***-{digits[-4:]}"
    
    def _mask_ssn(self, ssn: str) -> str:
        digits = re.sub(r"\D", "", ssn)
        if len(digits) < 4:
            return "***-**-****"
        return f"***-**-{digits[-4:]}"
    
    def _mask_name(self, name: str) -> str:
        parts = name.split()
        return " ".join(
            part if len(part) <= 2 else f"{part[0]}{'*' * (len(part) - 1)}"
            for part in parts
        )
```

```python
# Pydantic model with masking
from pydantic import BaseModel
from typing import ClassVar, Dict, Any

class MaskedField:
    def __init__(self, data_type: DataType, in_response: bool = False, in_logs: bool = True):
        self.data_type = data_type
        self.in_response = in_response
        self.in_logs = in_logs

class CustomerDto(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    card_number: str
    
    _masked_fields: ClassVar[Dict[str, MaskedField]] = {
        "email": MaskedField(DataType.EMAIL, in_response=True),
        "phone": MaskedField(DataType.PHONE, in_response=True),
        "card_number": MaskedField(DataType.PAN, in_response=True, in_logs=True),
    }
    
    def to_masked_dict(self) -> Dict[str, Any]:
        service = DataMaskingService()
        data = self.model_dump()
        for field, config in self._masked_fields.items():
            if config.in_response and field in data:
                data[field] = service.mask(data[field], config.data_type)
        return data
```

```python
# FastAPI masking middleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

class MaskingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, masking_service: DataMaskingService):
        super().__init__(app)
        self.masking_service = masking_service
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Process JSON responses if needed
        return response
```

### Configuration

```python
MASKING_CONFIG = {
    'enabled': True,
    'default_mask_char': '*',
    'types': {
        'pan': {'show_last': 4},
        'email': {'show_first': 1, 'show_last': 1},
        'phone': {'show_last': 4}
    }
}
```

## Important Rules

- Use `ClassVar` to define maskable fields in Pydantic.
- Implement separate methods for logs and responses.
- Consider context when applying masking.

## Example

```python
service = DataMaskingService()

customer = {
    'id': '123',
    'email': 'john.doe@example.com',
    'phone': '+1-555-123-4567',
    'card_number': '4111111111111111'
}

masked = service.mask_dict(customer, {
    'email': DataType.EMAIL,
    'phone': DataType.PHONE,
    'card_number': DataType.PAN
})
# {'id': '123', 'email': 'j***e@example.com', 'phone': '***-***-4567', 'card_number': '************1111'}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
