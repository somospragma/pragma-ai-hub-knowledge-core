<!-- keywords: naming, conventions, mapstruct, mapper, gateway, adapter, usecase, dto, record, java -->

# Reference: Naming Conventions — Java

## Purpose

Define the mandatory naming conventions for classes, interfaces, files, and modules in Java hexagonal microservices.

## Scope of Application

All Java projects (Spring Boot, WebFlux, Gradle). NON-NEGOTIABLE.

## Step by Step / Guidelines

> **All Java interfaces MUST have the `I` prefix. This is NON-NEGOTIABLE.**

### Class and Interface Naming (PascalCase)

| Component | Suffix | Class Name | File Name |
|-----------|--------|------------|-----------|
| Domain entity | _(none)_ | `Account` | `Account.java` |
| Value object | _(none)_ | `Money` | `Money.java` |
| Domain enum | _(none)_ | `OrderStatus` | `OrderStatus.java` |
| Output port | `I*Gateway` | `IAccountGateway` | `IAccountGateway.java` |
| Use case | `*UseCase` | `CreateAccountUseCase` | `CreateAccountUseCase.java` |
| Domain service | `*Service` | `PricingService` | `PricingService.java` |
| Driven adapter | `*Adapter` | `AccountJpaAdapter` | `AccountJpaAdapter.java` |
| Framework entity (SQL) | `*Entity` | `AccountEntity` | `AccountEntity.java` |
| Framework entity (Mongo) | `*Document` | `AccountDocument` | `AccountDocument.java` |
| Framework entity (DynamoDB) | `*Item` | `AccountItem` | `AccountItem.java` |
| Framework repository | `*Repository` | `AccountJpaRepository` | `AccountJpaRepository.java` |
| Persistence mapper (MapStruct) | `*EntityMapper` | `AccountEntityMapper` | `AccountEntityMapper.java` |
| REST mapper (MapStruct) | `*RestMapper` | `AccountRestMapper` | `AccountRestMapper.java` |
| External API mapper (MapStruct) | `*AdapterMapper` | `AbanksAdapterMapper` | `AbanksAdapterMapper.java` |
| Router (WebFlux) | `*Router` | `AccountRouter` | `AccountRouter.java` |
| Handler (WebFlux) | `*Handler` | `AccountHandler` | `AccountHandler.java` |
| Controller (Spring MVC) | `*Controller` | `AccountController` | `AccountController.java` |
| DTO request | `*Request` (Record) | `CreateAccountRequest` | `CreateAccountRequest.java` |
| DTO response | `*Response` (Record) | `AccountResponse` | `AccountResponse.java` |
| Domain exception | `*Exception` | `AccountNotFoundException` | `AccountNotFoundException.java` |
| Config class | `*Config` | `UseCasesConfig` | `UseCasesConfig.java` |

### Mapper Rules (Java — MapStruct mandatory)

All mappers MUST be MapStruct `@Mapper(componentModel = "spring")` interfaces.

```java
@Mapper(componentModel = "spring")
public interface AccountEntityMapper {
    Account toModel(AccountEntity entity);
    AccountEntity toEntity(Account model);
}
```

### Module/Folder Naming (kebab-case)

| Module type | Pattern | Example |
|-------------|---------|---------|
| Driven adapter (REST) | `{system}-client-api` | `t24-client-api`, `abanks-client-api` |
| Driven adapter (SOAP) | `{system}-soap-api` | `vision-plus-soap-api` |
| Driven adapter (DB) | `{technology}-persistence` | `r2dbc-persistence`, `oracle-repository` |
| Entry point (reactive) | `reactive-web` | `reactive-web` |
| Entry point (imperative) | `rest` | `rest` |
| Helpers | `helpers` | `helpers` |
| App assembler | `app-service` | `app-service` |

### Package Naming

```
{base.package}.model          → domain/model
{base.package}.ports          → domain/ports  
{base.package}.usecase        → domain/usecases
{base.package}.helper         → infrastructure/helpers
{base.package}.{adapter}      → infrastructure/driven-adapters/{adapter}
{base.package}.entrypoint     → infrastructure/entry-points/{entry-point}
{base.package}.config         → application/app-service/config
```

### Naming Patterns

| Pattern | Structure | Example |
|---------|-----------|---------|
| Port | `I{Concept}Gateway` | `IAccountGateway`, `INotificationGateway` |
| Adapter | `{Concept}{Technology}Adapter` | `AccountJpaAdapter`, `AccountR2dbcAdapter` |
| Use case | `{Action}{Concept}UseCase` | `CreateAccountUseCase`, `GetAccountUseCase` |
| Mapper | `{Concept}{Layer}Mapper` | `AccountEntityMapper`, `AccountRestMapper` |
| DTO | `{Action}{Concept}Request/Response` | `CreateAccountRequest`, `AccountResponse` |
| Exception | `{Concept}{Reason}Exception` | `AccountNotFoundException`, `InsufficientFundsException` |

## Verification Checklist

- [ ] All interfaces MUST have `I` prefix (e.g., `IAccountGateway`)
- [ ] No `Impl` suffix on adapters (use `AccountJpaAdapter`, not `AccountGatewayImpl`)
- [ ] All mappers are MapStruct `@Mapper` interfaces — NO static/manual mappers
- [ ] Module folders use kebab-case
- [ ] Packages use lowercase dot notation
- [ ] DTOs are Java Records. DTOs MUST NOT have `*DTO` suffix. Use `*Request` / `*Response` directly
- [ ] Use cases end in `UseCase`, not `Service` or `Handler`

## Tools and Resources

_(No additional information required for this section.)_
