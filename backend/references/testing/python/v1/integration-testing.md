<!-- keywords: integration testing, testcontainers, localstack, fastapi testclient, python -->
# Integration Testing — Python Implementation

## Purpose

Implementation guide for integration tests in Python using Testcontainers, LocalStack, and FastAPI TestClient.

## Libraries and dependencies

```toml
# pyproject.toml
[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.1"
testcontainers = "^3.7.1"
httpx = "^0.25.0"
boto3 = "^1.28.0"
```

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.1
testcontainers[postgres,localstack]>=3.7.1
httpx>=0.25.0
boto3>=1.28.0
```

## Configuration

### conftest.py

```python
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.localstack import LocalStackContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="module")
def db_engine(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    return engine

@pytest.fixture(scope="module")
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture(scope="module")
def localstack_container():
    with LocalStackContainer(image="localstack/localstack:3.0") as localstack:
        yield localstack
```

## Step by Step / Guidelines

### Test with PostgreSQL Testcontainer

```python
import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from order_repository import OrderRepository
from models import Order, Base

@pytest.fixture(scope="module")
def postgres_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="module")
def db_session(postgres_container):
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def repository(db_session):
    return OrderRepository(db_session)

def test_save_and_retrieve_order(repository, db_session):
    order = Order(
        customer_id="cust-123",
        status="PENDING",
        total_amount=100.00
    )
    
    saved = repository.save(order)
    db_session.commit()
    
    found = repository.find_by_id(saved.id)
    
    assert found is not None
    assert found.customer_id == "cust-123"
```

### Test with LocalStack (SQS)

```python
import pytest
import json
import boto3
from testcontainers.localstack import LocalStackContainer

@pytest.fixture(scope="module")
def localstack():
    with LocalStackContainer(image="localstack/localstack:3.0") as localstack:
        yield localstack

@pytest.fixture
def sqs_client(localstack):
    return boto3.client(
        'sqs',
        endpoint_url=localstack.get_url(),
        region_name='us-east-1',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

@pytest.fixture
def queue_url(sqs_client):
    response = sqs_client.create_queue(QueueName='order-events')
    return response['QueueUrl']

def test_send_and_receive_message(sqs_client, queue_url):
    event = {'orderId': 'ord-123', 'type': 'CREATED'}
    
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(event)
    )
    
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5
    )
    
    assert len(response.get('Messages', [])) == 1
    assert json.loads(response['Messages'][0]['Body']) == event
```

### API Integration Test with FastAPI

```python
import pytest
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer
from main import app
import os

@pytest.fixture(scope="module")
def postgres():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="module")
def client(postgres):
    os.environ['DATABASE_URL'] = postgres.get_connection_url()
    with TestClient(app) as client:
        yield client

def test_create_order(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "customer_id": "cust-123",
            "items": [{"product_id": "prod-1", "quantity": 2, "unit_price": 25.00}],
            "currency": "USD"
        }
    )
    
    assert response.status_code == 201
    assert response.json()["customer_id"] == "cust-123"
    assert response.json()["total_amount"] == 50.00

def test_validation_error(client):
    response = client.post(
        "/api/v1/orders",
        json={"customer_id": "", "items": []}
    )
    
    assert response.status_code == 400
    assert response.json()["title"] == "Validation Error"
```

### Async test with httpx

```python
import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_async_create_order():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/orders",
            json={
                "customer_id": "cust-123",
                "items": [{"product_id": "prod-1", "quantity": 2, "unit_price": 25.00}],
                "currency": "USD"
            }
        )
    
    assert response.status_code == 201
    assert response.json()["customer_id"] == "cust-123"
```

## Mocks and fixtures

### Fixture Factory

```python
class OrderFixtures:
    @staticmethod
    def valid_order_request():
        return {
            "customer_id": "cust-123",
            "items": [
                {"product_id": "prod-1", "quantity": 2, "unit_price": 25.00}
            ],
            "currency": "USD"
        }
    
    @staticmethod
    def order_entity():
        return Order(
            customer_id="cust-123",
            status="PENDING",
            total_amount=50.00
        )
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
