<!-- keywords: secrets manager, aws, secret rotation, boto3, aiobotocore, credentials, async, python -->
# AWS Secrets Manager Patterns - Python Implementation

## Purpose

Implement secrets management with AWS Secrets Manager in Python using boto3 and aiobotocore with asynchronous patterns.

## Scope of Application

- When developing in Python with FastAPI or asyncio.
- When asynchronous access to secrets is needed.
- To implement credential caching.
- When configuring dynamic database connections.

## Main Content

### Dependencies

```txt
boto3>=1.26.0
aiobotocore>=2.5.0
pydantic>=2.0.0
asyncpg>=0.27.0
aws-lambda-powertools>=2.0.0
```

### Asynchronous Implementation with Caching

```python
import asyncio
import json
from typing import TypeVar, Type, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiobotocore.session

T = TypeVar('T')

@dataclass
class CachedSecret:
    value: str
    expires_at: datetime

class AsyncSecretsService:
    def __init__(self, ttl_seconds: int = 3600):
        self.session = aiobotocore.session.get_session()
        self.ttl = timedelta(seconds=ttl_seconds)
        self._cache: dict[str, CachedSecret] = {}
        self._lock = asyncio.Lock()
    
    async def get_secret(self, secret_id: str) -> str:
        """Gets a secret with caching."""
        cached = self._cache.get(secret_id)
        if cached and cached.expires_at > datetime.utcnow():
            return cached.value
        
        async with self._lock:
            cached = self._cache.get(secret_id)
            if cached and cached.expires_at > datetime.utcnow():
                return cached.value
            
            async with self.session.create_client('secretsmanager') as client:
                response = await client.get_secret_value(SecretId=secret_id)
                secret_value = response['SecretString']
                
                self._cache[secret_id] = CachedSecret(
                    value=secret_value,
                    expires_at=datetime.utcnow() + self.ttl
                )
                
                return secret_value
    
    async def get_secret_as(self, secret_id: str, model_class: Type[T]) -> T:
        """Gets a secret and deserializes it to a model."""
        secret_string = await self.get_secret(secret_id)
        data = json.loads(secret_string)
        
        if hasattr(model_class, 'model_validate'):
            return model_class.model_validate(data)
        return model_class(**data)
    
    def invalidate(self, secret_id: Optional[str] = None) -> None:
        """Invalidates cache for a secret or all secrets."""
        if secret_id:
            self._cache.pop(secret_id, None)
        else:
            self._cache.clear()
```

### Secret Models with Pydantic

```python
from pydantic import BaseModel, Field

class DatabaseCredentials(BaseModel):
    username: str
    password: str
    host: str
    port: int = 5432
    dbname: str
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.dbname}"
    
    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.dbname}"

class ApiCredentials(BaseModel):
    api_key: str = Field(alias="apiKey")
    api_secret: str = Field(alias="apiSecret")
    base_url: str = Field(alias="baseUrl")
    
    class Config:
        populate_by_name = True
```

### Usage with FastAPI and asyncpg

```python
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
import asyncpg
import os

secrets_service = AsyncSecretsService(ttl_seconds=1800)
db_pool: Optional[asyncpg.Pool] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    
    creds = await secrets_service.get_secret_as(
        os.environ['DB_SECRET_ARN'],
        DatabaseCredentials
    )
    db_pool = await asyncpg.create_pool(
        creds.async_connection_string,
        min_size=5,
        max_size=20
    )
    
    yield
    
    if db_pool:
        await db_pool.close()

app = FastAPI(lifespan=lifespan)

async def get_db() -> asyncpg.Connection:
    async with db_pool.acquire() as conn:
        yield conn

@app.get("/users/{user_id}")
async def get_user(user_id: str, db: asyncpg.Connection = Depends(get_db)):
    return await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
```

### Lambda Handler with Lambda Powertools

```python
import os
import json
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters

logger = Logger()

@parameters.secrets.get_secret(
    name=os.environ['DB_SECRET_ARN'],
    transform='json',
    max_age=300
)
def get_db_credentials():
    pass

def handler(event, context):
    creds = get_db_credentials()
    
    logger.info("Connecting to database", extra={"host": creds['host']})
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Success"})
    }
```

## Important Rules

- Use `asyncio.Lock` to avoid multiple simultaneous requests to the same secret.
- Implement caching with TTL to reduce latency and costs.
- Use Pydantic for secret validation and typing.
- Use Lambda Powertools for automatic caching in Lambda.

## Example

```python
from fastapi import FastAPI, HTTPException
import os

app = FastAPI()
secrets_service = AsyncSecretsService(ttl_seconds=1800)

@app.get("/api/external-service")
async def call_external_service():
    api_creds = await secrets_service.get_secret_as(
        os.environ['API_SECRET_ARN'],
        ApiCredentials
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{api_creds.base_url}/data",
            headers={
                "X-API-Key": api_creds.api_key,
                "X-API-Secret": api_creds.api_secret
            }
        )
        return response.json()
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
