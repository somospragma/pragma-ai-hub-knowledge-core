<!-- keywords: parameter store, aws ssm, configuration management, boto3, aiobotocore, async, python -->
# AWS Parameter Store Patterns - Python Implementation

## Purpose

Implement configuration management with AWS Parameter Store in Python using boto3 and aiobotocore with asynchronous patterns.

## Scope of Application

- When developing in Python with FastAPI or asyncio.
- When dynamic configuration is needed.
- To implement feature flags.
- When using Lambda Powertools.

## Main Content

### Dependencies

```txt
boto3>=1.26.0
aiobotocore>=2.5.0
pydantic>=2.0.0
aws-lambda-powertools>=2.0.0
```

### Asynchronous Implementation

```python
import asyncio
import json
from typing import TypeVar, Type, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiobotocore.session

T = TypeVar('T')

@dataclass
class CachedParameter:
    value: str
    expires_at: datetime

class AsyncParameterService:
    def __init__(
        self, 
        app_name: str,
        environment: str,
        cache_ttl_seconds: int = 300
    ):
        self.session = aiobotocore.session.get_session()
        self.app_name = app_name
        self.environment = environment
        self.ttl = timedelta(seconds=cache_ttl_seconds)
        self._cache: Dict[str, CachedParameter] = {}
        self._lock = asyncio.Lock()
    
    async def get_parameter(self, name: str, decrypt: bool = True) -> str:
        """Gets a parameter with caching."""
        full_path = self._build_path(name)
        
        cached = self._cache.get(full_path)
        if cached and cached.expires_at > datetime.utcnow():
            return cached.value
        
        async with self._lock:
            cached = self._cache.get(full_path)
            if cached and cached.expires_at > datetime.utcnow():
                return cached.value
            
            async with self.session.create_client('ssm') as client:
                response = await client.get_parameter(
                    Name=full_path,
                    WithDecryption=decrypt
                )
                value = response['Parameter']['Value']
                
                self._cache[full_path] = CachedParameter(
                    value=value,
                    expires_at=datetime.utcnow() + self.ttl
                )
                
                return value
    
    async def get_parameter_as(self, name: str, model_class: Type[T]) -> T:
        """Gets a parameter and deserializes it."""
        value = await self.get_parameter(name)
        data = json.loads(value)
        
        if hasattr(model_class, 'model_validate'):
            return model_class.model_validate(data)
        return model_class(**data)
    
    async def get_parameters_by_path(self, path: str) -> Dict[str, str]:
        """Gets all parameters under a path."""
        full_path = self._build_path(path)
        parameters = {}
        
        async with self.session.create_client('ssm') as client:
            paginator = client.get_paginator('get_parameters_by_path')
            
            async for page in paginator.paginate(
                Path=full_path,
                Recursive=True,
                WithDecryption=True
            ):
                for param in page['Parameters']:
                    key = param['Name'].replace(full_path, '').lstrip('/')
                    parameters[key] = param['Value']
        
        return parameters
    
    def _build_path(self, name: str) -> str:
        if name.startswith('/'):
            return name
        return f"/{self.app_name}/{self.environment}/{name}"
    
    def invalidate(self, name: Optional[str] = None) -> None:
        if name:
            full_path = self._build_path(name)
            self._cache.pop(full_path, None)
        else:
            self._cache.clear()
```

### Dynamic Configuration with Pydantic

```python
from pydantic import BaseModel
from typing import Dict, Optional
import asyncio

class DatabaseConfig(BaseModel):
    host: str
    port: int = 5432

class CacheConfig(BaseModel):
    ttl: int = 300

class FeatureFlags(BaseModel):
    new_ui: bool = False
    beta_features: bool = False

class AppConfig(BaseModel):
    log_level: str = "INFO"
    api_timeout: int = 30
    database: DatabaseConfig
    cache: CacheConfig
    feature_flags: FeatureFlags

class DynamicConfigService:
    def __init__(self, parameter_service: AsyncParameterService):
        self.parameter_service = parameter_service
        self._current_config: Optional[AppConfig] = None
        self._refresh_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        await self.refresh()
        self._start_polling()
    
    async def refresh(self) -> None:
        params = await self.parameter_service.get_parameters_by_path("/config")
        
        self._current_config = AppConfig(
            log_level=params.get("log-level", "INFO"),
            api_timeout=int(params.get("api-timeout", "30")),
            database=DatabaseConfig(
                host=params.get("database/host", "localhost"),
                port=int(params.get("database/port", "5432"))
            ),
            cache=CacheConfig(
                ttl=int(params.get("cache/ttl", "300"))
            ),
            feature_flags=FeatureFlags(
                **json.loads(params.get("feature-flags", "{}"))
            )
        )
    
    def _start_polling(self) -> None:
        async def poll():
            while True:
                await asyncio.sleep(300)
                try:
                    await self.refresh()
                except Exception as e:
                    print(f"Failed to refresh config: {e}")
        
        self._refresh_task = asyncio.create_task(poll())
    
    @property
    def config(self) -> AppConfig:
        if not self._current_config:
            raise RuntimeError("Configuration not initialized")
        return self._current_config
    
    def is_feature_enabled(self, feature: str) -> bool:
        return getattr(self.config.feature_flags, feature, False)
```

### Lambda with Lambda Powertools

```python
from aws_lambda_powertools.utilities import parameters
import os
import json

@parameters.ssm.get_parameter(
    name=f"/{os.environ['APP_NAME']}/{os.environ['ENVIRONMENT']}/log-level",
    max_age=300
)
def get_log_level():
    pass

@parameters.ssm.get_parameters(
    path=f"/{os.environ['APP_NAME']}/{os.environ['ENVIRONMENT']}/database",
    recursive=True,
    decrypt=True,
    max_age=300
)
def get_database_config():
    pass

def handler(event, context):
    log_level = get_log_level()
    db_config = get_database_config()
    
    print(f"Log level: {log_level}")
    print(f"DB Host: {db_config.get('host')}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Success"})
    }
```

## Important Rules

- Use `asyncio.Lock` to avoid multiple simultaneous requests.
- Implement caching with TTL to reduce latency and costs.
- Use Pydantic for configuration validation and typing.
- Use Lambda Powertools for automatic caching in Lambda.

## Example

```python
from fastapi import FastAPI
import os

app = FastAPI()
parameter_service = AsyncParameterService(
    app_name="myapp",
    environment=os.environ.get("ENVIRONMENT", "dev"),
    cache_ttl_seconds=300
)
config_service = DynamicConfigService(parameter_service)

@app.on_event("startup")
async def startup():
    await config_service.initialize()

@app.get("/features/{feature}")
async def check_feature(feature: str):
    enabled = config_service.is_feature_enabled(feature)
    return {"feature": feature, "enabled": enabled}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
