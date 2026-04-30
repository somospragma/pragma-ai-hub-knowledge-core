<!-- keywords: hexagonal architecture, serverless, typescript, lambda, archetype, clean architecture -->
# Hexagonal TypeScript Serverless Archetype

## Purpose

Provide a standardized base structure for developing serverless functions in TypeScript using hexagonal architecture. Aligned with the canonical definition in `01-architecture/hexagonal-layers.md`.

## Scope of Application

- When developing serverless functions (AWS Lambda, Azure Functions) with TypeScript.
- When a clean, decoupled hexagonal architecture is needed for serverless projects.
- For projects that require integration with databases, caches, or external REST APIs.

## Main Content

### Layer Structure

1. **Domain:** Pure business models, `*Gateway` port interfaces, and `*UseCase` classes. No framework dependencies.
2. **Infrastructure:** Entry points (serverless function handlers), driven adapters (DynamoDB, REST clients, Redis, etc.), and cross-cutting helpers (HTTP client, logging, middleware).
3. **Application:** Assembler only — DI container and configuration. No business logic.

### Folder Structure

```
project/
├── domain/
│   ├── model/                      ← Pure interfaces/types, value objects, enums. No framework.
│   ├── ports/                      ← *Gateway interfaces. Flat, no inbound/outbound sub-folders.
│   └── usecases/                   ← *UseCase classes. Depend only on model + ports.
├── infrastructure/
│   ├── driven_adapters/
│   │   ├── dynamodb/               ← DynamoDB persistence (*Adapter implements *Gateway)
│   │   ├── redis_cache/            ← Redis cache adapter
│   │   ├── rest_api_{name}/        ← External API consumer (e.g., rest_api_external/)
│   │   └── .../
│   ├── entry_points/
│   │   └── functions/              ← Serverless function handlers (Lambda/Azure Functions)
│   │       ├── get_user/
│   │       │   └── handler.ts
│   │       └── create_order/
│   │           └── handler.ts
│   └── helpers/                    ← cross-cutting infra utilities (HTTP client, logging, middleware)
│       ├── http_client.ts
│       ├── logger.ts
│       └── middleware.ts
├── application/
│   └── app_service/                ← DI container, config. NO business logic.
│       └── container.ts
├── tests/
├── serverless.yml                  ← or template.yaml (SAM)
├── tsconfig.json
├── package.json
└── jest.config.js
```

### Implemented Design Patterns

- Repository Pattern (driven adapters implement `*Gateway`)
- Adapter Pattern (`*Adapter` classes in driven adapters)
- Dependency Injection (container in `application/app_service/`)
- Decorator Pattern (middleware composition)
- Strategy Pattern (swappable adapters behind `*Gateway` interfaces)

## Important Rules

- Serverless functions are entry points: they live in `infrastructure/entry_points/functions/` and call use cases.
- The domain MUST remain independent of frameworks and infrastructure details.
- Use cases live in `domain/usecases/`, never in `application/` or inside individual function folders.
- Port interfaces use the `*Gateway` naming convention. This is **NON-NEGOTIABLE**.
- Adapter implementations use the `*Adapter` naming convention.
- `infrastructure/helpers/` holds cross-cutting infra concerns (logging, HTTP client, middleware). Business logic NEVER goes here.
- `application/app_service/` is ONLY the assembler (DI container + config). No use cases, no business logic.
- DTOs live inside each entry point or driven adapter, not in a shared layer.
- Mappers live inside each adapter, not in a shared layer.
- Dependencies always flow inward: infrastructure → domain. The domain never knows about infrastructure.

## Dependency Rules

```
domain/model       → nothing (pure TypeScript types)
domain/ports       → model only
domain/usecases    → model + ports
helpers            → model + ports (+ framework deps as needed)
driven_adapters    → model + ports + helpers
entry_points       → model + ports + usecases + helpers
app_service        → all modules
```

## Example

### Serverless Function (Entry Point)

```typescript
// infrastructure/entry_points/functions/get_parameter/handler.ts
import { container } from "../../../../application/app_service/container";
import { GetParameterUseCase } from "../../../../domain/usecases/GetParameterUseCase";
import { applyMiddleware } from "../../../helpers/middleware";

async function handler(req: HttpRequest, context: InvocationContext): Promise<HttpResponseInit> {
    return applyMiddleware(context, async () => {
        const useCase = container.resolve(GetParameterUseCase);
        const result = await useCase.execute(req.params.key);

        return { status: 200, body: JSON.stringify(result) };
    });
}
```

### Gateway Port

```typescript
// domain/ports/ParameterGateway.ts
import { Parameter } from "../model/Parameter";

export interface ParameterGateway {
    getByKey(key: string): Promise<Parameter | null>;
    save(parameter: Parameter): Promise<void>;
}
```

### Use Case

```typescript
// domain/usecases/GetParameterUseCase.ts
import { ParameterGateway } from "../ports/ParameterGateway";
import { Parameter } from "../model/Parameter";

export class GetParameterUseCase {
    constructor(private readonly parameterGateway: ParameterGateway) {}

    async execute(key: string): Promise<Parameter> {
        const parameter = await this.parameterGateway.getByKey(key);
        if (!parameter) throw new Error(`Parameter not found: ${key}`);
        return parameter;
    }
}
```

### Driven Adapter

```typescript
// infrastructure/driven_adapters/redis_cache/ParameterRedisAdapter.ts
import { ParameterGateway } from "../../../domain/ports/ParameterGateway";
import { Parameter } from "../../../domain/model/Parameter";

export class ParameterRedisAdapter implements ParameterGateway {
    constructor(private readonly redisClient: RedisClient) {}

    async getByKey(key: string): Promise<Parameter | null> {
        const value = await this.redisClient.get(key);
        return value ? { key, value } : null;
    }

    async save(parameter: Parameter): Promise<void> {
        await this.redisClient.set(parameter.key, parameter.value);
    }
}
```

### DTO with Validation

```typescript
// infrastructure/entry_points/functions/create_user/dto/CreateUserRequest.ts
import { IsString, IsNotEmpty, Length } from "class-validator";

export class CreateUserRequest {
    @IsString()
    @IsNotEmpty({ message: "Username is required" })
    @Length(1, 100, { message: "Username must be between 1 and 100 characters" })
    firstName!: string;
}
```

## Anti-patterns — What NOT to do

| Anti-pattern | Why it's wrong | Correct structure |
|---|---|---|
| `crosscutting/` folder at root or inside `src/` | Hexagonal architecture has no "crosscutting" layer. cross-cutting infra utilities belong in `infrastructure/helpers/`. | Use `infrastructure/helpers/` for logging, HTTP client, middleware, config. |
| `application/` inside each business domain (e.g., `parameterManagement/application/`) | Use cases belong in `domain/usecases/`, not in per-domain `application/` folders. `application/` is only the assembler. | Use cases in `domain/usecases/`. `application/app_service/` is only DI + config. |
| Functions at root calling into per-domain `application/` layers | Functions are entry points and belong in `infrastructure/entry_points/`. They call use cases from `domain/usecases/`. | `infrastructure/entry_points/functions/{function_name}/handler.ts` |
| Port interfaces named `*Port` or `*Repository` | the organization convention requires `*Gateway` for all port interfaces. | `ParameterGateway`, `UserGateway`, `NotificationGateway` |
| Business logic in `infrastructure/helpers/` | Helpers are for infra-level cross-cutting concerns only. | Business logic goes in `domain/usecases/` or `domain/model/`. |

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
