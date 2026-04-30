<!-- keywords: lambda, clean architecture, python, serverless, fastapi, pydantic, pytest, aws lambda, archetype -->
# Lambda Python Clean Architecture Archetype

## Purpose

Define the structure, patterns, and practices for developing AWS Lambda functions in Python following Clean Architecture principles, with support for FastAPI, Pydantic, pytest, and best practices from the Python serverless ecosystem.

## Scope of Application

- When creating new Lambda functions in Python
- To migrate existing Lambdas to a clean architecture
- As a structure guide for Python serverless projects
- During code reviews of Python Lambda functions

## Main Content

### Project Structure

```
lambda-python-clean/
├── src/
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   └── user.py
│   │   ├── ports/
│   │   │   ├── __init__.py
│   │   │   ├── inbound/
│   │   │   │   ├── __init__.py
│   │   │   │   └── user_service_port.py
│   │   │   └── outbound/
│   │   │       ├── __init__.py
│   │   │       └── user_repository_port.py
│   │   └── exceptions/
│   │       ├── __init__.py
│   │       └── domain_exceptions.py
│   ├── application/
│   │   ├── __init__.py
│   │   └── usecases/
│   │       ├── __init__.py
│   │       ├── create_user.py
│   │       └── get_user.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── inbound/
│   │   │   │   ├── __init__.py
│   │   │   │   └── api_gateway_handler.py
│   │   │   └── outbound/
│   │   │       ├── __init__.py
│   │   │       └── dynamodb_repository.py
│   │   └── config/
│   │       ├── __init__.py
│   │       └── settings.py
│   └── shared/
│       ├── __init__.py
│       ├── logger.py
│       └── responses.py
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── __init__.py
│   │   └── domain/
│   │       └── test_user.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_dynamodb_repository.py
│   └── conftest.py
├── handler.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── template.yaml
└── Makefile
```

### Domain Layer

#### Entities

```python
# src/domain/entities/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid

@dataclass
class User:
    """User domain entity."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    name: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        if not self.name:
            raise ValueError("Name is required")
    
    def deactivate(self) -> None:
        """Deactivates the user."""
        self.status = "inactive"
        self.updated_at = datetime.utcnow()
    
    def update_name(self, new_name: str) -> None:
        """Updates the user's name."""
        if not new_name:
            raise ValueError("Name cannot be empty")
        self.name = new_name
        self.updated_at = datetime.utcnow()
```

#### Ports

```python
# src/domain/ports/outbound/user_repository_port.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.user import User

class UserRepositoryPort(ABC):
    """Outbound port for user persistence."""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """Saves a user."""
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Finds a user by ID."""
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Finds a user by email."""
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Deletes a user."""
        pass
```

```python
# src/domain/ports/inbound/user_service_port.py
from abc import ABC, abstractmethod
from typing import Optional
from domain.entities.user import User

class UserServicePort(ABC):
    """Inbound port for user operations."""
    
    @abstractmethod
    async def create_user(self, email: str, name: str) -> User:
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def deactivate_user(self, user_id: str) -> User:
        pass
```

#### Domain Exceptions

```python
# src/domain/exceptions/domain_exceptions.py
class DomainException(Exception):
    """Base domain exception."""
    
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class UserNotFoundException(DomainException):
    """User not found."""
    
    def __init__(self, user_id: str):
        super().__init__(
            message=f"User with id {user_id} not found",
            code="USER_NOT_FOUND"
        )

class UserAlreadyExistsException(DomainException):
    """User already exists."""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"User with email {email} already exists",
            code="USER_ALREADY_EXISTS"
        )

class ValidationException(DomainException):
    """Validation error."""
    
    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR")
```

### Application Layer

```python
# src/application/usecases/create_user.py
from domain.entities.user import User
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.exceptions.domain_exceptions import UserAlreadyExistsException
from shared.logger import get_logger

logger = get_logger(__name__)

class CreateUserUseCase:
    """Use case for creating a user."""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self._user_repository = user_repository
    
    async def execute(self, email: str, name: str) -> User:
        """Executes user creation."""
        logger.info(f"Creating user with email: {email}")
        
        # Check if user already exists
        existing_user = await self._user_repository.find_by_email(email)
        if existing_user:
            logger.warning(f"User with email {email} already exists")
            raise UserAlreadyExistsException(email)
        
        # Create and save user
        user = User(email=email, name=name)
        saved_user = await self._user_repository.save(user)
        
        logger.info(f"User created successfully with id: {saved_user.id}")
        return saved_user
```

```python
# src/application/usecases/get_user.py
from typing import Optional
from domain.entities.user import User
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from domain.exceptions.domain_exceptions import UserNotFoundException
from shared.logger import get_logger

logger = get_logger(__name__)

class GetUserUseCase:
    """Use case for retrieving a user."""
    
    def __init__(self, user_repository: UserRepositoryPort):
        self._user_repository = user_repository
    
    async def execute(self, user_id: str) -> User:
        """Retrieves a user by ID."""
        logger.info(f"Getting user with id: {user_id}")
        
        user = await self._user_repository.find_by_id(user_id)
        if not user:
            logger.warning(f"User with id {user_id} not found")
            raise UserNotFoundException(user_id)
        
        return user
```


### Infrastructure Layer

#### DynamoDB Adapter

```python
# src/infrastructure/adapters/outbound/dynamodb_repository.py
from typing import Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

from domain.entities.user import User
from domain.ports.outbound.user_repository_port import UserRepositoryPort
from infrastructure.config.settings import Settings
from shared.logger import get_logger

logger = get_logger(__name__)

class DynamoDBUserRepository(UserRepositoryPort):
    """Repository implementation with DynamoDB."""
    
    def __init__(self, settings: Settings):
        self._table_name = settings.users_table_name
        self._dynamodb = boto3.resource('dynamodb')
        self._table = self._dynamodb.Table(self._table_name)
    
    async def save(self, user: User) -> User:
        """Saves a user to DynamoDB."""
        try:
            item = {
                'PK': f'USER#{user.id}',
                'SK': f'USER#{user.id}',
                'GSI1PK': f'EMAIL#{user.email}',
                'GSI1SK': f'USER#{user.id}',
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'status': user.status,
                'createdAt': user.created_at.isoformat(),
                'updatedAt': user.updated_at.isoformat() if user.updated_at else None,
                'entityType': 'USER'
            }
            
            self._table.put_item(Item=item)
            logger.info(f"User {user.id} saved to DynamoDB")
            return user
            
        except ClientError as e:
            logger.error(f"Error saving user to DynamoDB: {e}")
            raise
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Finds a user by ID."""
        try:
            response = self._table.get_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'USER#{user_id}'
                }
            )
            
            item = response.get('Item')
            if not item:
                return None
            
            return self._to_entity(item)
            
        except ClientError as e:
            logger.error(f"Error finding user by id: {e}")
            raise
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Finds a user by email using GSI."""
        try:
            response = self._table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={':pk': f'EMAIL#{email}'}
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            return self._to_entity(items[0])
            
        except ClientError as e:
            logger.error(f"Error finding user by email: {e}")
            raise
    
    async def delete(self, user_id: str) -> bool:
        """Deletes a user."""
        try:
            self._table.delete_item(
                Key={
                    'PK': f'USER#{user_id}',
                    'SK': f'USER#{user_id}'
                }
            )
            return True
        except ClientError as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    def _to_entity(self, item: dict) -> User:
        """Converts a DynamoDB item to an entity."""
        return User(
            id=item['id'],
            email=item['email'],
            name=item['name'],
            status=item['status'],
            created_at=datetime.fromisoformat(item['createdAt']),
            updated_at=datetime.fromisoformat(item['updatedAt']) if item.get('updatedAt') else None
        )
```

#### API Gateway Handler

```python
# src/infrastructure/adapters/inbound/api_gateway_handler.py
from typing import Any, Dict
from pydantic import BaseModel, EmailStr, validator
import json

from application.usecases.create_user import CreateUserUseCase
from application.usecases.get_user import GetUserUseCase
from infrastructure.adapters.outbound.dynamodb_repository import DynamoDBUserRepository
from infrastructure.config.settings import Settings
from domain.exceptions.domain_exceptions import (
    DomainException,
    UserNotFoundException,
    UserAlreadyExistsException
)
from shared.responses import success_response, error_response
from shared.logger import get_logger

logger = get_logger(__name__)

# Pydantic DTOs
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    status: str
    created_at: str

# Dependency initialization
settings = Settings()
user_repository = DynamoDBUserRepository(settings)
create_user_usecase = CreateUserUseCase(user_repository)
get_user_usecase = GetUserUseCase(user_repository)

async def create_user_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler for creating a user."""
    try:
        body = json.loads(event.get('body', '{}'))
        request = CreateUserRequest(**body)
        
        user = await create_user_usecase.execute(
            email=request.email,
            name=request.name
        )
        
        response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            created_at=user.created_at.isoformat()
        )
        
        return success_response(response.dict(), status_code=201)
        
    except UserAlreadyExistsException as e:
        return error_response(e.message, e.code, 409)
    except ValueError as e:
        return error_response(str(e), "VALIDATION_ERROR", 400)
    except Exception as e:
        logger.exception("Unexpected error creating user")
        return error_response("Internal server error", "INTERNAL_ERROR", 500)

async def get_user_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handler for retrieving a user."""
    try:
        user_id = event.get('pathParameters', {}).get('id')
        if not user_id:
            return error_response("User ID is required", "VALIDATION_ERROR", 400)
        
        user = await get_user_usecase.execute(user_id)
        
        response = UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            status=user.status,
            created_at=user.created_at.isoformat()
        )
        
        return success_response(response.dict())
        
    except UserNotFoundException as e:
        return error_response(e.message, e.code, 404)
    except Exception as e:
        logger.exception("Unexpected error getting user")
        return error_response("Internal server error", "INTERNAL_ERROR", 500)
```

#### Configuration

```python
# src/infrastructure/config/settings.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application configuration."""
    
    # AWS
    aws_region: str = "us-east-1"
    
    # DynamoDB
    users_table_name: str = "users"
    
    # Logging
    log_level: str = "INFO"
    
    # Environment
    environment: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

### Shared Utilities

```python
# src/shared/logger.py
import logging
import json
import sys
from typing import Any

class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Gets a configured logger."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger
```

```python
# src/shared/responses.py
from typing import Any, Dict
import json

def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    """Generates a success response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(data)
    }

def error_response(message: str, code: str, status_code: int) -> Dict[str, Any]:
    """Generates an error response following RFC 7807."""
    error_body = {
        "type": f"about:blank",
        "title": message,
        "status": status_code,
        "detail": message,
        "instance": code
    }
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/problem+json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(error_body)
    }
```

### Main Handler

```python
# handler.py
import asyncio
from infrastructure.adapters.inbound.api_gateway_handler import (
    create_user_handler,
    get_user_handler
)

def create_user(event, context):
    """Entry point for creating a user."""
    return asyncio.get_event_loop().run_until_complete(
        create_user_handler(event, context)
    )

def get_user(event, context):
    """Entry point for retrieving a user."""
    return asyncio.get_event_loop().run_until_complete(
        get_user_handler(event, context)
    )
```

### Testing

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.entities.user import User
from domain.ports.outbound.user_repository_port import UserRepositoryPort

@pytest.fixture
def mock_user_repository():
    """Mock user repository."""
    return AsyncMock(spec=UserRepositoryPort)

@pytest.fixture
def sample_user():
    """Sample user for tests."""
    return User(
        id="test-id-123",
        email="test@example.com",
        name="Test User"
    )
```

```python
# tests/unit/domain/test_user.py
import pytest
from domain.entities.user import User

class TestUser:
    def test_create_user_success(self):
        user = User(email="test@example.com", name="Test User")
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.status == "active"
        assert user.id is not None
    
    def test_create_user_invalid_email(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid-email", name="Test User")
    
    def test_create_user_empty_name(self):
        with pytest.raises(ValueError, match="Name is required"):
            User(email="test@example.com", name="")
    
    def test_deactivate_user(self):
        user = User(email="test@example.com", name="Test User")
        user.deactivate()
        
        assert user.status == "inactive"
        assert user.updated_at is not None
```

```python
# tests/unit/application/test_create_user.py
import pytest
from unittest.mock import AsyncMock
from application.usecases.create_user import CreateUserUseCase
from domain.entities.user import User
from domain.exceptions.domain_exceptions import UserAlreadyExistsException

class TestCreateUserUseCase:
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_user_repository):
        mock_user_repository.find_by_email.return_value = None
        mock_user_repository.save.return_value = User(
            email="test@example.com",
            name="Test User"
        )
        
        usecase = CreateUserUseCase(mock_user_repository)
        result = await usecase.execute("test@example.com", "Test User")
        
        assert result.email == "test@example.com"
        mock_user_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_already_exists(self, mock_user_repository, sample_user):
        mock_user_repository.find_by_email.return_value = sample_user
        
        usecase = CreateUserUseCase(mock_user_repository)
        
        with pytest.raises(UserAlreadyExistsException):
            await usecase.execute("test@example.com", "Test User")
```

### SAM Template

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Lambda Python Clean Architecture

Globals:
  Function:
    Timeout: 30
    Runtime: python3.11
    MemorySize: 256
    Environment:
      Variables:
        USERS_TABLE_NAME: !Ref UsersTable
        LOG_LEVEL: INFO

Resources:
  CreateUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.create_user
      CodeUri: .
      Events:
        CreateUser:
          Type: Api
          Properties:
            Path: /users
            Method: post
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable

  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.get_user
      CodeUri: .
      Events:
        GetUser:
          Type: Api
          Properties:
            Path: /users/{id}
            Method: get
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable

  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: users
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: GSI1PK
          AttributeType: S
        - AttributeName: GSI1SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: GSI1
          KeySchema:
            - AttributeName: GSI1PK
              KeyType: HASH
            - AttributeName: GSI1SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
```

## Important Rules

1. **Pure domain**: No framework dependencies in the domain layer
2. **Pydantic for DTOs**: Use Pydantic for validation in the infrastructure layer
3. **Dataclasses for entities**: Use dataclasses for domain entities
4. **Async/await**: Use asynchronous programming for I/O operations
5. **Type hints**: Always include type hints throughout the code
6. **Structured logging**: JSON logs with relevant context
7. **Error handling**: Specific domain exceptions
8. **Testing**: Minimum 80% coverage in domain and application layers

## Example

See the complete structure in the main content.

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
