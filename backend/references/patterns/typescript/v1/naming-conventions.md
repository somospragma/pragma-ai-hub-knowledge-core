<!-- keywords: naming conventions, nomenclatura, interfaces, files, modules, classes, hexagonal, typescript -->
# Reference: Naming Conventions — TypeScript

## Purpose

Define the mandatory naming conventions for classes, interfaces, files, and modules in TypeScript hexagonal microservices.

## Scope of Application

All TypeScript projects (Lambda, serverless, Node.js). NON-NEGOTIABLE.

## Step by Step / Guidelines

### Class/Interface Naming (PascalCase) and File Naming (PascalCase)

| Component | Suffix | Class/Interface Name | File Name |
|-----------|--------|---------------------|-----------|
| Domain entity | _(none)_ | `Account` | `Account.ts` |
| Value object | _(none)_ | `Money` | `Money.ts` |
| Domain enum | _(none)_ | `OrderStatus` | `OrderStatus.ts` |
| Output port (interface) | `*Gateway` | `AccountGateway` | `AccountGateway.ts` |
| Use case | `*UseCase` | `CreateAccountUseCase` | `CreateAccountUseCase.ts` |
| Domain service | `*Service` | `PricingService` | `PricingService.ts` |
| Driven adapter | `*Adapter` | `AccountDynamoAdapter` | `AccountDynamoAdapter.ts` |
| Framework entity (DynamoDB) | `*Item` | `AccountItem` | `AccountItem.ts` |
| Framework entity (Mongo) | `*Document` | `AccountDocument` | `AccountDocument.ts` |
| Persistence mapper | `*EntityMapper` | `AccountEntityMapper` | `AccountEntityMapper.ts` |
| REST mapper | `*RestMapper` | `AccountRestMapper` | `AccountRestMapper.ts` |
| Lambda handler | `handler` (function) | `handler()` | `handler.ts` |
| DTO request | `*Request` | `CreateAccountRequest` | `CreateAccountRequest.ts` |
| DTO response | `*Response` | `AccountResponse` | `AccountResponse.ts` |
| Domain exception | `*Error` | `AccountNotFoundError` | `AccountNotFoundError.ts` |

### Mapper Rules (TypeScript — manual functions or classes)

Mappers are pure functions or static class methods. No framework needed.

```typescript
export class AccountEntityMapper {
    static toEntity(item: AccountItem): Account {
        return { id: item.pk, name: item.name, email: item.email };
    }
    
    static toItem(entity: Account): AccountItem {
        return { pk: entity.id, sk: `ACCOUNT#${entity.id}`, name: entity.name, email: entity.email };
    }
}
```

### Module/Folder Naming (snake_case)

| Module type | Pattern | Example |
|-------------|---------|---------|
| Driven adapter (REST) | `rest_api_{system}` | `rest_api_t24`, `rest_api_abanks` |
| Driven adapter (DB) | `dynamodb`, `mongodb` | `dynamodb` |
| Entry point (Lambda) | `functions/{function_name}` | `functions/get_user` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app_service` | `app_service` |

### Import Naming

```typescript
import { Account } from "../../../domain/model/Account";
import { AccountGateway } from "../../../domain/ports/AccountGateway";
import { CreateAccountUseCase } from "../../../domain/usecases/CreateAccountUseCase";
import { AccountDynamoAdapter } from "../../driven_adapters/dynamodb/AccountDynamoAdapter";
import { CreateAccountRequest } from "../dto/CreateAccountRequest";
```

### Naming Patterns

| Pattern | Structure | Example |
|---------|-----------|---------|
| Port | `{Concept}Gateway` | `AccountGateway`, `NotificationGateway` |
| Adapter | `{Concept}{Technology}Adapter` | `AccountDynamoAdapter`, `AccountRedisAdapter` |
| Use case | `{Action}{Concept}UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` |
| Mapper | `{Concept}{Layer}Mapper` | `AccountEntityMapper`, `AccountRestMapper` |
| Error | `{Concept}{Reason}Error` | `AccountNotFoundError`, `InsufficientFundsError` |

### TypeScript-specific rules

- Interfaces do NOT use `I` prefix (use `AccountGateway`, not `IAccountGateway`)
- Use `interface` for ports, `class` for implementations
- Use `type` for simple DTOs, `class` with `class-validator` decorators for validated DTOs
- Prefer `readonly` properties in domain entities
- Use `enum` for domain enumerations

## Verification Checklist

- [ ] Classes and interfaces use PascalCase
- [ ] Files use PascalCase (matching the class name)
- [ ] Folders use snake_case
- [ ] Ports are `interface` ending in `*Gateway`
- [ ] No `I` prefix on interfaces
- [ ] Adapters are `class` ending in `*Adapter`
- [ ] Use cases end in `*UseCase`
- [ ] Errors end in `*Error` (not `*Exception` — TypeScript convention)

## Tools and Resources

_(No additional information required for this section.)_
