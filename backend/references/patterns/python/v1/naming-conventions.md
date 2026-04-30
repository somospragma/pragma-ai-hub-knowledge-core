<!-- keywords: naming conventions, nomenclatura, files, modules, classes, hexagonal, python -->
# Reference: Naming Conventions — Python

## Purpose

Define the mandatory naming conventions for classes, files, and modules in Python hexagonal microservices.

## Scope of Application

All Python projects (FastAPI, Lambda, container). NON-NEGOTIABLE.

## Step by Step / Guidelines

### Class Naming (PascalCase) and File Naming (snake_case)

| Component | Suffix | Class Name | File Name |
|-----------|--------|------------|-----------|
| Domain entity | _(none)_ | `Account` | `account.py` |
| Value object | _(none, frozen)_ | `Money` | `money.py` |
| Domain enum | _(none)_ | `OrderStatus` | `order_status.py` |
| Output port (ABC) | `*Gateway` | `AccountGateway` | `account_gateway.py` |
| Use case | `*UseCase` | `CreateAccountUseCase` | `create_account_use_case.py` |
| Domain service | `*Service` | `PricingService` | `pricing_service.py` |
| Driven adapter | `*Adapter` | `AccountSqlAlchemyAdapter` | `account_sqlalchemy_adapter.py` |
| Framework model (SQLAlchemy) | `*Model` | `AccountModel` | `account_model.py` |
| Framework model (DynamoDB) | `*Item` | `AccountItem` | `account_item.py` |
| Persistence mapper | `*EntityMapper` | `AccountEntityMapper` | `account_entity_mapper.py` |
| REST mapper | `*RestMapper` | `AccountRestMapper` | `account_rest_mapper.py` |
| Controller (FastAPI) | `*Controller` | `AccountController` | `account_controller.py` |
| DTO request (Pydantic) | `*Request` | `CreateAccountRequest` | `account_dto.py` (grouped) |
| DTO response (Pydantic) | `*Response` | `AccountResponse` | `account_dto.py` (grouped) |
| Domain exception | `*Exception` | `AccountNotFoundException` | `domain_exceptions.py` (grouped) |
| Lambda handler | `handler` (function) | `handler()` | `handler.py` |

### Mapper Rules (Python — manual classes)

Mappers are plain Python classes with `to_entity()` and `to_model()` methods. No framework needed.

```python
class AccountEntityMapper:
    def to_entity(self, model: AccountModel) -> Account:
        return Account(id=model.id, name=model.name, email=Email(model.email))
    
    def to_model(self, entity: Account) -> AccountModel:
        return AccountModel(id=entity.id, name=entity.name, email=str(entity.email))
```

### Module/Folder Naming (snake_case)

| Module type | Pattern | Example |
|-------------|---------|---------|
| Driven adapter (REST) | `rest_api_{system}` | `rest_api_t24`, `rest_api_abanks` |
| Driven adapter (DB) | `persistence` | `persistence` |
| Entry point (FastAPI) | `rest` | `rest` |
| Entry point (Lambda) | `functions` | `functions` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app_service` | `app_service` |

### Package/Import Naming

```python
from domain.model.entities.account import Account
from domain.ports.account_gateway import AccountGateway
from domain.usecases.create_account_use_case import CreateAccountUseCase
from infrastructure.driven_adapters.persistence.account_sqlalchemy_adapter import AccountSqlAlchemyAdapter
from infrastructure.entry_points.rest.dto.account_dto import CreateAccountRequest, AccountResponse
from infrastructure.helpers.correlation_id import get_correlation_id
```

### Naming Patterns

| Pattern | Structure | Example |
|---------|-----------|---------|
| Port | `{Concept}Gateway` | `AccountGateway`, `NotificationGateway` |
| Adapter | `{Concept}{Technology}Adapter` | `AccountSqlAlchemyAdapter`, `AccountDynamoAdapter` |
| Use case | `{Action}{Concept}UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` |
| Mapper | `{Concept}{Layer}Mapper` | `AccountEntityMapper`, `AccountRestMapper` |
| File | `{snake_case_of_class}.py` | `create_account_use_case.py` |

## Verification Checklist

- [ ] Classes use PascalCase
- [ ] Files use snake_case
- [ ] Folders use snake_case
- [ ] Ports are ABC classes ending in `*Gateway`
- [ ] No `I` prefix on interfaces
- [ ] DTOs are Pydantic `BaseModel` subclasses
- [ ] Domain entities are `@dataclass`, value objects are `@dataclass(frozen=True)`
- [ ] Each `__init__.py` exists in every package

## Tools and Resources

_(No additional information required for this section.)_
