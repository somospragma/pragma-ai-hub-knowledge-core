---
id: backend-skill-node-lambda-patrones
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Patrones de Diseño y Convenciones — Node Lambda

## Propósito

Definir las convenciones de naming, principios SOLID aplicados, validación de inputs con Zod, mapeo DTO↔Entity, y patrones de diseño estándar para funciones Lambda con TypeScript.

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
| Mapper de persistencia | `*EntityMapper` | `AccountEntityMapper` | `AccountEntityMapper.ts` |
| Mapper REST | `*RestMapper` | `AccountRestMapper` | `AccountRestMapper.ts` |
| Lambda handler | `handler` (función) | `handler()` | `handler.ts` |
| DTO request | `*Request` | `CreateAccountRequest` | `CreateAccountRequest.ts` |
| DTO response | `*Response` | `AccountResponse` | `AccountResponse.ts` |
| Excepción de dominio | `*Error` | `AccountNotFoundError` | `AccountNotFoundError.ts` |

### Reglas específicas de TypeScript

- Las interfaces NO usan prefijo `I` (usar `AccountGateway`, no `IAccountGateway`)
- Usar `interface` para puertos, `class` para implementaciones
- Usar `type` para DTOs simples, `class` con decoradores para DTOs validados
- Preferir propiedades `readonly` en entidades de dominio
- Usar `enum` para enumeraciones de dominio

### Módulos/Carpetas (snake_case)

| Tipo de módulo | Patrón | Ejemplo |
|---------------|--------|---------|
| Driven adapter (REST) | `rest_api_{sistema}` | `rest_api_t24` |
| Driven adapter (DB) | `dynamodb`, `mongodb` | `dynamodb` |
| Entry point (Lambda) | `functions/{function_name}` | `functions/get_user` |
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

## 2. Principios SOLID en Lambda TypeScript

### S — Single Responsibility Principle

```typescript
// Handler solo orquesta
export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const useCase = container.resolve(CreateAccountUseCase);
  const body = JSON.parse(event.body || '{}');
  const result = await useCase.execute(body);
  return { statusCode: 201, body: JSON.stringify(result) };
};

// Use case con responsabilidad única
class CreateAccountUseCase {
  constructor(private readonly accountGateway: AccountGateway) {}
  async execute(request: CreateAccountRequest): Promise<Account> {
    const account: Account = { id: crypto.randomUUID(), ...request, status: 'ACTIVE' };
    return this.accountGateway.save(account);
  }
}
```

### D — Dependency Inversion Principle

```typescript
// El dominio define la abstracción
interface AccountGateway {
  findById(id: string): Promise<Account | null>;
  save(account: Account): Promise<Account>;
}

// Use case depende de abstracción
class GetAccountUseCase {
  constructor(private readonly accountGateway: AccountGateway) {}
  async execute(id: string): Promise<Account> {
    const account = await this.accountGateway.findById(id);
    if (!account) throw new AccountNotFoundError(id);
    return account;
  }
}

// Infraestructura implementa la abstracción
class AccountDynamoAdapter implements AccountGateway {
  constructor(private readonly docClient: DynamoDBDocumentClient, private readonly tableName: string) {}
  async findById(id: string): Promise<Account | null> { /* ... */ }
  async save(account: Account): Promise<Account> { /* ... */ }
}
```

---

## 3. Validación de Inputs con Zod

```typescript
import { z } from 'zod';

export const CreateAccountSchema = z.object({
  name: z.string().min(1).max(100),
  email: z.string().email(),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/).optional()
});

export type CreateAccountRequest = z.infer<typeof CreateAccountSchema>;

// Validación en handler
export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const body = JSON.parse(event.body || '{}');
  const parseResult = CreateAccountSchema.safeParse(body);

  if (!parseResult.success) {
    return {
      statusCode: 400,
      body: JSON.stringify({
        type: 'https://api.company.com/errors/validation-error',
        title: 'Validation Error',
        status: 400,
        errors: parseResult.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
      })
    };
  }

  const useCase = container.resolve(CreateAccountUseCase);
  const result = await useCase.execute(parseResult.data);
  return { statusCode: 201, body: JSON.stringify(result) };
};
```

---

## 4. Mapeo DTO ↔ Entity

### Mapper como clase pura

```typescript
export class AccountEntityMapper {
  static toEntity(item: AccountItem): Account {
    return { id: item.pk.replace('ACCOUNT#', ''), name: item.name, email: item.email, status: item.status };
  }

  static toItem(entity: Account): AccountItem {
    return { pk: `ACCOUNT#${entity.id}`, sk: 'PROFILE', name: entity.name, email: entity.email, status: entity.status };
  }
}

// Uso en adapter
class AccountDynamoAdapter implements AccountGateway {
  async findById(id: string): Promise<Account | null> {
    const response = await this.docClient.send(new GetCommand({ TableName: this.tableName, Key: { pk: `ACCOUNT#${id}`, sk: 'PROFILE' } }));
    return response.Item ? AccountEntityMapper.toEntity(response.Item as AccountItem) : null;
  }

  async save(account: Account): Promise<Account> {
    const item = AccountEntityMapper.toItem(account);
    await this.docClient.send(new PutCommand({ TableName: this.tableName, Item: item }));
    return account;
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
- [ ] Errores terminan en `*Error`
- [ ] Handlers solo orquestan, sin lógica de negocio
- [ ] Validación con Zod en el handler antes de invocar use case
- [ ] Mappers son funciones puras o clases estáticas
