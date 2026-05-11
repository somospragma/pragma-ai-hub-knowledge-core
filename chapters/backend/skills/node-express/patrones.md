---
id: backend-skill-node-express-patrones
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Patrones de Diseño y Convenciones — Node Express

## Propósito

Definir las convenciones de naming, principios SOLID aplicados, validación de inputs con Zod, mapeo DTO↔Entity, y patrones de diseño estándar para microservicios Node.js con Express y TypeScript.

---

## 1. Convenciones de Naming

### Clases e Interfaces (PascalCase) y Archivos (PascalCase)

| Componente | Sufijo | Nombre Clase/Interface | Nombre Archivo |
|-----------|--------|----------------------|----------------|
| Entidad de dominio | _(ninguno)_ | `Account` | `Account.ts` |
| Value object | _(ninguno)_ | `Money` | `Money.ts` |
| Enum de dominio | _(ninguno)_ | `OrderStatus` | `OrderStatus.ts` |
| Puerto de salida (interface) | `*Gateway` | `AccountGateway` | `AccountGateway.ts` |
| Caso de uso | `*UseCase` | `CreateAccountUseCase` | `CreateAccountUseCase.ts` |
| Servicio de dominio | `*Service` | `PricingService` | `PricingService.ts` |
| Driven adapter | `*Adapter` | `AccountDynamoAdapter` | `AccountDynamoAdapter.ts` |
| Entidad framework (DynamoDB) | `*Item` | `AccountItem` | `AccountItem.ts` |
| Entidad framework (Mongo) | `*Document` | `AccountDocument` | `AccountDocument.ts` |
| Mapper de persistencia | `*EntityMapper` | `AccountEntityMapper` | `AccountEntityMapper.ts` |
| Mapper REST | `*RestMapper` | `AccountRestMapper` | `AccountRestMapper.ts` |
| DTO request | `*Request` | `CreateAccountRequest` | `CreateAccountRequest.ts` |
| DTO response | `*Response` | `AccountResponse` | `AccountResponse.ts` |
| Excepción de dominio | `*Error` | `AccountNotFoundError` | `AccountNotFoundError.ts` |

### Reglas específicas de TypeScript

- Las interfaces NO usan prefijo `I` (usar `AccountGateway`, no `IAccountGateway`)
- Usar `interface` para puertos, `class` para implementaciones
- Usar `type` para DTOs simples, `class` con decoradores `class-validator` para DTOs validados
- Preferir propiedades `readonly` en entidades de dominio
- Usar `enum` para enumeraciones de dominio

### Módulos/Carpetas (snake_case)

| Tipo de módulo | Patrón | Ejemplo |
|---------------|--------|---------|
| Driven adapter (REST) | `rest_api_{sistema}` | `rest_api_t24` |
| Driven adapter (DB) | `dynamodb`, `mongodb` | `dynamodb` |
| Entry point | `routes` | `routes` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app_service` | `app_service` |

### Patrones de Naming

| Patrón | Estructura | Ejemplo |
|--------|-----------|---------|
| Puerto | `{Concepto}Gateway` | `AccountGateway`, `NotificationGateway` |
| Adapter | `{Concepto}{Tecnología}Adapter` | `AccountDynamoAdapter`, `AccountRedisAdapter` |
| Caso de uso | `{Acción}{Concepto}UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` |
| Mapper | `{Concepto}{Capa}Mapper` | `AccountEntityMapper`, `AccountRestMapper` |
| Error | `{Concepto}{Razón}Error` | `AccountNotFoundError`, `InsufficientFundsError` |

---

## 2. Principios SOLID en TypeScript

### Dependencias

```json
{
  "dependencies": {
    "inversify": "^6.0.2",
    "reflect-metadata": "^0.1.13"
  },
  "devDependencies": {
    "typescript": "^5.2.2"
  }
}
```

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

### S — Single Responsibility Principle

```typescript
// CORRECTO: Servicio con responsabilidad única
class LoanService {
  constructor(private readonly loanRepository: LoanRepository) {}

  async createLoan(request: LoanRequest): Promise<Loan> {
    const loan: Loan = {
      id: generateId(),
      amount: request.amount,
      customerId: request.customerId,
      status: 'PENDING'
    };
    return this.loanRepository.save(loan);
  }
}

// Validación separada
class LoanValidator {
  validate(request: LoanRequest): void {
    if (request.amount <= 0) {
      throw new ValidationError('Amount must be positive');
    }
  }
}

// Notificación separada
class LoanNotificationService {
  constructor(private readonly emailService: EmailService) {}

  async notifyLoanCreated(loan: Loan): Promise<void> {
    await this.emailService.send(loan.customerId, `Loan created: ${loan.id}`);
  }
}
```

### O — Open/Closed Principle

```typescript
interface NotificationSender {
  send(message: string, recipient: string): Promise<void>;
  getType(): NotificationType;
}

class EmailNotificationSender implements NotificationSender {
  async send(message: string, recipient: string): Promise<void> { /* ... */ }
  getType(): NotificationType { return NotificationType.EMAIL; }
}

class SmsNotificationSender implements NotificationSender {
  async send(message: string, recipient: string): Promise<void> { /* ... */ }
  getType(): NotificationType { return NotificationType.SMS; }
}

// Servicio extensible sin modificar
class NotificationService {
  private senders: Map<NotificationType, NotificationSender>;

  constructor(senderList: NotificationSender[]) {
    this.senders = new Map(senderList.map(s => [s.getType(), s]));
  }

  async send(type: NotificationType, message: string, recipient: string): Promise<void> {
    const sender = this.senders.get(type);
    if (!sender) throw new Error(`No sender for type: ${type}`);
    await sender.send(message, recipient);
  }
}
```

### I — Interface Segregation Principle

```typescript
interface ReadRepository<T, ID> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
}

interface WriteRepository<T, ID> {
  save(entity: T): Promise<T>;
  delete(id: ID): Promise<void>;
}

// Implementación elige qué interfaces implementar
class UserRepository implements ReadRepository<User, string>, WriteRepository<User, string> {
  // Implementa lectura y escritura
}

class CachedConfigRepository implements ReadRepository<Config, string> {
  // Solo implementa lectura
}
```

### D — Dependency Inversion Principle

```typescript
// El dominio define la abstracción
interface LoanRepository {
  findById(id: string): Promise<Loan | null>;
  save(loan: Loan): Promise<Loan>;
}

// Servicio de dominio depende de abstracción
class LoanService {
  constructor(private readonly loanRepository: LoanRepository) {}

  async processLoan(loanId: string): Promise<Loan> {
    const loan = await this.loanRepository.findById(loanId);
    if (!loan) throw new LoanNotFoundError(loanId);
    loan.status = 'PROCESSED';
    return this.loanRepository.save(loan);
  }
}

// Infraestructura implementa la abstracción
class PostgresLoanRepository implements LoanRepository {
  constructor(private readonly pool: Pool) {}
  async findById(id: string): Promise<Loan | null> { /* ... */ }
  async save(loan: Loan): Promise<Loan> { /* ... */ }
}
```

### Inyección de dependencias con Inversify

```typescript
import { Container, injectable, inject } from 'inversify';

const TYPES = {
  LoanRepository: Symbol.for('LoanRepository'),
  LoanService: Symbol.for('LoanService')
};

@injectable()
class LoanService {
  constructor(
    @inject(TYPES.LoanRepository) private loanRepository: LoanRepository
  ) {}
}

const container = new Container();
container.bind<LoanRepository>(TYPES.LoanRepository).to(PostgresLoanRepository);
container.bind<LoanService>(TYPES.LoanService).to(LoanService);
```

---

## 3. Validación de Inputs con Zod

### Dependencias

```json
{
  "dependencies": {
    "zod": "^3.22.4"
  }
}
```

### Schemas de validación

```typescript
import { z } from 'zod';

export const OrderItemSchema = z.object({
  productId: z.string().min(1).max(50).regex(/^[a-zA-Z0-9-]+$/),
  quantity: z.number().int().min(1).max(1000),
  unitPrice: z.number().positive().max(999999.99)
    .transform(val => Math.round(val * 100) / 100)
});

export const OrderRequestSchema = z.object({
  customerId: z.string().min(1).max(50).regex(/^[a-zA-Z0-9-]+$/),
  items: z.array(OrderItemSchema).min(1).max(100),
  currency: z.string().regex(/^[A-Z]{3}$/),
  notificationEmail: z.string().email().optional(),
  deliveryDate: z.string().datetime()
    .refine(date => new Date(date) > new Date(), {
      message: 'Delivery date must be in the future'
    }).optional()
});

export type OrderRequest = z.infer<typeof OrderRequestSchema>;
```

### Middleware de validación para Express

```typescript
import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';

export function validate<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const errors = error.errors.map(e => ({
          field: e.path.join('.'),
          message: e.message
        }));
        res.status(400).json({
          type: 'https://api.company.com/errors/validation-error',
          title: 'Validation Error',
          status: 400,
          detail: 'Request validation failed',
          errors
        });
      } else {
        next(error);
      }
    }
  };
}

// Uso en router
router.post('/orders', validate(OrderRequestSchema), orderController.create);
```

---

## 4. Mapeo DTO ↔ Entity

### Mapper como clase pura

```typescript
export class AccountEntityMapper {
  static toEntity(item: AccountItem): Account {
    return { id: item.pk, name: item.name, email: item.email };
  }

  static toItem(entity: Account): AccountItem {
    return {
      pk: entity.id,
      sk: `ACCOUNT#${entity.id}`,
      name: entity.name,
      email: entity.email
    };
  }
}
```

### Mapper con class-transformer

```typescript
import { plainToInstance } from 'class-transformer';
import { Expose, Transform, Type, Exclude } from 'class-transformer';

export class OrderResponse {
  @Expose() id: string;
  @Expose() customerId: string;
  @Expose() @Transform(({ value }) => Number(value.toFixed(2))) totalAmount: number;
  @Expose() status: string;
  @Expose() @Transform(({ value }) => value.toISOString()) createdDate: string;
  @Exclude() internalNotes: string;
}

class OrderMapper {
  toEntity(request: OrderRequest): Partial<Order> {
    const items = request.items.map(item => ({
      productId: item.productId,
      quantity: item.quantity,
      unitPrice: item.unitPrice
    }));
    const totalAmount = items.reduce((sum, i) => sum + i.unitPrice * i.quantity, 0);
    return { customerId: request.customerId, items: items as OrderItem[], totalAmount, status: 'PENDING', createdAt: new Date() };
  }

  toResponse(entity: Order): OrderResponse {
    return plainToInstance(OrderResponse, entity, { excludeExtraneousValues: true });
  }
}
```

---

## Checklist de Verificación

- [ ] Clases e interfaces usan PascalCase
- [ ] Archivos usan PascalCase (coinciden con el nombre de la clase)
- [ ] Carpetas usan snake_case
- [ ] Puertos son `interface` terminando en `*Gateway`
- [ ] Sin prefijo `I` en interfaces
- [ ] Adapters son `class` terminando en `*Adapter`
- [ ] Casos de uso terminan en `*UseCase`
- [ ] Errores terminan en `*Error` (no `*Exception`)
- [ ] Validación con Zod en middleware
- [ ] Mappers son funciones puras o clases estáticas
