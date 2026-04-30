<!-- keywords: soc2, audit logging, event traceability, boto3, dataclasses, decorators, compliance, python -->
# SOC2 Audit Logging - Python Implementation

## Purpose

Implement SOC2-compliant audit logging in Python using boto3, dataclasses, and decorators for automatic auditing.

## Scope of Application

- When developing Python systems that require SOC2 certification.
- When audit decorators need to be implemented.
- To configure immutable event storage.

## Main Content

### Dependencies

```txt
boto3>=1.28.0
```

### Implementation

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid

class AuditEventType(Enum):
    DATA_ACCESS = "DATA_ACCESS"
    DATA_MODIFICATION = "DATA_MODIFICATION"
    AUTHENTICATION = "AUTHENTICATION"

class ActionStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

@dataclass(frozen=True)
class Actor:
    user_id: str
    user_type: str
    ip_address: str

@dataclass(frozen=True)
class Resource:
    type: str
    id: str
    name: str

@dataclass(frozen=True)
class Action:
    type: str
    status: ActionStatus
    details: Optional[str] = None

@dataclass(frozen=True)
class AuditEvent:
    event_type: AuditEventType
    actor: Actor
    resource: Resource
    action: Action
    context: Dict[str, str]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

```python
# Audit service
import boto3
import json
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, stream_name: str, table_name: str):
        self.kinesis = boto3.client('kinesis')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
        self.stream_name = stream_name
    
    async def log_event(self, event: AuditEvent) -> None:
        event_dict = self._to_dict(event)
        await self._persist_to_dynamodb(event_dict)
        await self._send_to_kinesis(event_dict)
        logger.info("audit_event", extra={"audit": event_dict})
    
    async def _persist_to_dynamodb(self, event: dict) -> None:
        self.table.put_item(
            Item={
                'pk': f"EVENT#{event['event_id']}",
                'sk': event['timestamp'],
                'data': json.dumps(event),
                'ttl': self._calculate_ttl()
            },
            ConditionExpression='attribute_not_exists(pk)'
        )
    
    def _calculate_ttl(self) -> int:
        import time
        seven_years = 7 * 365 * 24 * 60 * 60
        return int(time.time()) + seven_years
```

```python
# Decorator for automatic auditing
def auditable(event_type: AuditEventType, resource_type: str, action_type: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            audit_service = get_audit_service()
            actor = extract_actor_from_context()
            resource_id = kwargs.get('id') or args[1] if len(args) > 1 else 'unknown'
            
            try:
                result = await func(*args, **kwargs)
                await audit_service.log_event(AuditEvent(
                    event_type=event_type,
                    actor=actor,
                    resource=Resource(type=resou
rce_type, id=str(resource_id), name=func.__name__),
                    action=Action(type=action_type, status=ActionStatus.SUCCESS),
                    context=get_request_context()
                ))
                return result
            except Exception as e:
                await audit_service.log_event(AuditEvent(
                    event_type=event_type,
                    actor=actor,
                    resource=Resource(type=resource_type, id=str(resource_id), name=func.__name__),
                    action=Action(type=action_type, status=ActionStatus.FAILURE, details=str(e)),
                    context=get_request_context()
                ))
                raise
        return wrapper
    return decorator
```

### Configuration

```python
AUDIT_CONFIG = {
    'stream_name': os.environ['AUDIT_STREAM_NAME'],
    'table_name': os.environ['AUDIT_TABLE_NAME'],
    'retention_years': 7
}
```

## Important Rules

- Use `frozen=True` in dataclasses for immutability.
- Implement 7-year TTL.
- Use `ConditionExpression` to prevent overwriting.

## Example

```python
@auditable(event_type=AuditEventType.DATA_ACCESS, resource_type="CUSTOMER", action_type="READ")
async def get_customer(self, customer_id: str) -> Customer:
    return await self.repository.find_by_id(customer_id)
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
