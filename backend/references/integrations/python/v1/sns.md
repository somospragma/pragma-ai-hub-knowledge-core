<!-- keywords: sns, aws, pub/sub, notification, boto3, aiobotocore, python -->
# Amazon SNS Integration - Python

## Purpose

Implement integration with Amazon SNS in Python projects using boto3 and aiobotocore.

## Scope of Application

- Python projects that require publishing messages to SNS
- Python Lambdas that publish events
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
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    source: str
    version: int
    payload: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class SnsPublisher:
    """Synchronous publisher for SNS"""
    
    def __init__(self, topic_arn: str):
        self.client = boto3.client('sns')
        self.topic_arn = topic_arn
    
    def publish(self, event: DomainEvent) -> str:
        response = self.client.publish(
            TopicArn=self.topic_arn,
            Message=json.dumps(asdict(event)),
            MessageAttributes=self._build_attributes(event)
        )
        return response['MessageId']
    
    def publish_batch(self, events: List[DomainEvent]) -> List[Dict[str, Any]]:
        results = []
        
        for i in range(0, len(events), 10):
            batch = events[i:i + 10]
            
            entries = [
                {
                    'Id': str(idx),
                    'Message': json.dumps(asdict(event)),
                    'MessageAttributes': self._build_attributes(event)
                }
                for idx, event in enumerate(batch, start=i)
            ]
            
            response = self.client.publish_batch(
                TopicArn=self.topic_arn,
                PublishBatchRequestEntries=entries
            )
            
            results.extend([
                {'message_id': s['MessageId'], 'success': True}
                for s in response.get('Successful', [])
            ])
            results.extend([
                {'id': f['Id'], 'success': False, 'error': f['Message']}
                for f in response.get('Failed', [])
            ])
        
        return results
    
    def publish_fifo(
        self, 
        event: DomainEvent, 
        message_group_id: str
    ) -> str:
        response = self.client.publish(
            TopicArn=self.topic_arn,
            Message=json.dumps(asdict(event)),
            MessageGroupId=message_group_id,
            MessageDeduplicationId=event.event_id,
            MessageAttributes=self._build_attributes(event)
        )
        return response['MessageId']
    
    def _build_attributes(self, event: DomainEvent) -> Dict[str, Any]:
        return {
            'eventType': {
                'DataType': 'String',
                'StringValue': event.event_type
            },
            'source': {
                'DataType': 'String',
                'StringValue': event.source
            },
            'version': {
                'DataType': 'Number',
                'StringValue': str(event.version)
            }
        }
```

### Async Client

```python
import asyncio
from aiobotocore.session import get_session


class AsyncSnsPublisher:
    """Asynchronous publisher for SNS using aiobotocore"""
    
    def __init__(self, topic_arn: str):
        self.topic_arn = topic_arn
        self._session = get_session()
    
    async def publish(self, event: DomainEvent) -> str:
        async with self._session.create_client('sns') as client:
            response = await client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(asdict(event)),
                MessageAttributes=self._build_attributes(event)
            )
            return response['MessageId']
    
    async def publish_batch(
        self, 
        events: List[DomainEvent]
    ) -> List[Dict[str, Any]]:
        async with self._session.create_client('sns') as client:
            tasks = []
            
            for i in range(0, len(events), 10):
                batch = events[i:i + 10]
                entries = [
                    {
                        'Id': str(idx),
                        'Message': json.dumps(asdict(event)),
                        'MessageAttributes': self._build_attributes(event)
                    }
                    for idx, event in enumerate(batch, start=i)
                ]
                
                tasks.append(
                    client.publish_batch(
                        TopicArn=self.topic_arn,
                        PublishBatchRequestEntries=entries
                    )
                )
            
            responses = await asyncio.gather(*tasks)
            
            results = []
            for response in responses:
                results.extend([
                    {'message_id': s['MessageId'], 'success': True}
                    for s in response.get('Successful', [])
                ])
            
            return results
    
    def _build_attributes(self, event: DomainEvent) -> Dict[str, Any]:
        return {
            'eventType': {'DataType': 'String', 'StringValue': event.event_type},
            'source': {'DataType': 'String', 'StringValue': event.source},
            'version': {'DataType': 'Number', 'StringValue': str(event.version)}
        }
```

### Lambda Handler for subscription

```python
import json
from typing import Dict, Any


def handler(event: Dict[str, Any], context) -> None:
    """Handler for SNS messages"""
    for record in event['Records']:
        sns_message = record['Sns']
        
        message = json.loads(sns_message['Message'])
        attributes = sns_message.get('MessageAttributes', {})
        
        print(f"Processing event: {attributes.get('eventType', {}).get('Value')}")
        print(f"Message ID: {sns_message['MessageId']}")
        
        process_event(message)


def process_event(event: Dict[str, Any]) -> None:
    event_type = event.get('event_type')
    
    if event_type == 'ORDER_CREATED':
        handle_order_created(event['payload'])
    elif event_type == 'ORDER_UPDATED':
        handle_order_updated(event['payload'])
    else:
        print(f"Unknown event type: {event_type}")
```

### Error handling

```python
from botocore.exceptions import ClientError
import time


def publish_with_retry(
    publisher: SnsPublisher,
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
- Partition batches into groups of maximum 10 messages
- Use `aiobotocore` for high-throughput operations
- Implement retry with exponential backoff
- Close async sessions properly

## Example

```python
# Usage in Lambda
import os

publisher = SnsPublisher(os.environ['TOPIC_ARN'])


def lambda_handler(event, context):
    order = json.loads(event['body'])
    
    domain_event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type='ORDER_CREATED',
        source='order-service',
        version=1,
        payload=order
    )
    
    message_id = publisher.publish(domain_event)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'messageId': message_id})
    }
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
