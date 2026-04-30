<!-- keywords: pci-dss, compliance, pan tokenization, log sanitization, card validation, boto3, pydantic, python -->
# PCI-DSS Compliance - Python Implementation

## Purpose

Implement PCI-DSS compliance controls in Python using boto3 and Pydantic, including PAN tokenization, log sanitization, and card data validation.

## Scope of Application

- When developing payment services in Python.
- When card data tokenization needs to be implemented.
- To configure PCI-compliant sanitization decorators.

## Main Content

### Dependencies

```txt
# requirements.txt
boto3>=1.28.0
pydantic>=2.0.0
```

### Implementation

```python
# Tokenization service
import boto3
import secrets
from dataclasses import dataclass

class PciTokenizationService:
    def __init__(self, kms_key_id: str):
        self.kms_client = boto3.client('kms')
        self.kms_key_id = kms_key_id
        self.token_store = {}  # In production use DynamoDB
    
    def tokenize(self, pan: str) -> str:
        if not self._validate_luhn(pan):
            raise ValueError("Invalid PAN")
        
        token = self._generate_token()
        encrypted = self.kms_client.encrypt(
            KeyId=self.kms_key_id,
            Plaintext=pan.encode(),
            EncryptionContext={'purpose': 'pan-tokenization'}
        )
        self.token_store[token] = encrypted['CiphertextBlob']
        return token

    def detokenize(self, token: str) -> str:
        if token not in self.token_store:
            raise ValueError("Token not found")
        
        decrypted = self.kms_client.decrypt(
            CiphertextBlob=self.token_store[token],
            EncryptionContext={'purpose': 'pan-tokenization'}
        )
        return decrypted['Plaintext'].decode()
    
    def _generate_token(self) -> str:
        return f"tok_{secrets.token_urlsafe(24)}"
    
    def _validate_luhn(self, pan: str) -> bool:
        digits = [int(d) for d in pan if d.isdigit()]
        checksum = 0
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0
```

```python
# Decorator for log sanitization
import functools
import re
import logging

PAN_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')
SENSITIVE_KEYS = {'pan', 'card_number', 'cvv', 'cvc', 'security_code'}

class PciSafeFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return PAN_PATTERN.sub('[PAN-REDACTED]', message)

def pci_safe_logging(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        safe_kwargs = {
            k: '[REDACTED]' if k.lower() in SENSITIVE_KEYS else v
            for k, v in kwargs.items()
        }
        logging.debug(f"Calling {func.__name__} with sanitized args")
        return func(*args, **kwargs)
    return wrapper
```

```python
# Pydantic validation for PCI data
from pydantic import BaseModel, field_validator, Field
from typing import Annotated

class CardData(BaseModel):
    pan: Annotated[str, Field(min_length=13, max_length=19)]
    expiry_month: Annotated[int, Field(ge=1, le=12)]
    expiry_year: Annotated[int, Field(ge=2024, le=2099)]
    cvv: Annotated[str, Field(min_length=3, max_length=4, exclude=True)]
    
    @field_validator('pan')
    @classmethod
    def validate_pan(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('PAN must contain only digits')
        return v
    
    @property
    def masked_pan(self) -> str:
        return '*' * (len(self.pan) - 4) + self.pan[-4:]
```

### Configuration

```python
# config.py
import os

PCI_CONFIG = {
    'kms_key_id': os.environ['KMS_KEY_ID'],
    'token_prefix': 'tok_'
}
```

## Important Rules

- Use `exclude=True` on CVV fields in Pydantic.
- Implement custom formatter for logs.
- Never store CVV after authorization.

## Example

```python
service = PciTokenizationService(os.environ['KMS_KEY_ID'])
token = service.tokenize("4111111111111111")
print(f"Token: {token}")
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
