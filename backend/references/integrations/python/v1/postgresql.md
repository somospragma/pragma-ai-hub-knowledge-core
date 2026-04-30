<!-- keywords: postgresql, asyncpg, async, database, connection pooling, python -->
# PostgreSQL Integration - Python

## Purpose

Implement integration with PostgreSQL in Python using asyncpg for high-performance asynchronous operations.

## Scope of Application

- Python projects that require PostgreSQL
- Implementation with FastAPI or async frameworks
- Applications with high concurrency

## Main Content

### Dependencies

```txt
# requirements.txt
asyncpg>=0.28.0
pydantic>=2.0.0
```

### Async Client

```python
import asyncpg
from typing import Optional, List, TypeVar, Type
from contextlib import asynccontextmanager
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    min_size: int = 5
    max_size: int = 20

class AsyncPostgresClient:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_size,
            max_size=self.config.max_size,
            command_timeout=60
        )
    
    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
    
    @property
    def pool(self) -> asyncpg.Pool:
        if not self._pool:
            raise RuntimeError("Database not connected")
        return self._pool
    
    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def execute(self, query: str, *args) -> str:
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    @asynccontextmanager
    async def transaction(self):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
```

### CRUD Operations

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import uuid

class Customer(BaseModel):
    id: str
    name: str
    email: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class CustomerRepository:
    def __init__(self, db: AsyncPostgresClient):
        self.db = db
    
    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        row = await self.db.fetchrow(
            "SELECT * FROM customers WHERE id = $1",
            customer_id
        )
        return Customer(**dict(row)) if row else None
    
    async def find_by_status(self, status: str) -> List[Customer]:
        rows = await self.db.fetch(
            "SELECT * FROM customers WHERE status = $1",
            status
        )
        return [Customer(**dict(row)) for row in rows]
    
    async def create(
        self, 
        name: str, 
        email: str, 
        status: str = "ACTIVE"
    ) -> Customer:
        row = await self.db.fetchrow(
            """INSERT INTO customers (id, name, email, status, created_at)
               VALUES ($1, $2, $3, $4, NOW())
               RETURNING *""",
            str(uuid.uuid4()), name, email, status
        )
        return Customer(**dict(row))
    
    async def update(
        self, 
        customer_id: str, 
        **updates
    ) -> Optional[Customer]:
        fields = []
        values = []
        for i, (key, value) in enumerate(updates.items(), start=1):
            fields.append(f"{key} = ${i}")
            values.append(value)
        
        values.append(customer_id)
        
        row = await self.db.fetchrow(
            f"""UPDATE customers 
                SET {', '.join(fields)} 
                WHERE id = ${len(values)}
                RETURNING *""",
            *values
        )
        return Customer(**dict(row)) if row else None
    
    async def delete(self, customer_id: str) -> bool:
        result = await self.db.execute(
            "DELETE FROM customers WHERE id = $1",
            customer_id
        )
        return result == "DELETE 1"
```

### Transactions

```python
async def create_with_order(
    self, 
    name: str, 
    email: str
) -> Customer:
    async with self.db.transaction() as conn:
        customer_id = str(uuid.uuid4())
        
        customer_row = await conn.fetchrow(
            """INSERT INTO customers (id, name, email, status, created_at)
               VALUES ($1, $2, $3, 'ACTIVE', NOW())
               RETURNING *""",
            customer_id, name, email
        )
        
        await conn.execute(
            """INSERT INTO orders (id, customer_id, amount, status)
               VALUES ($1, $2, 0, 'PENDING')""",
            str(uuid.uuid4()), customer_id
        )
        
        return Customer(**dict(customer_row))
```

### Error handling

```python
import asyncpg

class CustomerService:
    def __init__(self, repo: CustomerRepository):
        self.repo = repo
    
    async def create_customer(
        self, 
        name: str, 
        email: str
    ) -> Customer:
        try:
            return await self.repo.create(name, email)
        except asyncpg.UniqueViolationError:
            raise ConflictError(f"Customer with email {email} already exists")
        except asyncpg.ForeignKeyViolationError:
            raise BadRequestError("Invalid reference")
        except asyncpg.PostgresConnectionError as e:
            raise ServiceUnavailableError(f"Database connection error: {e}")
```

## Important Rules

- Connection pooling: Always use asyncpg.create_pool()
- Timeouts: Configure command_timeout for queries
- Transactions: Use async with conn.transaction()
- Prepared statements: Use $1, $2 for parameters

## Example

```python
# Full usage with FastAPI
from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import os

db_client: Optional[AsyncPostgresClient] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client
    db_client = AsyncPostgresClient(DatabaseConfig(
        host=os.environ['DB_HOST'],
        port=int(os.environ['DB_PORT']),
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD']
    ))
    await db_client.connect()
    yield
    await db_client.close()

app = FastAPI(lifespan=lifespan)

def get_customer_repo() -> CustomerRepository:
    return CustomerRepository(db_client)

@app.get("/customers/{customer_id}")
async def get_customer(
    customer_id: str,
    repo: CustomerRepository = Depends(get_customer_repo)
):
    customer = await repo.find_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@app.post("/customers", status_code=201)
async def create_customer(
    name: str,
    email: str,
    repo: CustomerRepository = Depends(get_customer_repo)
):
    return await repo.create(name, email)
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
