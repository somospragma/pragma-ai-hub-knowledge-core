<!-- keywords: solid, single responsibility, open closed, liskov, interface segregation, dependency inversion, typescript, nodejs -->
# SOLID Principles — TypeScript Implementation

## Purpose

Implementation guide for SOLID principles in TypeScript/Node.js, including functional examples and usage patterns.

## Libraries and dependencies

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

### S - Single Responsibility Principle

```typescript
// CORRECT: Service with single responsibility
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

// Separate validation
class LoanValidator {
  validate(request: LoanRequest): void {
    if (request.amount <= 0) {
      throw new ValidationError('Amount must be positive');
    }
  }
}

// Separate notification
class LoanNotificationService {
  constructor(private readonly emailService: EmailService) {}

  async notifyLoanCreated(loan: Loan): Promise<void> {
    await this.emailService.send(
      loan.customerId,
      `Loan created: ${loan.id}`
    );
  }
}
```

### O - Open/Closed Principle

```typescript
// Base interface
interface NotificationSender {
  send(message: string, recipient: string): Promise<void>;
  getType(): NotificationType;
}

// Extensible implementations
class EmailNotificationSender implements NotificationSender {
  async send(message: string, recipient: string): Promise<void> {
    // Email sending logic
  }

  getType(): NotificationType {
    return NotificationType.EMAIL;
  }
}

class SmsNotificationSender implements NotificationSender {
  async send(message: string, recipient: string): Promise<void> {
    // SMS sending logic
  }

  getType(): NotificationType {
    return NotificationType.SMS;
  }
}

// Service that uses the implementations
class NotificationService {
  private senders: Map<NotificationType, NotificationSender>;

  constructor(senderList: NotificationSender[]) {
    this.senders = new Map(
      senderList.map(sender => [sender.getType(), sender])
    );
  }

  async send(type: NotificationType, message: string, recipient: string): Promise<void> {
    const sender = this.senders.get(type);
    if (!sender) {
      throw new Error(`No sender for type: ${type}`);
    }
    await sender.send(message, recipient);
  }
}
```

### L - Liskov Substitution Principle

```typescript
// Repository interface
interface Repository<T, ID> {
  findById(id: ID): Promise<T | null>;
  save(entity: T): Promise<T>;
}

// Interchangeable implementations
class PostgresUserRepository implements Repository<User, string> {
  async findById(id: string): Promise<User | null> {
    // PostgreSQL implementation
  }

  async save(entity: User): Promise<User> {
    // PostgreSQL implementation
  }
}

class InMemoryUserRepository implements Repository<User, string> {
  private store = new Map<string, User>();

  async findById(id: string): Promise<User | null> {
    return this.store.get(id) ?? null;
  }

  async save(entity: User): Promise<User> {
    this.store.set(entity.id, entity);
    return entity;
  }
}
```

### I - Interface Segregation Principle

```typescript
// Segregated interfaces
interface ReadRepository<T, ID> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
}

interface WriteRepository<T, ID> {
  save(entity: T): Promise<T>;
  delete(id: ID): Promise<void>;
}

interface BulkRepository<T> {
  saveAll(entities: T[]): Promise<void>;
}

// Implementation can choose which interfaces to implement
class UserRepository implements ReadRepository<User, string>, WriteRepository<User, string> {
  // Implements only basic read and write
}

// Cache only needs read
class CachedConfigRepository implements ReadRepository<Config, string> {
  // Only implements read
}
```

### D - Dependency Inversion Principle

```typescript
// Domain defines the abstraction
interface LoanRepository {
  findById(id: string): Promise<Loan | null>;
  save(loan: Loan): Promise<Loan>;
  findByCustomerId(customerId: string): Promise<Loan[]>;
}

// Domain service depends on abstraction
class LoanService {
  constructor(private readonly loanRepository: LoanRepository) {}

  async processLoan(loanId: string): Promise<Loan> {
    const loan = await this.loanRepository.findById(loanId);
    if (!loan) {
      throw new LoanNotFoundError(loanId);
    }
    loan.status = 'PROCESSED';
    return this.loanRepository.save(loan);
  }
}

// Infrastructure implements the abstraction
class PostgresLoanRepository implements LoanRepository {
  constructor(private readonly pool: Pool) {}

  async findById(id: string): Promise<Loan | null> {
    const result = await this.pool.query(
      'SELECT * FROM loans WHERE id = $1',
      [id]
    );
    return result.rows[0] ?? null;
  }

  async save(loan: Loan): Promise<Loan> {
    // PostgreSQL implementation
  }
}
```

### Dependency injection with Inversify

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

// Container configuration
const container = new Container();
container.bind<LoanRepository>(TYPES.LoanRepository).to(PostgresLoanRepository);
container.bind<LoanService>(TYPES.LoanService).to(LoanService);
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
