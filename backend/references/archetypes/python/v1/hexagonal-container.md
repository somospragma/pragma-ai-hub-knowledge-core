<!-- keywords: hexagonal architecture, python, container, fastapi, sqlalchemy, ecs, fargate, microservice, archetype -->
# Hexagonal Python Container Archetype

## Purpose

Define the structure, patterns, and practices for developing Python container microservices following hexagonal architecture, with FastAPI as the web framework, SQLAlchemy for persistence, and full support for ECS/Fargate deployment.

This archetype implements the canonical hexagonal multi-module architecture defined in the corresponding reference, adapted to Python idioms.

## Scope of Application

- When creating new Python container microservices
- For services with complex domain logic
- When multiple input/output adapters are required
- For services that need high testability and maintainability

## Main Content

### Project Structure

```
project/
├── domain/
│   ├── model/
│   │   ├── entities/               ← Pure dataclasses, no framework
│   │   └── value_objects/          ← Frozen dataclasses
│   ├── ports/                      ← ABC interfaces (*Gateway). Flat, no inbound/outbound.
│   │   ├── user_gateway.py
│   │   └── notification_gateway.py
│   ├── usecases/                   ← Use case classes (*UseCase)
│   │   ├── create_user_use_case.py
│   │   └── get_user_use_case.py
│   ├── services/                   ← Domain services (shared logic across use cases)
│   └── exceptions/                 ← Domain exceptions
├── infrastructure/
│   ├── driven_adapters/
│   │   ├── persistence/            ← SQLAlchemy async repository
│   │   ├── rest_api_{name}/        ← External API consumer (httpx/aiohttp)
│   │   └── .../
│   ├── entry_points/
│   │   └── rest/                   ← FastAPI router + handlers
│   └── helpers/                    ← cross-cutting infra utilities
├── application/
│   └── app_service/                ← Main app, DI container config, settings
│       ├── main.py
│       ├── config/
│       │   └── container.py        ← Dependency injection container
│       └── resources/
│           └── settings.py
├── tests/
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

### Domain Layer

#### Value Objects

```python
# domain/model/value_objects/email.py
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Email:
    """Value Object for email."""
    
    value: str
    
    def __post_init__(self):
        if not self._is_valid(self.value):
            raise ValueError(f"Invalid email format: {self.value}")
    
    @staticmethod
    def _is_valid(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        return self.value
```

```python
# domain/model/value_objects/money.py
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

@dataclass(frozen=True)
class Money:
    """Value Object for money."""
    
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        object.__setattr__(
            self, 
            'amount', 
            self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        )
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def multiply(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)
```

#### Entities

```python
# domain/model/entities/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import uuid

from domain.model.value_objects.email import Email

@dataclass
class User:
    """User domain entity (Aggregate Root)."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: Email = field(default=None)
    name: str = ""
    status: str = "active"
    roles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    version: int = 0
    
    def __post_init__(self):
        if isinstance(self.email, str):
            object.__setattr__(self, 'email', Email(self.email))
        self._validate()
    
    def _validate(self):
        if not self.name:
            raise ValueError("Name is required")
        if len(self.name) < 2:
            raise ValueError("Name must be at least 2 characters")
    
    def activate(self) -> None:
        if self.status == "active":
            raise ValueError("User is already active")
        self.status = "active"
        self._touch()
    
    def deactivate(self) -> None:
        if self.status == "inactive":
            raise ValueError("User is already inactive")
        self.status = "inactive"
        self._touch()
    
    def add_role(self, role: str) -> None:
        if role in self.roles:
            raise ValueError(f"User already has role: {role}")
        self.roles.append(role)
        self._touch()
    
    def remove_role(self, role: str) -> None:
        if role not in self.roles:
            raise ValueError(f"User does not have role: {role}")
        self.roles.remove(role)
        self._touch()
    
    def update_name(self, new_name: str) -> None:
        if len(new_name) < 2:
            raise ValueError("Name must be at least 2 characters")
        self.name = new_name
        self._touch()
    
    def _touch(self) -> None:
        self.updated_at = datetime.utcnow()
        self.version += 1
```

#### Ports (*Gateway — flat, no inbound/outbound)

Ports are ABC interfaces that define what the domain needs from the outside world. They live in a flat `domain/ports/` directory. The naming convention is **always `*Gateway`** — this is NON-NEGOTIABLE per `hexagonal-layers.md`.

```python
# domain/ports/user_gateway.py
from abc import ABC, abstractmethod
from typing import Optional, List
from domain.model.entities.user import User

class UserGateway(ABC):
    """Gateway interface for user persistence."""
    
    @abstractmethod
    async def save(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        pass
```

```python
# domain/ports/notification_gateway.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class NotificationGateway(ABC):
    """Gateway interface for notifications."""
    
    @abstractmethod
    async def send_email(
        self, 
        to: str, 
        subject: str, 
        body: str,
        template_data: Dict[str, Any] = None
    ) -> bool:
        pass
    
    @abstractmethod
    async def send_sms(self, phone_number: str, message: str) -> bool:
        pass
```

#### Domain Exceptions

```python
# domain/exceptions/domain_exceptions.py

class DomainException(Exception):
    """Base domain exception."""
    pass

class UserNotFoundException(DomainException):
    def __init__(self, user_id: str):
        super().__init__(f"User not found: {user_id}")

class UserAlreadyExistsException(DomainException):
    def __init__(self, email: str):
        super().__init__(f"User already exists with email: {email}")
```

#### Use Cases (domain/usecases/)

Use cases live in `domain/usecases/`, NOT in `application/`. They receive `*Gateway` interfaces via constructor and contain business logic only. No framework annotations.

```python
# domain/usecases/create_user_use_case.py
import logging
from domain.model.entities.user import User
from domain.model.value_objects.email import Email
from domain.ports.user_gateway import UserGateway
from domain.ports.notification_gateway import NotificationGateway
from domain.exceptions.domain_exceptions import UserAlreadyExistsException

logger = logging.getLogger(__name__)

class CreateUserUseCase:
    """Use case for creating a user."""
    
    def __init__(
        self, 
        user_gateway: UserGateway,
        notification_gateway: NotificationGateway
    ):
        self._user_gateway = user_gateway
        self._notification_gateway = notification_gateway
    
    async def execute(self, email: str, name: str, roles: list[str] = None) -> User:
        """Executes user creation."""
        logger.info(f"Creating user with email: {email}")
        
        if await self._user_gateway.exists_by_email(email):
            raise UserAlreadyExistsException(email)
        
        user = User(
            email=Email(email),
            name=name,
            roles=roles or []
        )
        
        saved_user = await self._user_gateway.save(user)
        
        await self._notification_gateway.send_email(
            to=str(saved_user.email),
            subject="Welcome",
            body=f"Welcome {saved_user.name}!"
        )
        
        logger.info(f"User created: {saved_user.id}")
        return saved_user
```

```python
# domain/usecases/get_user_use_case.py
import logging
from typing import Optional
from domain.model.entities.user import User
from domain.ports.user_gateway import UserGateway
from domain.exceptions.domain_exceptions import UserNotFoundException

logger = logging.getLogger(__name__)

class GetUserUseCase:
    """Use case for retrieving a user."""
    
    def __init__(self, user_gateway: UserGateway):
        self._user_gateway = user_gateway
    
    async def execute(self, user_id: str) -> User:
        """Retrieves a user by ID."""
        user = await self._user_gateway.find_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        return user
```

### Infrastructure Layer

#### Driven Adapters (outbound — implement *Gateway)

Each driven adapter implements a `*Gateway` interface from `domain/ports/` using concrete technology. The implementation class follows the `*Adapter` naming convention.

```python
# infrastructure/driven_adapters/persistence/user_sqlalchemy_adapter.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.exc import IntegrityError

from domain.model.entities.user import User
from domain.model.value_objects.email import Email
from domain.ports.user_gateway import UserGateway
from infrastructure.driven_adapters.persistence.models.user_model import UserModel
from infrastructure.driven_adapters.persistence.mappers.user_entity_mapper import UserEntityMapper

class UserSqlAlchemyAdapter(UserGateway):
    """Implements UserGateway with SQLAlchemy async."""
    
    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = UserEntityMapper()
    
    async def save(self, user: User) -> User:
        model = self._mapper.to_model(user)
        self._session.add(model)
        await self._session.flush()
        return self._mapper.to_entity(model)
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.get(UserModel, user_id)
        return self._mapper.to_entity(result) if result else None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._mapper.to_entity(model) if model else None
    
    async def find_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._mapper.to_entity(m) for m in result.scalars().all()]
    
    async def delete(self, user_id: str) -> bool:
        model = await self._session.get(UserModel, user_id)
        if model:
            await self._session.delete(model)
            return True
        return False
    
    async def exists_by_email(self, email: str) -> bool:
        stmt = select(exists().where(UserModel.email == email))
        result = await self._session.execute(stmt)
        return result.scalar()
```

```python
# infrastructure/driven_adapters/persistence/models/user_model.py
from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    """SQLAlchemy model — internal to the persistence adapter."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="active")
    roles = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=0)
```

```python
# infrastructure/driven_adapters/persistence/mappers/user_entity_mapper.py
from domain.model.entities.user import User
from domain.model.value_objects.email import Email
from infrastructure.driven_adapters.persistence.models.user_model import UserModel

class UserEntityMapper:
    """Maps between domain User entity and SQLAlchemy UserModel."""
    
    def to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=Email(model.email),
            name=model.name,
            status=model.status,
            roles=model.roles or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version
        )
    
    def to_model(self, entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            name=entity.name,
            status=entity.status,
            roles=entity.roles,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            version=entity.version
        )
```

#### Entry Points (inbound — call use cases)

Entry points receive external stimuli (HTTP, events) and delegate to use cases. DTOs live inside each entry point.

```python
# infrastructure/entry_points/rest/dto/user_dto.py
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class CreateUserRequest(BaseModel):
    """DTO for creating a user."""
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    roles: List[str] = Field(default_factory=list)

class UpdateUserRequest(BaseModel):
    """DTO for updating a user."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    status: Optional[str] = Field(None, pattern='^(active|inactive)$')

class UserResponse(BaseModel):
    """User response DTO."""
    id: str
    email: str
    name: str
    status: str
    roles: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class UserListResponse(BaseModel):
    """User list DTO."""
    items: List[UserResponse]
    total: int
    skip: int
    limit: int
```

```python
# infrastructure/entry_points/rest/user_controller.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from domain.usecases.create_user_use_case import CreateUserUseCase
from domain.usecases.get_user_use_case import GetUserUseCase
from domain.exceptions.domain_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)
from infrastructure.entry_points.rest.dto.user_dto import (
    CreateUserRequest,
    UserResponse
)
from infrastructure.entry_points.rest.mappers.user_rest_mapper import UserRestMapper

router = APIRouter(prefix="/api/v1/users", tags=["users"])

class UserController:
    """FastAPI controller for user operations."""
    
    def __init__(
        self,
        create_user_use_case: CreateUserUseCase,
        get_user_use_case: GetUserUseCase
    ):
        self._create_user = create_user_use_case
        self._get_user = get_user_use_case
        self._mapper = UserRestMapper()
        self._register_routes()
    
    def _register_routes(self):
        router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)(self.create_user)
        router.get("/{user_id}", response_model=UserResponse)(self.get_user)
    
    async def create_user(self, request: CreateUserRequest) -> UserResponse:
        try:
            user = await self._create_user.execute(
                email=request.email,
                name=request.name,
                roles=request.roles
            )
            return self._mapper.to_response(user)
        except UserAlreadyExistsException as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    
    async def get_user(self, user_id: str) -> UserResponse:
        try:
            user = await self._get_user.execute(user_id)
            return self._mapper.to_response(user)
        except UserNotFoundException as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
```

```python
# infrastructure/entry_points/rest/mappers/user_rest_mapper.py
from domain.model.entities.user import User
from infrastructure.entry_points.rest.dto.user_dto import UserResponse

class UserRestMapper:
    """Maps between domain User entity and REST DTOs."""
    
    def to_response(self, user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            email=str(user.email),
            name=user.name,
            status=user.status,
            roles=user.roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
```

#### Helpers (cross-cutting infra utilities)

Shared utilities used by both driven adapters and entry points. NOT for business logic.

```python
# infrastructure/helpers/correlation_id.py
from contextvars import ContextVar
import uuid

correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

def get_correlation_id() -> str:
    return correlation_id_var.get() or str(uuid.uuid4())

def set_correlation_id(cid: str) -> None:
    correlation_id_var.set(cid)
```

```python
# infrastructure/helpers/logging_config.py
import logging
from infrastructure.helpers.correlation_id import get_correlation_id

class CorrelationFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True

def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.addFilter(CorrelationFilter())
    formatter = logging.Formatter(
        '%(asctime)s [%(correlation_id)s] %(levelname)s %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logging.root.addHandler(handler)
    logging.root.setLevel(level)
```

### Application Layer (assembler only)

The application layer assembles all modules, boots the framework, and configures dependency injection. It contains NO business logic and NO use cases.

```python
# application/app_service/resources/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Centralized microservice configuration."""
    
    app_name: str = "python-hexagonal-service"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
    database_pool_size: int = 10
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
```

```python
# application/app_service/config/container.py
from domain.usecases.create_user_use_case import CreateUserUseCase
from domain.usecases.get_user_use_case import GetUserUseCase
from domain.ports.user_gateway import UserGateway
from domain.ports.notification_gateway import NotificationGateway
from infrastructure.driven_adapters.persistence.user_sqlalchemy_adapter import UserSqlAlchemyAdapter

class Container:
    """Dependency injection container. Wires *Gateway implementations to use cases."""
    
    def __init__(self, session_factory, notification_adapter: NotificationGateway):
        self._session_factory = session_factory
        self._notification_adapter = notification_adapter
    
    def create_user_use_case(self) -> CreateUserUseCase:
        session = self._session_factory()
        user_gateway: UserGateway = UserSqlAlchemyAdapter(session)
        return CreateUserUseCase(
            user_gateway=user_gateway,
            notification_gateway=self._notification_adapter
        )
    
    def get_user_use_case(self) -> GetUserUseCase:
        session = self._session_factory()
        user_gateway: UserGateway = UserSqlAlchemyAdapter(session)
        return GetUserUseCase(user_gateway=user_gateway)
```

```python
# application/app_service/main.py
from fastapi import FastAPI
from application.app_service.resources.settings import Settings
from application.app_service.config.container import Container
from infrastructure.entry_points.rest.user_controller import router as user_router
from infrastructure.helpers.logging_config import setup_logging

def create_app() -> FastAPI:
    settings = Settings()
    setup_logging()
    
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.include_router(user_router)
    
    return app

app = create_app()
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "application.app_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Dependency Rules (Python adaptation)

```
domain/model       → nothing (pure Python dataclasses)
domain/ports       → domain/model only
domain/usecases    → domain/model + domain/ports
domain/services    → domain/model + domain/ports
infra/helpers      → domain/model + domain/ports (+ framework deps)
infra/driven_adap  → domain/model + domain/ports + infra/helpers
infra/entry_points → domain/model + domain/ports + domain/usecases + infra/helpers
application        → all modules
```

Dependencies always point toward the domain. Infrastructure depends on the domain, never the other way around.

## Naming Conventions (Python adaptation)

| Component | Convention | Example | Location |
|-----------|-----------|---------|----------|
| Domain entity | Dataclass | `User`, `Order` | `domain/model/entities/` |
| Value object | Frozen dataclass | `Email`, `Money` | `domain/model/value_objects/` |
| Output port (ABC) | `*Gateway` | `UserGateway`, `NotificationGateway` | `domain/ports/` |
| Use case | `*UseCase` | `CreateUserUseCase`, `GetUserUseCase` | `domain/usecases/` |
| Driven adapter | `*Adapter` | `UserSqlAlchemyAdapter`, `NotificationSesAdapter` | `infrastructure/driven_adapters/*/` |
| Framework model | `*Model` | `UserModel` | `driven_adapters/*/models/` |
| Entity mapper | `*EntityMapper` | `UserEntityMapper` | `driven_adapters/*/mappers/` |
| REST mapper | `*RestMapper` | `UserRestMapper` | `entry_points/*/mappers/` |
| DTO request | `*Request` (Pydantic) | `CreateUserRequest` | `entry_points/*/dto/` |
| DTO response | `*Response` (Pydantic) | `UserResponse` | `entry_points/*/dto/` |
| Controller | `*Controller` | `UserController` | `entry_points/rest/` |

The `*Gateway` convention for ABC interfaces and `*Adapter` for implementations is **NON-NEGOTIABLE**.

## Anti-patterns — What NOT to do

| Anti-pattern | Why it's wrong | Correct structure |
|---|---|---|
| Use cases in `application/` | `application/app_service/` is ONLY the assembler: `main.py` + `container.py`. No business logic. | Use cases MUST be in `domain/usecases/`. |
| `domain/ports/inbound/` and `domain/ports/outbound/` | The standard does not use `in/out` separation for ports. | Ports MUST be in `domain/ports/` (flat). Only `*Gateway` ABC classes. |
| `*Port` or `*Repository` naming for domain interfaces | Violates the mandatory `*Gateway` convention. | Always use `*Gateway` (e.g., `UserGateway`, not `UserRepositoryPort`). |
| Missing `infrastructure/helpers/` | cross-cutting infra utilities end up duplicated or misplaced. | `infrastructure/helpers/` MUST exist for shared infra concerns. |
| DTOs in a shared layer | DTOs belong inside each entry point, not in a shared `dto/` package. | DTOs live in `infrastructure/entry_points/*/dto/`. |
| Flat `infrastructure/` with no adapter separation | Each adapter must be independently testable. | Use `driven_adapters/` and `entry_points/` with individual modules per adapter. |

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
