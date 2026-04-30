<!-- keywords: lambda, clean architecture, typescript, serverless, clean code, solid, design patterns, nodejs, archetype -->
# Lambda Node Clean Architecture Archetype

## Purpose

Provide a base structure for developing Lambda functions with TypeScript applying Clean Architecture and Clean Code principles. This archetype demonstrates the implementation of modern design patterns and SOLID principles in a serverless context.

## Scope of Application

- When developing Lambda functions with TypeScript that require high maintainability.
- When Clean Architecture needs to be applied in serverless projects.
- For projects that require multiple Lambda functions with shared code.
- As an implementation guide for design patterns in Node.js.

## Main Content

### Project Structure

```
backend-diseno-arquitectura-fnc-ts-architype-lambda-node/
├── src/
│   ├── dependencies/              # Shared code between functions
│   │   ├── core/                  # Shared domain logic
│   │   └── transversal/           # cross-cutting utilities
│   └── functions/                 # Individual Lambda functions
│       ├── create-user-http/
│       │   ├── application/       # Use cases
│       │   ├── infrastructure/    # Adapters
│       │   └── handler.ts         # Entry point
│       ├── get-users-http/
│       └── create-posts-http/
├── test/                          # Unit tests
├── __mocks__/                     # Mocks for testing
├── serverless.yml                 # Serverless Framework configuration
├── jest.config.js
├── eslint.config.mjs
├── tsconfig.json
└── package.json
```

### Architecture per Function

Each Lambda function follows the Clean Architecture structure:

```
function-name/
├── application/           # Application layer (use cases)
├── infrastructure/        # Infrastructure layer (adapters)
└── handler.ts            # Lambda entry point
```

### Applied Principles

| Principle | Description |
|-----------|-------------|
| SRP | Each module has a single reason to change |
| OCP | Code open for extension, closed for modification |
| LSP | Derived classes substitute their bases without affecting behavior |
| ISP | Do not force dependencies on unused interfaces |
| DIP | Depend on abstractions, not implementations |
| DRY | Do not repeat code or business logic |
| KISS | Keep the code simple and straightforward |

### Implemented Design Patterns

- Singleton
- Builder
- Repository
- Decorator
- Adapter
- Facade
- Chain of Responsibility

### Technologies Used

- Language: TypeScript
- Framework: Serverless Framework
- Database: SQLite with TypeORM
- Testing: Jest
- Linting: ESLint
- Formatting: Prettier
- Commits: Commitlint

## Important Rules

1. Each Lambda function must follow the layer structure (application, infrastructure).
2. Shared code goes in `dependencies/` (core for domain, transversal for utilities).
3. Handlers only orchestrate; they do not contain business logic.
4. Use dependency injection to improve decoupling.
5. Avoid nested ifs (hadoken if) using patterns like Strategy.
6. Follow naming conventions: UpperCamelCase for classes, lowerCamelCase for variables.

## Example

### Handler (orchestration)

```typescript
// src/functions/create-user-http/handler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { CreateUserUseCase } from './application/create-user.usecase';
import { UserRepositoryAdapter } from './infrastructure/user-repository.adapter';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const repository = new UserRepositoryAdapter();
  const useCase = new CreateUserUseCase(repository);
  
  const body = JSON.parse(event.body || '{}');
  const result = await useCase.execute(body);
  
  return {
    statusCode: 201,
    body: JSON.stringify(result)
  };
};
```

### Map Pattern to Avoid Switch

```typescript
// Avoid switch statements using Map
const mapExecutor = new Map<string, Function>();
mapExecutor.set("VALIDATE", Array.from);
mapExecutor.set("CREATE", Object.assign);
mapExecutor.set("UPDATE", () => {});

// Execute action
mapExecutor.get("VALIDATE")?.();
```

### Execution Commands

```bash
# Install dependencies
npm install

# Run locally
npm run dev

# Run tests
npm test

# Lint
npm run lint
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
