<!-- keywords: sqlserver, sql server, pyodbc, database, microsoft, python -->
# SQL Server Integration - Python

## Purpose

Implement integration with SQL Server in Python using pyodbc.

## Scope of Application

- Python projects that require SQL Server
- Implementation with FastAPI or async frameworks (with wrapper)

## Main Content

### Dependencies

```txt
pyodbc>=4.0.0
```

### Client with Connection Pool

```python
import pyodbc
from contextlib import contextmanager
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

class SqlServerConnectionPool:
    def __init__(
        self,
        server: str,
        database: str,
        username: str,
        password: str,
        driver: str = "ODBC Driver 18 for SQL Server"
    ):
        self.connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    @contextmanager
    def get_connection(self):
        connection = pyodbc.connect(self.connection_string)
        try:
            yield connection
        finally:
            connection.close()
```


### Repository

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    status: str
    created_date: Optional[datetime] = None

class CustomerRepository:
    def __init__(self, pool: SqlServerConnectionPool):
        self.pool = pool
    
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT customer_id, name, email, status, created_date
                   FROM customers WHERE customer_id = ?""",
                (customer_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return Customer(*row)
            return None
    
    def save_with_transaction(self, customer: Customer) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT INTO customers 
                       (customer_id, name, email, status, created_date)
                       VALUES (?, ?, ?, ?, GETDATE())""",
                    (customer.customer_id, customer.name, 
                     customer.email, customer.status)
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
```

### Async Wrapper

```python
class AsyncCustomerRepository:
    def __init__(self, sync_repo: CustomerRepository):
        self.sync_repo = sync_repo
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    async def find_by_id(self, customer_id: str) -> Optional[Customer]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self.sync_repo.find_by_id, customer_id
        )
```

## Important Rules

- Use pyodbc with ODBC Driver 18
- Use ? parameters to prevent SQL injection
- Use ThreadPoolExecutor for async operations
- Configure Encrypt=yes for RDS

## Example

```python
pool = SqlServerConnectionPool(
    server=os.environ['SQL_SERVER'],
    database=os.environ['SQL_DATABASE'],
    username=os.environ['SQL_USER'],
    password=os.environ['SQL_PASSWORD']
)
repo = CustomerRepository(pool)
customer = repo.find_by_id('123')
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
