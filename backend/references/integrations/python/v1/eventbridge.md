<!-- keywords: eventbridge, aws, event-driven, boto3, aiobotocore, python -->
# Amazon EventBridge Integration - Python

## Purpose

Implement integration with Amazon EventBridge in Python projects using boto3 and aiobotocore.

## Scope of Application

- Python projects that require publishing events to EventBridge
- Python Lambdas that publish domain events
- Synchronous implementation with boto3 or asynchronous with aiobotocore

## Main Content

### Dependencies

```txt
# requirements.txt - Synchronous
boto3>=1.28.0

# requirements.txt - Asynchronous
aiobotocore>=2.5.0
```

```bash
# Installation
pip install boto3
pip install aiobotocore  # For async
```

### Synchronous Client

```python
import boto3
import json
from typing import List, Dict, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    version: int
    payload: Dict[str, Any]
    resources: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class EventBridgePublisher:
    """Synchronous publisher for EventBridge"""
    
    def __init__(self, event_bus_name: str, source: str):
        self.client = boto3.client('events')
        self.event_bus_name = event_bus_name
        self.source = source
    
    def publish(self, event: DomainEvent) -> str:
        entry = self._build_entry(event)
        
        response = self.client.put_events(Entries=[entry])
        
        if response.get('FailedEntryCount', 0) > 0:
            failed = response['Entries'][0]
            raise Exception(
                f"Failed to publish: {failed.get('ErrorCode')} - "
                f"{failed.get('ErrorMessage')}"
            )
        
        return response['Entries'][0]['EventId']
    
    def publish_batch(self, events: List[DomainEvent]) -> List[Dict[str, Any]]:
        results = []
        
        for i in range(0, len(events), 10):
            batch = events[i:i + 10]
            entries = [self._build_entry(event) for event in batch]
            
            response = self.client.put_events(Entries=entries)
            
            for entry in response['Entries']:
                if 'EventId' in entry:
                    results.append({
                        'event_id': entry['EventId'],
                        'success': True
                    })
                else:
                    results.append({
                        'success': False,
                        'error_code': entry.get('ErrorCode'),
                        'error_message': entry.get('ErrorMessage')
                    })
        
        return results
    
    def _build_entry(self, event: DomainEvent) -> Dict[str, Any]:
        return {
            'EventBusName': self.event_bus_name,
            'Source': self.source,
            'DetailType': event.event_type,
            'Detail': json.dumps(asdict(event)),
            'Time': datetime.utcnow(),
            'Resources': event.resources
        }
```

### Async Client

```python
import asyncio
from aiobotocore.session import get_session


class AsyncEventBridgePublisher:
    """Asynchronous publisher for EventBridge"""
    
    def __init__(self, event_bus_name: str, source: str):
        self.event_bus_name = event_bus_name
        self.source = source
        self._session = get_session()
    
    async def publish(self, event: DomainEvent) -> str:
        async with self._session.create_client('events') as client:
            entry = self._build_entry(event)
            response = await client.put_events(Entries=[entry])
            
            if response.get('FailedEntryCount', 0) > 0:
                failed = response['Entries'][0]
                raise Exception(f"Failed: {failed.get('ErrorCode')}")
            
            return response['Entries'][0]['EventId']
    
    async def publish_batch(
        self, 
        events: List[DomainEvent]
    ) -> List[Dict[str, Any]]:
        async with self._session.create_client('events') as client:
            tasks = []
            
            for i in range(0, len(events), 10):
                batch = events[i:i + 10]
                entries = [self._build_entry(event) for event in batch]
                tasks.append(client.put_events(Entries=entries))
            
            responses = await asyncio.gather(*tasks)
            
            results = []
            for response in responses:
                for entry in response['Entries']:
                    if 'EventId' in entry:
                        results.append({
                            'event_id': entry['EventId'],
                            'success': True
                        })
            
            return results
    
    def _build_entry(self, event: DomainEvent) -> Dict[str, Any]:
        return {
            'EventBusName': self.event_bus_name,
            'Source': self.source,
            'DetailType': event.event_type,
            'Detail': json.dumps(asdict(event)),
            'Resources': event.resources
        }
```

### Lambda Handler for rules

```python
from typing import Dict, Any


def handler(event: Dict[str, Any], context) -> None:
    """Handler for EventBridge events"""
    print(f"Received event: {event['source']} - {event['detail-type']}")
    
    domain_event = event['detail']
    detail_type = event['detail-type']
    
    if detail_type == 'OrderCreated':
        handle_order_created(domain_event)
    elif detail_type == 'PaymentProcessed':
        handle_payment_processed(domain_event)
    else:
        print(f"Unknown event type: {detail_type}")


def handle_order_created(event: Dict[str, Any]) -> None:
    print(f"Processing order: {event['aggregate_id']}")
    # Business logic


def handle_payment_processed(event: Dict[str, Any]) -> None:
    print(f"Processing payment for: {event['aggregate_id']}")
    # Business logic
```

### Error handling

```python
from botocore.exceptions import ClientError
import time


def publish_with_retry(
    publisher: EventBridgePublisher,
    event: DomainEvent,
    max_retries: int = 3
) -> str:
    last_error = None
    
    for attempt in range(max_retries):
        try:
            return publisher.publish(event)
        except ClientError as e:
            last_error = e
            error_code = e.response['Error']['Code']
            
            if error_code in ['Throttling', 'ServiceUnavailable']:
                delay = (2 ** attempt) * 0.1
                time.sleep(delay)
                continue
            raise
    
    raise last_error
```

## Important Rules

- Reuse boto3 client between Lambda invocations
- Partition batches into groups of maximum 10 events
- Use `aiobotocore` for high-throughput operations
- Implement retry with exponential backoff
- Close async sessions properly

## Example

```python
# Usage in Lambda
import os
import uuid

publisher = EventBridgePublisher(
    event_bus_name=os.environ['EVENT_BUS_NAME'],
    source='com.company.orders'
)


def lambda_handler(event, context):
    order = json.loads(event['body'])
    
    domain_event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type='OrderCreated',
        aggregate_id=order['id'],
        aggregate_type='Order',
        version=1,
        payload=order,
        resources=[f"arn:aws:orders:{order['id']}"]
    )
    
    event_id = publisher.publish(domain_event)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'eventId': event_id})
    }
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
