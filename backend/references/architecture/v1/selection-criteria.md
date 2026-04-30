<!-- keywords: architecture selection, decision matrix, hexagonal, onion, simple, project complexity, architectural pattern -->
# Architecture Selection Criteria

## Purpose

Provide a clear decision matrix for choosing the most appropriate architectural pattern (hexagonal, onion, simple) based on project complexity, team size, business requirements, and technical constraints.

## Scope of Application

- When starting a new project or microservice
- When evaluating the migration of an existing system
- During architecture reviews to validate decisions
- When training teams on when to apply each pattern

## Main Content

### Decision Matrix

| Criterion | Simple Architecture | Onion Architecture | Hexagonal Architecture |
|----------|--------------------|--------------------|------------------------|
| Domain complexity | Low | Medium-High | High |
| Business rules | Minimal/CRUD | Moderate | Complex |
| External integrations | 1-2 | 2-4 | 4+ |
| Team size | 1-2 devs | 2-4 devs | 4+ devs |
| Expected lifespan | < 1 year | 1-3 years | > 3 years |
| Testing needs | Basic | Moderate | Exhaustive |
| Infrastructure change | Unlikely | Possible | Likely |

### Simple Architecture

**Characteristics:**
- Basic layered structure: Controller → Service → Repository
- No additional port/adapter abstractions
- Direct dependencies on frameworks and infrastructure

**Indicators for choosing:**
- CRUD services without complex business logic
- Prototypes or MVPs
- Lambdas with a single responsibility
- Simple point-to-point integrations
- Small teams with high turnover

```
src/
├── controllers/
├── services/
├── repositories/
├── models/
└── config/
```

### Onion Architecture

**Characteristics:**
- Concentric layers with dependencies flowing inward
- Domain at the core, infrastructure on the outside
- Dependency inversion between layers

**Indicators for choosing:**
- Moderate domain logic
- Need to separate domain from infrastructure
- Multiple data sources
- Isolated domain testing required

```
src/
├── domain/
│   ├── entities/
│   └── services/
├── application/
│   ├── usecases/
│   └── ports/
├── infrastructure/
│   ├── persistence/
│   └── external/
└── presentation/
    └── controllers/
```

### Hexagonal Architecture

**Characteristics:**
- Explicit ports and adapters
- Fully isolated domain
- Multiple adapters per port
- Maximum testability and flexibility

**Indicators for choosing:**
- Complex domain with multiple bounded contexts
- Multiple input channels (REST, events, CLI)
- Multiple infrastructure providers
- Strict compliance requirements
- Large teams with distributed ownership

```
project/
├── domain/
│   ├── model/              ← Pure entities, value objects
│   ├── ports/              ← *Gateway interfaces (contracts with the outside)
│   └── usecases/           ← Business logic
├── infrastructure/
│   ├── driven-adapters/    ← Output adapters (*Adapter)
│   │   ├── persistence/
│   │   └── rest-consumer/
│   └── entry-points/       ← Input adapters
│       └── rest/
└── application/
    └── app-service/        ← Assembly and configuration
```

### Decision Tree

```
Does the service have complex business logic?
├── NO → Does it have multiple external integrations?
│        ├── NO → Simple Architecture
│        └── YES → Onion Architecture
└── YES → Does it require multiple adapters per port?
         ├── NO → Onion Architecture
         └── YES → Hexagonal Architecture
```

### Considerations by Service Type

#### Lambdas/Serverless Functions

| Lambda Type | Recommended Architecture |
|----------------|-------------------------|
| Simple API Gateway trigger | Simple |
| SQS/SNS event processor | Simple or Onion |
| Multi-service orchestrator | Onion |
| Complex domain with multiple triggers | Hexagonal |

#### Container Microservices

| Service Type | Recommended Architecture |
|------------------|-------------------------|
| BFF (Backend for Frontend) | Simple |
| Core domain service | Hexagonal |
| Integration service | Onion |
| Reporting service | Simple |

## Important Rules

1. **Don't over-architect**: A simple CRUD doesn't need hexagonal
2. **Evaluate cost-benefit**: More layers = more code = more maintenance
3. **Consider the team**: The architecture must be understandable by everyone
4. **Allow evolution**: Start simple and refactor when necessary
5. **Consistency in the domain**: Services in the same bounded context should use the same architecture
6. **Document the decision**: Use ADR to justify the choice

## Example

### Case: Payment System

**Context:**
- Financial domain with complex rules
- Multiple payment providers (Stripe, PayPal, wire transfers)
- PCI-DSS requirements
- Team of 6 developers
- Expected lifespan: 5+ years

**Evaluation:**

| Criterion | Value | Points |
|----------|-------|--------|
| Domain complexity | High | 3 |
| Business rules | Complex | 3 |
| External integrations | 5+ | 3 |
| Team size | 6 | 3 |
| Lifespan | 5+ years | 3 |
| Testing needs | Exhaustive | 3 |
| Infrastructure change | Likely | 3 |

**Decision: Hexagonal Architecture**

```java
// Output port
public interface PaymentGateway {
    PaymentResult processPayment(Payment payment);
    PaymentStatus checkStatus(String transactionId);
}

// Stripe adapter
@Component
public class StripePaymentAdapter implements PaymentGateway {
    @Override
    public PaymentResult processPayment(Payment payment) {
        // Stripe-specific implementation
    }
}

// PayPal adapter
@Component
public class PayPalPaymentAdapter implements PaymentGateway {
    @Override
    public PaymentResult processPayment(Payment payment) {
        // PayPal-specific implementation
    }
}
```

### Case: Notification Service

**Context:**
- Email and SMS sending
- No complex business logic
- Single provider (AWS SES/SNS)
- Team of 2 developers
- Lifespan: 2 years

**Evaluation:**

| Criterion | Value | Points |
|----------|-------|--------|
| Domain complexity | Low | 1 |
| Business rules | Minimal | 1 |
| External integrations | 2 | 1 |
| Team size | 2 | 1 |
| Lifespan | 2 years | 2 |
| Testing needs | Basic | 1 |
| Infrastructure change | Unlikely | 1 |

**Decision: Simple Architecture**

```typescript
// Simple and direct structure
@Injectable()
export class NotificationService {
  constructor(
    private readonly sesClient: SESClient,
    private readonly snsClient: SNSClient
  ) {}

  async sendEmail(request: EmailRequest): Promise<void> {
    await this.sesClient.send(new SendEmailCommand(request));
  }

  async sendSms(request: SmsRequest): Promise<void> {
    await this.snsClient.send(new PublishCommand(request));
  }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
