<!-- keywords: mongodb, nosql, motor, async, document database, python -->
# MongoDB Integration - Python

## Purpose

Implement integration with MongoDB in Python using Motor for asynchronous operations.

## Scope of Application

- Python projects that require MongoDB/DocumentDB
- Implementation with FastAPI or async frameworks
- Applications with high concurrency

## Main Content

### Dependencies

```txt
motor>=3.3.0
pymongo>=4.5.0
```

### Async Client

```python
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

class MongoConnectionManager:
    def __init__(self, uri: str, database: str):
        self.async_client = AsyncIOMotorClient(
            uri,
            maxPoolSize=50,
            minPoolSize=5,
            maxIdleTimeMS=60000,
            retryWrites=True,
            retryReads=True
        )
        self.sync_client = MongoClient(uri)
        self.async_db = self.async_client[database]
        self.sync_db = self.sync_client[database]
    
    def close(self):
        self.async_client.close()
        self.sync_client.close()
```

### Async Repository

```python
@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    status: str
    created_date: Optional[datetime] = None
    addresses: Optional[List[Dict[str, str]]] = None

class AsyncCustomerRepository:
    def __init__(self, connection_manager: MongoConnectionManager):
        self.collection = connection_manager.async_db.customers
    
    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        doc = await self.collection.find_one({"customer_id": customer_id})
        if doc:
            return Customer(
                customer_id=doc["customer_id"],
                name=doc["name"],
                email=doc["email"],
                status=doc["status"],
                created_date=doc.get("created_date")
            )
        return None

    
    async def find_by_status(self, status: str) -> List[Customer]:
        cursor = self.collection.find({"status": status}).sort("created_date", -1)
        customers = []
        async for doc in cursor:
            customers.append(Customer(
                customer_id=doc["customer_id"],
                name=doc["name"],
                email=doc["email"],
                status=doc["status"],
                created_date=doc.get("created_date")
            ))
        return customers
    
    async def aggregate_by_status(self) -> List[Dict[str, Any]]:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        cursor = self.collection.aggregate(pipeline)
        return [doc async for doc in cursor]
    
    async def upsert(self, customer: Customer) -> Customer:
        result = await self.collection.find_one_and_update(
            {"customer_id": customer.customer_id},
            {
                "$set": {
                    "name": customer.name,
                    "email": customer.email,
                    "status": customer.status
                },
                "$setOnInsert": {"created_date": datetime.utcnow()}
            },
            upsert=True,
            return_document=True
        )
        return Customer(
            customer_id=result["customer_id"],
            name=result["name"],
            email=result["email"],
            status=result["status"],
            created_date=result.get("created_date")
        )
    
    async def create_indexes(self):
        await self.collection.create_indexes([
            {"keys": [("customer_id", 1)], "unique": True},
            {"keys": [("email", 1)]},
            {"keys": [("status", 1), ("created_date", -1)]},
            {"keys": [("name", "text"), ("email", "text")]}
        ])
```

### Error handling

```python
from pymongo.errors import DuplicateKeyError

async def create_customer(self, customer: Customer) -> Customer:
    try:
        await self.collection.insert_one({
            "customer_id": customer.customer_id,
            "name": customer.name,
            "email": customer.email,
            "status": customer.status,
            "created_date": datetime.utcnow()
        })
        return customer
    except DuplicateKeyError:
        raise ConflictError("Customer already exists")
```

## Important Rules

- Use Motor for asynchronous operations
- Create indexes for frequently queried fields
- Use aggregations for complex queries
- Implement retry for transient errors

## Example

```python
# Usage with FastAPI
from fastapi import FastAPI, HTTPException

app = FastAPI()
mongo = MongoConnectionManager(
    os.environ['MONGO_URI'],
    os.environ['MONGO_DB']
)
repo = AsyncCustomerRepository(mongo)

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    customer = await repo.find_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Not found")
    return customer

@app.on_event("shutdown")
def shutdown():
    mongo.close()
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
