<!-- keywords: dynamodb, aws, nosql, aiobotocore, async, python -->
# DynamoDB Integration - Python

## Purpose

Implement integration with DynamoDB in Python using aiobotocore for asynchronous operations.

## Scope of Application

- Python projects that require DynamoDB
- Implementation with FastAPI or async frameworks
- Serverless applications with Lambda

## Main Content

### Dependencies

```txt
aiobotocore>=2.5.0
boto3>=1.28.0
```

### Async Client

```python
import aiobotocore.session
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import uuid
from datetime import datetime

@dataclass
class Customer:
    pk: str
    sk: str
    name: str
    email: str
    status: str
    gsi1pk: str
    gsi1sk: str
    
    @classmethod
    def create(cls, name: str, email: str, status: str = "ACTIVE") -> "Customer":
        customer_id = str(uuid.uuid4())
        return cls(
            pk=f"CUSTOMER#{customer_id}",
            sk="PROFILE",
            name=name,
            email=email,
            status=status,
            gsi1pk=f"STATUS#{status}",
            gsi1sk=datetime.utcnow().isoformat()
        )
    
    def to_item(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_item(cls, item: Dict[str, Any]) -> "Customer":
        return cls(**item)
```

### Async Repository

```python
class AsyncDynamoRepository:
    def __init__(self, table_name: str):
        self.session = aiobotocore.session.get_session()
        self.table_name = table_name
    
    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        async with self.session.create_client('dynamodb') as client:
            response = await client.get_item(
                TableName=self.table_name,
                Key={
                    'pk': {'S': f'CUSTOMER#{customer_id}'},
                    'sk': {'S': 'PROFILE'}
                }
            )
            
            if 'Item' not in response:
                return None
            
            return Customer.from_item(self._deserialize(response['Item']))

    
    async def find_by_status(self, status: str) -> List[Customer]:
        async with self.session.create_client('dynamodb') as client:
            response = await client.query(
                TableName=self.table_name,
                IndexName='GSI1',
                KeyConditionExpression='gsi1pk = :status',
                ExpressionAttributeValues={
                    ':status': {'S': f'STATUS#{status}'}
                }
            )
            
            return [
                Customer.from_item(self._deserialize(item))
                for item in response.get('Items', [])
            ]
    
    async def save(self, customer: Customer) -> None:
        async with self.session.create_client('dynamodb') as client:
            await client.put_item(
                TableName=self.table_name,
                Item=self._serialize(customer.to_item()),
                ConditionExpression='attribute_not_exists(pk)'
            )
    
    def _serialize(self, item: Dict[str, Any]) -> Dict[str, Dict]:
        return {k: {'S': str(v)} for k, v in item.items()}
    
    def _deserialize(self, item: Dict[str, Dict]) -> Dict[str, Any]:
        return {k: list(v.values())[0] for k, v in item.items()}
```

### Transactions

```python
async def create_order_with_items(
    self,
    customer_id: str,
    items: List[Dict[str, Any]]
) -> str:
    order_id = str(uuid.uuid4())
    total = sum(item['price'] * item['quantity'] for item in items)
    
    transact_items = [
        {
            'Put': {
                'TableName': self.table_name,
                'Item': self._serialize({
                    'pk': f'ORDER#{order_id}',
                    'sk': 'METADATA',
                    'customer_id': customer_id,
                    'amount': str(total),
                    'status': 'PENDING'
                }),
                'ConditionExpression': 'attribute_not_exists(pk)'
            }
        }
    ]
    
    for idx, item in enumerate(items):
        transact_items.append({
            'Put': {
                'TableName': self.table_name,
                'Item': self._serialize({
                    'pk': f'ORDER#{order_id}',
                    'sk': f'ITEM#{idx}',
                    **item
                })
            }
        })
    
    async with self.session.create_client('dynamodb') as client:
        await client.transact_write_items(TransactItems=transact_items)
    
    return order_id
```

### Error handling

```python
from botocore.exceptions import ClientError

async def create_customer(self, name: str, email: str) -> Customer:
    customer = Customer.create(name, email)
    try:
        await self.save(customer)
        return customer
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ConflictError('Customer already exists')
        raise
```

## Important Rules

- Use aiobotocore for asynchronous operations
- Implement retry for ProvisionedThroughputExceededException
- Use transact_write_items for atomic operations
- Serialize/deserialize DynamoDB types correctly

## Example

```python
# Lambda handler
from fastapi import FastAPI, HTTPException

app = FastAPI()
repo = AsyncDynamoRepository(os.environ['TABLE_NAME'])

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    customer = await repo.find_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Not found")
    return customer

@app.post("/customers", status_code=201)
async def create_customer(name: str, email: str):
    customer = Customer.create(name, email)
    await repo.save(customer)
    return customer
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
