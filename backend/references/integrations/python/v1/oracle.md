<!-- keywords: oracle, database, cx_oracle, connection pooling, python -->
# Oracle Database Integration - Python

## Purpose

Implement integration with Oracle Database in Python using cx_Oracle with connection pooling.

## Scope of Application

- Python projects that require Oracle Database
- Implementation with FastAPI or async frameworks (with wrapper)
- Working with stored procedures

## Main Content

### Dependencies

```txt
cx_Oracle>=8.3.0
```

### Client with Connection Pool

```python
import cx_Oracle
from contextlib import contextmanager
from typing import Optional, List
import asyncio
from concurrent.futures import ThreadPoolExecutor

class OracleConnectionPool:
    def __init__(
        self,
        user: str,
        password: str,
        dsn: str,
        min_connections: int = 2,
        max_connections: int = 10
    ):
        self.pool = cx_Oracle.SessionPool(
            user=user,
            password=password,
            dsn=dsn,
            min=min_connections,
            max=max_connections,
            increment=1,
            threaded=True,
            getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT
        )
        self._executor = ThreadPoolExecutor(max_workers=max_connections)
    
    @contextmanager
    def get_connection(self):
        connection = self.pool.acquire()
        try:
            yield connection
        finally:
            self.pool.release(connection)
    
    def close(self):
        self.pool.close()
        self._executor.shutdown(wait=True)
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
    def __init__(self, pool: OracleConnectionPool):
        self.pool = pool
    
    def find_by_id(self, customer_id: str) -> Optional[Customer]:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT customer_id, name, email, status, created_date
                   FROM customers WHERE customer_id = :customer_id""",
                {"customer_id": customer_id}
            )
            row = cursor.fetchone()
            
            if row:
                return Customer(*row)
            return None
    
    def call_stored_procedure(self, status: str) -> List[Customer]:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            ref_cursor = cursor.var(cx_Oracle.CURSOR)
            
            cursor.callproc(
                "CUSTOMER_PKG.GET_CUSTOMERS_BY_STATUS",
                [status, ref_cursor]
            )
            
            customers = []
            for row in ref_cursor.getvalue():
                customers.append(Customer(*row))
            
            return customers
    
    def save_with_transaction(self, customer: Customer) -> None:
        with self.pool.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT INTO customers 
                       (customer_id, name, email, status, created_date)
                       VALUES (:1, :2, :3, :4, SYSDATE)""",
                    [customer.customer_id, customer.name, 
                     customer.email, customer.status]
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

- Use SessionPool for connection pooling
- Close REF CURSOR cursors after use
- Use bind variables to prevent SQL injection
- Use ThreadPoolExecutor for async operations

## Example

```python
pool = OracleConnectionPool(
    user=os.environ['ORACLE_USER'],
    password=os.environ['ORACLE_PASSWORD'],
    dsn=os.environ['ORACLE_DSN']
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
