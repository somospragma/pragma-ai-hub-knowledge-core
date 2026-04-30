<!-- keywords: dto, entity, mapping, class-transformer, data transformation, typescript -->
# DTO-Entity Mapping — TypeScript Implementation

## Purpose

Implementation guide for DTO-Entity mapping in TypeScript using class-transformer, with functional examples.

## Libraries and dependencies

```json
{
  "dependencies": {
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.0",
    "reflect-metadata": "^0.1.13"
  }
}
```

## Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "strict": true
  }
}
```

## Step by Step / Guidelines

### Entities and DTOs

```typescript
// entities.ts
import { Expose, Transform, Type, Exclude } from 'class-transformer';

export class OrderItem {
  id: string;
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
}

export class Order {
  id: string;
  customerId: string;
  
  @Type(() => OrderItem)
  items: OrderItem[];
  
  totalAmount: number;
  status: string;
  createdAt: Date;
}
```

### DTOs with decorators

```typescript
// dtos.ts
import { Expose, Transform, Type, Exclude } from 'class-transformer';
import { IsNotEmpty, IsArray, ValidateNested, Min, IsPositive } from 'class-validator';

export class OrderItemRequest {
  @IsNotEmpty()
  productId: string;
  
  @Min(1)
  quantity: number;
  
  @IsPositive()
  unitPrice: number;
}

export class OrderRequest {
  @IsNotEmpty()
  customerId: string;
  
  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderItemRequest)
  items: OrderItemRequest[];
  
  currency: string;
}

export class OrderItemResponse {
  @Expose()
  productId: string;
  
  @Expose()
  productName: string;
  
  @Expose()
  quantity: number;
  
  @Expose()
  @Transform(({ value }) => Number(value.toFixed(2)))
  unitPrice: number;
}

export class OrderResponse {
  @Expose()
  id: string;
  
  @Expose()
  customerId: string;
  
  @Expose()
  @Type(() => OrderItemResponse)
  items: OrderItemResponse[];
  
  @Expose()
  @Transform(({ value }) => Number(value.toFixed(2)))
  totalAmount: number;
  
  @Expose()
  status: string;
  
  @Expose()
  @Transform(({ value }) => value.toISOString())
  createdDate: string;
  
  @Exclude()
  internalNotes: string;
}
```

### Mapper class

```typescript
// mapper.ts
import { plainToInstance, instanceToPlain } from 'class-transformer';

class OrderMapper {
  toEntity(request: OrderRequest): Partial<Order> {
    const items = request.items.map(item => ({
      productId: item.productId,
      quantity: item.quantity,
      unitPrice: item.unitPrice
    }));
    
    const totalAmount = items.reduce(
      (sum, item) => sum + item.unitPrice * item.quantity,
      0
    );
    
    return {
      customerId: request.customerId,
      items: items as OrderItem[],
      totalAmount,
      status: 'PENDING',
      createdAt: new Date()
    };
  }
  
  toResponse(entity: Order): OrderResponse {
    return plainToInstance(OrderResponse, entity, {
      excludeExtraneousValues: true
    });
  }
  
  toResponseList(entities: Order[]): OrderResponse[] {
    return entities.map(entity => this.toResponse(entity));
  }
  
  updateEntity(entity: Order, request: Partial<OrderRequest>): Order {
    if (request.customerId) {
      entity.customerId = request.customerId;
    }
    if (request.items) {
      entity.items = request.items.map(item => ({
        ...item,
        id: '',
        productName: ''
      }));
      entity.totalAmount = entity.items.reduce(
        (sum, item) => sum + item.unitPrice * item.quantity,
        0
      );
    }
    return entity;
  }
}

export const orderMapper = new OrderMapper();
```

### Usage in Service

```typescript
// order.service.ts
class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly orderMapper: OrderMapper
  ) {}

  async createOrder(request: OrderRequest): Promise<OrderResponse> {
    const entity = this.orderMapper.toEntity(request);
    const saved = await this.orderRepository.save(entity as Order);
    return this.orderMapper.toResponse(saved);
  }

  async updateOrder(id: string, request: Partial<OrderRequest>): Promise<OrderResponse> {
    const entity = await this.orderRepository.findById(id);
    if (!entity) {
      throw new OrderNotFoundError(id);
    }
    const updated = this.orderMapper.updateEntity(entity, request);
    const saved = await this.orderRepository.save(updated);
    return this.orderMapper.toResponse(saved);
  }
}
```

### Validation with class-validator

```typescript
// validation.middleware.ts
import { validate } from 'class-validator';
import { plainToInstance } from 'class-transformer';

async function validateDto<T extends object>(
  dtoClass: new () => T,
  body: unknown
): Promise<T> {
  const dto = plainToInstance(dtoClass, body);
  const errors = await validate(dto);
  
  if (errors.length > 0) {
    const messages = errors.map(e => Object.values(e.constraints || {}).join(', '));
    throw new ValidationError(messages);
  }
  
  return dto;
}
```

## Mocks and fixtures

### Mapper test

```typescript
describe('OrderMapper', () => {
  const mapper = new OrderMapper();

  it('should map request to entity', () => {
    const request: OrderRequest = {
      customerId: 'cust-123',
      items: [{ productId: 'prod-1', quantity: 2, unitPrice: 25.00 }],
      currency: 'USD'
    };

    const entity = mapper.toEntity(request);

    expect(entity.status).toBe('PENDING');
    expect(entity.totalAmount).toBe(50.00);
    expect(entity.createdAt).toBeDefined();
  });
});
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
