<!-- keywords: kafka, msk, event streaming, aiokafka, kafka-python, consumer, producer, python -->
# Apache Kafka / Amazon MSK Integration - Python

## Purpose

Implement integration with Apache Kafka and Amazon MSK in Python projects using aiokafka and kafka-python.

## Scope of Application

- Python projects that require Kafka producers and consumers
- Applications connecting to MSK
- Synchronous implementation with kafka-python or asynchronous with aiokafka

## Main Content

### Dependencies

```txt
# requirements.txt - Asynchronous
aiokafka>=0.8.0

# requirements.txt - Synchronous
kafka-python>=2.0.0
```

```bash
pip install aiokafka
pip install kafka-python
```

### Async Client

```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
from typing import List, Callable, Awaitable
from dataclasses import dataclass, asdict


@dataclass
class DomainEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    payload: dict


class AsyncKafkaClient:
    """Asynchronous client for Kafka using aiokafka"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer = None
        self.consumer: AIOKafkaConsumer = None
    
    async def start_producer(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            enable_idempotence=True
        )
        await self.producer.start()
    
    async def start_consumer(self, group_id: str, topics: List[str]):
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False
        )
        await self.consumer.start()

    async def send(self, topic: str, event: DomainEvent) -> None:
        await self.producer.send_and_wait(
            topic,
            key=event.aggregate_id,
            value=asdict(event),
            headers=[
                ('event-type', event.event_type.encode('utf-8'))
            ]
        )
    
    async def send_batch(self, topic: str, events: List[DomainEvent]) -> None:
        batch = self.producer.create_batch()
        
        for event in events:
            metadata = batch.append(
                key=event.aggregate_id.encode('utf-8'),
                value=json.dumps(asdict(event)).encode('utf-8'),
                timestamp=None
            )
            if metadata is None:
                await self.producer.send_batch(batch, topic)
                batch = self.producer.create_batch()
                batch.append(
                    key=event.aggregate_id.encode('utf-8'),
                    value=json.dumps(asdict(event)).encode('utf-8'),
                    timestamp=None
                )
        
        if batch.record_count() > 0:
            await self.producer.send_batch(batch, topic)
    
    async def consume(
        self, 
        handler: Callable[[DomainEvent], Awaitable[None]]
    ) -> None:
        async for message in self.consumer:
            try:
                event = DomainEvent(**message.value)
                await handler(event)
                await self.consumer.commit()
            except Exception as e:
                print(f"Error processing message: {e}")
    
    async def stop(self):
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()
```

### Synchronous Client

```python
from kafka import KafkaProducer, KafkaConsumer


class SyncKafkaClient:
    """Synchronous client for Kafka"""
    
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
    
    def create_producer(self) -> KafkaProducer:
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all'
        )
    
    def create_consumer(self, group_id: str, topics: List[str]) -> KafkaConsumer:
        return KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='earliest'
        )
```

### Error handling

```python
import time


async def send_with_retry(
    client: AsyncKafkaClient,
    topic: str,
    event: DomainEvent,
    max_retries: int = 3
) -> None:
    last_error = None
    
    for attempt in range(max_retries):
        try:
            await client.send(topic, event)
            return
        except Exception as e:
            last_error = e
            delay = (2 ** attempt) * 0.1
            await asyncio.sleep(delay)
    
    raise last_error
```

## Important Rules

- Use `acks='all'` for durability
- Enable `enable_idempotence=True` for exactly-once
- Implement manual commits for fine-grained control
- Close connections properly with `stop()`
- Use `aiokafka` for high throughput

## Example

```python
import asyncio
import os
import uuid


async def main():
    client = AsyncKafkaClient(os.environ['KAFKA_BROKERS'])
    await client.start_producer()
    
    event = DomainEvent(
        event_id=str(uuid.uuid4()),
        event_type='ORDER_CREATED',
        aggregate_id='order-123',
        payload={'customerId': 'cust-456', 'amount': 100}
    )
    
    await client.send('orders-topic', event)
    await client.stop()


if __name__ == '__main__':
    asyncio.run(main())
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
