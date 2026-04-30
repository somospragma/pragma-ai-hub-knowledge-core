<!-- keywords: solid, single responsibility, open closed, liskov, interface segregation, dependency inversion, python -->
# SOLID Principles — Python Implementation

## Purpose

Implementation guide for SOLID principles in Python, including functional examples and usage patterns.

## Libraries and dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
dependency-injector = "^4.41.0"
```

```txt
# requirements.txt
dependency-injector>=4.41.0
```

## Step by Step / Guidelines

### S - Single Responsibility Principle

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

# CORRECT: Service with single responsibility
class LoanService:
    def __init__(self, loan_repository: 'LoanRepository'):
        self._loan_repository = loan_repository
    
    def create_loan(self, request: 'LoanRequest') -> 'Loan':
        loan = Loan(
            amount=request.amount,
            customer_id=request.customer_id,
            status='PENDING'
        )
        return self._loan_repository.save(loan)

# Separate validation
class LoanValidator:
    def validate(self, request: 'LoanRequest') -> None:
        if request.amount <= 0:
            raise ValidationError('Amount must be positive')

# Separate notification
class LoanNotificationService:
    def __init__(self, email_service: 'EmailService'):
        self._email_service = email_service
    
    def notify_loan_created(self, loan: 'Loan') -> None:
        self._email_service.send(
            loan.customer_id,
            f'Loan created: {loan.id}'
        )
```

### O - Open/Closed Principle

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List

class NotificationType(Enum):
    EMAIL = 'email'
    SMS = 'sms'
    PUSH = 'push'

# Base interface
class NotificationSender(ABC):
    @abstractmethod
    def send(self, message: str, recipient: str) -> None:
        pass
    
    @abstractmethod
    def get_type(self) -> NotificationType:
        pass

# Extensible implementations
class EmailNotificationSender(NotificationSender):
    def send(self, message: str, recipient: str) -> None:
        # Email sending logic
        pass
    
    def get_type(self) -> NotificationType:
        return NotificationType.EMAIL

class SmsNotificationSender(NotificationSender):
    def send(self, message: str, recipient: str) -> None:
        # SMS sending logic
        pass
    
    def get_type(self) -> NotificationType:
        return NotificationType.SMS

# Service that uses the implementations
class NotificationService:
    def __init__(self, senders: List[NotificationSender]):
        self._senders: Dict[NotificationType, NotificationSender] = {
            sender.get_type(): sender for sender in senders
        }
    
    def send(self, notification_type: NotificationType, message: str, recipient: str) -> None:
        sender = self._senders.get(notification_type)
        if not sender:
            raise ValueError(f'No sender for type: {notification_type}')
        sender.send(message, recipient)
```

### L - Liskov Substitution Principle

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, Dict

T = TypeVar('T')
ID = TypeVar('ID')

# Repository interface
class Repository(ABC, Generic[T, ID]):
    @abstractmethod
    def find_by_id(self, id: ID) -> Optional[T]:
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        pass

# Interchangeable implementations
class PostgresUserRepository(Repository['User', str]):
    def find_by_id(self, id: str) -> Optional['User']:
        # PostgreSQL implementation
        pass
    
    def save(self, entity: 'User') -> 'User':
        # PostgreSQL implementation
        pass

class InMemoryUserRepository(Repository['User', str]):
    def __init__(self):
        self._store: Dict[str, 'User'] = {}
    
    def find_by_id(self, id: str) -> Optional['User']:
        return self._store.get(id)
    
    def save(self, entity: 'User') -> 'User':
        self._store[entity.id] = entity
        return entity
```

### I - Interface Segregation Principle

```python
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')
ID = TypeVar('ID')

# Segregated interfaces
class ReadRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def find_by_id(self, id: ID) -> Optional[T]:
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        pass

class WriteRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def save(self, entity: T) -> T:
        pass
    
    @abstractmethod
    def delete(self, id: ID) -> None:
        pass

class BulkRepository(ABC, Generic[T]):
    @abstractmethod
    def save_all(self, entities: List[T]) -> None:
        pass

# Implementation can choose which interfaces to implement
class UserRepository(ReadRepository['User', str], WriteRepository['User', str]):
    # Implements only basic read and write
    pass

# Cache only needs read
class CachedConfigRepository(ReadRepository['Config', str]):
    # Only implements read
    pass
```

### D - Dependency Inversion Principle

```python
from abc import ABC, abstractmethod
from typing import Optional, List

# Domain defines the abstraction
class LoanRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: str) -> Optional['Loan']:
        pass
    
    @abstractmethod
    def save(self, loan: 'Loan') -> 'Loan':
        pass
    
    @abstractmethod
    def find_by_customer_id(self, customer_id: str) -> List['Loan']:
        pass

# Domain service depends on abstraction
class LoanService:
    def __init__(self, loan_repository: LoanRepository):
        self._loan_repository = loan_repository
    
    def process_loan(self, loan_id: str) -> 'Loan':
        loan = self._loan_repository.find_by_id(loan_id)
        if not loan:
            raise LoanNotFoundError(loan_id)
        loan.status = 'PROCESSED'
        return self._loan_repository.save(loan)

# Infrastructure implements the abstraction
class PostgresLoanRepository(LoanRepository):
    def __init__(self, connection):
        self._connection = connection
    
    def find_by_id(self, id: str) -> Optional['Loan']:
        # PostgreSQL implementation
        pass
    
    def save(self, loan: 'Loan') -> 'Loan':
        # PostgreSQL implementation
        pass
```

### Dependency injection with dependency-injector

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Repositories
    loan_repository = providers.Singleton(
        PostgresLoanRepository,
        connection=config.database.connection
    )
    
    # Services
    loan_service = providers.Factory(
        LoanService,
        loan_repository=loan_repository
    )

# Usage
container = Container()
container.config.from_yaml('config.yml')

loan_service = container.loan_service()
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
