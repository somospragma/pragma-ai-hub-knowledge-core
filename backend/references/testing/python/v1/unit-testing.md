<!-- keywords: unit testing, pytest, test patterns, mocking, fixtures, python -->
# Unit Testing — Python Implementation

## Purpose

Implementation guide for unit tests in Python using pytest, with functional examples and project configuration.

## Libraries and dependencies

```toml
# pyproject.toml
[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.1"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["**/dto.py", "**/config.py", "**/__init__.py"]

[tool.coverage.report]
fail_under = 80
```

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-asyncio>=0.21.1
pytest-mock>=3.11.1
```

## Configuration

### conftest.py

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
def mock_repository():
    return Mock()

@pytest.fixture
def mock_notification():
    return Mock()

@pytest.fixture
def customer_service(mock_repository, mock_notification):
    return CustomerService(mock_repository, mock_notification)

@pytest.fixture
def async_repository():
    return AsyncMock()
```

## Step by Step / Guidelines

### Basic test with mocks

```python
# test_customer_service.py
import pytest
from unittest.mock import Mock, patch, call
from customer_service import CustomerService, CustomerNotFoundError

class TestCustomerService:
    
    def test_create_customer_successfully(self, customer_service, mock_repository, mock_notification):
        # Arrange
        request = {"name": "John Doe", "email": "john@example.com"}
        saved_customer = {
            "id": "cust-123",
            "name": "John Doe",
            "email": "john@example.com",
            "status": "ACTIVE"
        }
        mock_repository.save.return_value = saved_customer
        
        # Act
        result = customer_service.create(request)
        
        # Assert
        assert result == saved_customer
        mock_repository.save.assert_called_once()
        call_args = mock_repository.save.call_args[0][0]
        assert call_args["name"] == "John Doe"
        assert call_args["email"] == "john@example.com"
        mock_notification.send_welcome_email.assert_called_once_with("john@example.com")
    
    def test_create_customer_raises_on_empty_name(self, customer_service, mock_repository):
        request = {"name": "", "email": "john@example.com"}
        
        with pytest.raises(ValueError, match="Name is required"):
            customer_service.create(request)
        
        mock_repository.save.assert_not_called()
    
    def test_find_by_id_returns_customer(self, customer_service, mock_repository):
        customer = {"id": "cust-123", "name": "John Doe"}
        mock_repository.find_by_id.return_value = customer
        
        result = customer_service.find_by_id("cust-123")
        
        assert result == customer
        mock_repository.find_by_id.assert_called_once_with("cust-123")
    
    def test_find_by_id_raises_when_not_found(self, customer_service, mock_repository):
        mock_repository.find_by_id.return_value = None
        
        with pytest.raises(CustomerNotFoundError):
            customer_service.find_by_id("non-existent")
```

### Parameterized tests

```python
class TestValidationService:
    
    @pytest.mark.parametrize("email,is_valid", [
        ("john@example.com", True),
        ("invalid-email", False),
        ("", False),
        ("test@domain.co.uk", True),
    ])
    def test_validate_email(self, customer_service, email, is_valid):
        if is_valid:
            customer_service.validate_email(email)  # No exception
        else:
            with pytest.raises(ValueError):
                customer_service.validate_email(email)
    
    @pytest.mark.parametrize("name", ["", " ", "   ", None])
    def test_reject_blank_names(self, customer_service, name):
        request = {"name": name, "email": "test@example.com"}
        
        with pytest.raises(ValueError, match="Name is required"):
            customer_service.create(request)
```

### Async test

```python
import pytest
from unittest.mock import AsyncMock

class TestAsyncCustomerService:
    
    @pytest.mark.asyncio
    async def test_find_by_id_async(self, async_customer_service, async_repository):
        customer = {"id": "cust-123", "name": "John Doe"}
        async_repository.find_by_id.return_value = customer
        
        result = await async_customer_service.find_by_id("cust-123")
        
        assert result == customer
        async_repository.find_by_id.assert_awaited_once_with("cust-123")
    
    @pytest.mark.asyncio
    async def test_create_customer_async(self, async_customer_service, async_repository):
        request = {"name": "John Doe", "email": "john@example.com"}
        saved = {"id": "cust-123", **request, "status": "ACTIVE"}
        async_repository.save.return_value = saved
        
        result = await async_customer_service.create(request)
        
        assert result["id"] == "cust-123"
        assert result["status"] == "ACTIVE"
```

### Test with module patching

```python
from unittest.mock import patch
from datetime import datetime

class TestTimeBasedService:
    
    @patch('service.datetime')
    def test_uses_current_time(self, mock_datetime):
        fixed_time = datetime(2024, 1, 15, 10, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        service = TimeBasedService()
        record = service.create_record("test")
        
        assert record.created_at == fixed_time
```

## Code examples

### Reusable fixtures

```python
# conftest.py or fixtures.py
import pytest
from datetime import datetime

class CustomerFixtures:
    
    @staticmethod
    def valid_customer():
        return {
            "id": "cust-123",
            "name": "John Doe",
            "email": "john@example.com",
            "status": "ACTIVE",
            "created_at": datetime.now()
        }
    
    @staticmethod
    def valid_request():
        return {
            "name": "John Doe",
            "email": "john@example.com"
        }
    
    @staticmethod
    def customer_list(count: int):
        return [
            {
                "id": f"cust-{i}",
                "name": f"Customer {i}",
                "email": f"customer{i}@example.com",
                "status": "ACTIVE"
            }
            for i in range(count)
        ]

@pytest.fixture
def valid_customer():
    return CustomerFixtures.valid_customer()

@pytest.fixture
def valid_request():
    return CustomerFixtures.valid_request()
```

## Mocks and fixtures

### Exception mocking

```python
def test_handles_database_error(self, customer_service, mock_repository):
    mock_repository.save.side_effect = DatabaseError("Connection failed")
    
    with pytest.raises(ServiceError, match="Unable to save customer"):
        customer_service.create({"name": "John", "email": "john@test.com"})

def test_retries_on_transient_error(self, customer_service, mock_repository):
    mock_repository.save.side_effect = [
        TransientError("Temporary failure"),
        {"id": "cust-123", "name": "John"}
    ]
    
    result = customer_service.create_with_retry({"name": "John", "email": "john@test.com"})
    
    assert result["id"] == "cust-123"
    assert mock_repository.save.call_count == 2
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
