<!-- keywords: sqs, aws, queue, aiobotocore, async, messaging, python -->
# Amazon SQS Integration - Python

## Purpose

Implement integration with Amazon SQS in Python using aiobotocore for asynchronous operations.

## Scope of Application

- Python projects that require SQS
- Implementation with FastAPI or async frameworks
- Serverless applications with Lambda

## Main Content

### Dependencies

```txt
aiobotocore>=2.5.0
boto3>=1.28.0
```

### Async Producer

```python
import aiobotocore.session
import json
from typing import List, Optional
from dataclasses import dataclass, asdict

@dataclass
class MessageOptions:
    delay_seconds: int = 0
    message_group_id: Optional[str] = None
    message_deduplication_id: Optional[str] = None

class AsyncSqsProducer:
    def __init__(self, queue_url: str):
        self.session = aiobotocore.session.get_session()
        self.queue_url = queue_url
    
    async def send_message(
        self, 
        message: any, 
        options: Optional[MessageOptions] = None
    ) -> str:
        options = options or MessageOptions()
        
        async with self.session.create_client('sqs') as client:
            params = {
                'QueueUrl': self.queue_url,
                'MessageBody': json.dumps(
                    asdict(message) if hasattr(message, '__dataclass_fields__') else message
                ),
                'DelaySeconds': options.delay_seconds
            }
            
            if options.message_group_id:
                params['MessageGroupId'] = options.message_group_id
            if options.message_deduplication_id:
                params['MessageDeduplicationId'] = options.message_deduplication_id
            
            response = await client.send_message(**params)
            return response['MessageId']

    
    async def send_batch(self, messages: List[any]) -> None:
        async with self.session.create_client('sqs') as client:
            for i in range(0, len(messages), 10):
                batch = messages[i:i+10]
                entries = [
                    {
                        'Id': str(idx),
                        'MessageBody': json.dumps(
                            asdict(msg) if hasattr(msg, '__dataclass_fields__') else msg
                        )
                    }
                    for idx, msg in enumerate(batch)
                ]
                
                await client.send_message_batch(
                    QueueUrl=self.queue_url,
                    Entries=entries
                )
```

### Lambda Handler with Partial Batch Response

```python
import json
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class OrderMessage:
    order_id: str
    customer_id: str
    amount: float

def handler(event: Dict[str, Any], context) -> Dict[str, List]:
    batch_item_failures = []
    
    for record in event['Records']:
        try:
            message = OrderMessage(**json.loads(record['body']))
            process_order(message)
        except Exception as e:
            print(f"Failed to process message {record['messageId']}: {e}")
            batch_item_failures.append({
                'itemIdentifier': record['messageId']
            })
    
    return {'batchItemFailures': batch_item_failures}

def process_order(order: OrderMessage) -> None:
    print(f"Processing order {order.order_id}")
```

## Important Rules

- Use batch operations for better throughput (max 10 messages)
- Implement partial batch response in Lambda
- Use aiobotocore for asynchronous operations
- Implement idempotency in consumers

## Example

```python
# Producer usage
producer = AsyncSqsProducer(os.environ['QUEUE_URL'])

# Simple message
await producer.send_message({'order_id': '123', 'amount': 100})

# FIFO message
await producer.send_message(
    {'order_id': '123', 'amount': 100},
    MessageOptions(
        message_group_id='customer-456',
        message_deduplication_id='order-123'
    )
)
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
