---
id: backend-skill-node-lambda-arquetipo-clean
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Arquetipo Clean Architecture Lambda — Node Lambda

## Propósito

Proveer una estructura base para desarrollar funciones Lambda con TypeScript aplicando Clean Architecture y principios Clean Code. Demuestra la implementación de patrones de diseño modernos y principios SOLID en contexto serverless.

---

## Estructura del Proyecto

```
project/
├── src/
│   ├── dependencies/              # Código compartido entre funciones
│   │   ├── core/                  # Lógica de dominio compartida
│   │   └── transversal/           # Utilidades cross-cutting
│   └── functions/                 # Funciones Lambda individuales
│       ├── create-user-http/
│       │   ├── application/       # Casos de uso
│       │   ├── infrastructure/    # Adapters
│       │   └── handler.ts         # Entry point
│       ├── get-users-http/
│       └── create-posts-http/
├── test/                          # Tests unitarios
├── __mocks__/                     # Mocks para testing
├── serverless.yml                 # Configuración Serverless Framework
├── jest.config.js
├── eslint.config.mjs
├── tsconfig.json
└── package.json
```

---

## Arquitectura por Función

Cada función Lambda sigue la estructura Clean Architecture:

```
function-name/
├── application/           # Capa de aplicación (casos de uso)
├── infrastructure/        # Capa de infraestructura (adapters)
└── handler.ts            # Entry point Lambda
```

---

## Principios Aplicados

| Principio | Descripción |
|-----------|-------------|
| SRP | Cada módulo tiene una sola razón para cambiar |
| OCP | Código abierto para extensión, cerrado para modificación |
| LSP | Clases derivadas sustituyen sus bases sin afectar comportamiento |
| ISP | No forzar dependencias en interfaces no usadas |
| DIP | Depender de abstracciones, no de implementaciones |
| DRY | No repetir código ni lógica de negocio |
| KISS | Mantener el código simple y directo |

---

## Patrones de Diseño Implementados

- **Singleton**: Instancias únicas de clientes AWS
- **Builder**: Construcción de objetos complejos
- **Repository**: Abstracción de persistencia
- **Decorator**: Composición de comportamiento
- **Adapter**: Integración con servicios externos
- **Facade**: Simplificación de interfaces complejas
- **Chain of Responsibility**: Procesamiento en cadena

---

## Tecnologías

- **Lenguaje**: TypeScript
- **Framework**: Serverless Framework
- **Testing**: Jest
- **Linting**: ESLint + Prettier
- **Commits**: Commitlint

---

## Ejemplo: Handler (Orquestación)

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

## Ejemplo: Caso de Uso

```typescript
// src/functions/create-user-http/application/create-user.usecase.ts
import { UserGateway } from '../../../dependencies/core/ports/UserGateway';
import { User } from '../../../dependencies/core/model/User';

export class CreateUserUseCase {
  constructor(private readonly userGateway: UserGateway) {}

  async execute(input: { name: string; email: string }): Promise<User> {
    if (!input.name || !input.email) {
      throw new Error('Name and email are required');
    }
    const user: User = {
      id: crypto.randomUUID(),
      name: input.name,
      email: input.email,
      createdAt: new Date().toISOString()
    };
    return this.userGateway.save(user);
  }
}
```

## Ejemplo: Patrón Map para evitar Switch

```typescript
// Evitar switch statements usando Map
const mapExecutor = new Map<string, (data: any) => Promise<any>>();
mapExecutor.set('VALIDATE', validateOrder);
mapExecutor.set('CREATE', createOrder);
mapExecutor.set('UPDATE', updateOrder);

// Ejecutar acción
const action = mapExecutor.get(event.action);
if (action) await action(event.data);
```

---

## Configuración

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "test"]
}
```

### package.json (scripts)

```json
{
  "scripts": {
    "build": "tsc",
    "dev": "serverless offline",
    "test": "jest --coverage",
    "lint": "eslint src/",
    "deploy": "serverless deploy"
  }
}
```

---

## Reglas Importantes

1. Cada función Lambda DEBE seguir la estructura de capas (application, infrastructure)
2. Código compartido va en `dependencies/` (core para dominio, transversal para utilidades)
3. Handlers solo orquestan; NO contienen lógica de negocio
4. Usar inyección de dependencias para mejorar desacoplamiento
5. Evitar ifs anidados (hadoken if) usando patrones como Strategy o Map
6. Seguir convenciones de naming: PascalCase para clases, camelCase para variables
7. Mantener 100% de cobertura en tests unitarios
