---
id: backend-skill-node-lambda-arquetipo-hexagonal
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Arquetipo Hexagonal Serverless — Node Lambda

## Propósito

Proveer una estructura base estandarizada para desarrollar funciones serverless en TypeScript usando arquitectura hexagonal. Alineado con la definición canónica de capas hexagonales.

---

## Estructura de Capas

1. **Domain:** Modelos de negocio puros, interfaces de puertos `*Gateway`, y clases `*UseCase`. Sin dependencias de framework.
2. **Infrastructure:** Entry points (handlers Lambda), driven adapters (DynamoDB, REST clients, Redis), y helpers cross-cutting (HTTP client, logging, middleware).
3. **Application:** Solo assembler — contenedor DI y configuración. Sin lógica de negocio.

---

## Estructura de Carpetas

```
project/
├── domain/
│   ├── model/                      ← Interfaces/types puros, value objects, enums
│   ├── ports/                      ← Interfaces *Gateway (plano, sin sub-carpetas)
│   └── usecases/                   ← Clases *UseCase (dependen solo de model + ports)
├── infrastructure/
│   ├── driven_adapters/
│   │   ├── dynamodb/               ← Persistencia DynamoDB (*Adapter implementa *Gateway)
│   │   ├── redis_cache/            ← Adapter de caché Redis
│   │   ├── rest_api_{name}/        ← Consumidor de API externa
│   │   └── .../
│   ├── entry_points/
│   │   └── functions/              ← Handlers de funciones Lambda
│   │       ├── get_user/
│   │       │   └── handler.ts
│   │       └── create_order/
│   │           └── handler.ts
│   └── helpers/                    ← Utilidades cross-cutting de infra
│       ├── http_client.ts
│       ├── logger.ts
│       └── middleware.ts
├── application/
│   └── app_service/                ← Contenedor DI, config. SIN lógica de negocio
│       └── container.ts
├── tests/
├── serverless.yml                  ← o template.yaml (SAM)
├── tsconfig.json
├── package.json
└── jest.config.js
```

---

## Reglas de Dependencia

```
domain/model       → nada (tipos puros TypeScript)
domain/ports       → solo model
domain/usecases    → model + ports
helpers            → model + ports (+ deps de framework según necesidad)
driven_adapters    → model + ports + helpers
entry_points       → model + ports + usecases + helpers
app_service        → todos los módulos
```

---

## Patrones de Diseño Implementados

- **Repository Pattern**: Driven adapters implementan `*Gateway`
- **Adapter Pattern**: Clases `*Adapter` en driven adapters
- **Dependency Injection**: Contenedor en `application/app_service/`
- **Decorator Pattern**: Composición de middleware
- **Strategy Pattern**: Adapters intercambiables detrás de interfaces `*Gateway`

---

## Ejemplo: Entry Point (Handler Lambda)

```typescript
// infrastructure/entry_points/functions/get_parameter/handler.ts
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';
import { container } from '../../../../application/app_service/container';
import { GetParameterUseCase } from '../../../../domain/usecases/GetParameterUseCase';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const useCase = container.resolve(GetParameterUseCase);
  const key = event.pathParameters?.key;

  if (!key) {
    return { statusCode: 400, body: JSON.stringify({ error: 'Key is required' }) };
  }

  const result = await useCase.execute(key);
  return { statusCode: 200, body: JSON.stringify(result) };
};
```

## Ejemplo: Puerto Gateway

```typescript
// domain/ports/ParameterGateway.ts
import { Parameter } from '../model/Parameter';

export interface ParameterGateway {
  getByKey(key: string): Promise<Parameter | null>;
  save(parameter: Parameter): Promise<void>;
}
```

## Ejemplo: Caso de Uso

```typescript
// domain/usecases/GetParameterUseCase.ts
import { ParameterGateway } from '../ports/ParameterGateway';
import { Parameter } from '../model/Parameter';

export class GetParameterUseCase {
  constructor(private readonly parameterGateway: ParameterGateway) {}

  async execute(key: string): Promise<Parameter> {
    const parameter = await this.parameterGateway.getByKey(key);
    if (!parameter) throw new Error(`Parameter not found: ${key}`);
    return parameter;
  }
}
```

## Ejemplo: Driven Adapter

```typescript
// infrastructure/driven_adapters/dynamodb/ParameterDynamoAdapter.ts
import { DynamoDBDocumentClient, GetCommand, PutCommand } from '@aws-sdk/lib-dynamodb';
import { ParameterGateway } from '../../../domain/ports/ParameterGateway';
import { Parameter } from '../../../domain/model/Parameter';

export class ParameterDynamoAdapter implements ParameterGateway {
  constructor(private readonly docClient: DynamoDBDocumentClient, private readonly tableName: string) {}

  async getByKey(key: string): Promise<Parameter | null> {
    const response = await this.docClient.send(new GetCommand({
      TableName: this.tableName,
      Key: { pk: `PARAM#${key}`, sk: 'VALUE' }
    }));
    return response.Item ? { key, value: response.Item.value } : null;
  }

  async save(parameter: Parameter): Promise<void> {
    await this.docClient.send(new PutCommand({
      TableName: this.tableName,
      Item: { pk: `PARAM#${parameter.key}`, sk: 'VALUE', value: parameter.value }
    }));
  }
}
```

## Ejemplo: DTO con Validación

```typescript
// infrastructure/entry_points/functions/create_user/dto/CreateUserRequest.ts
import { IsString, IsNotEmpty, Length } from 'class-validator';

export class CreateUserRequest {
  @IsString()
  @IsNotEmpty({ message: 'Username is required' })
  @Length(1, 100)
  firstName!: string;
}
```

---

## Anti-patrones — Qué NO generar

| Anti-patrón | Por qué está mal | Estructura correcta |
|---|---|---|
| Carpeta `crosscutting/` en raíz | Hexagonal no tiene capa "crosscutting" | Usar `infrastructure/helpers/` |
| `application/` dentro de cada dominio | Use cases van en `domain/usecases/` | `application/app_service/` solo DI + config |
| Puertos nombrados `*Port` o `*Repository` | Convención Pragma requiere `*Gateway` | `ParameterGateway`, `UserGateway` |
| Lógica de negocio en `infrastructure/helpers/` | Helpers son solo para concerns de infra | Lógica en `domain/usecases/` o `domain/model/` |
| DTOs en capa compartida | DTOs viven dentro de cada entry point o adapter | Dentro de cada adapter/entry point |

---

## Reglas Importantes

- Las funciones serverless son entry points: viven en `infrastructure/entry_points/functions/`
- El dominio DEBE permanecer independiente de frameworks e infraestructura
- Los use cases viven en `domain/usecases/`, NUNCA en `application/`
- Los puertos usan convención `*Gateway` — **NO NEGOCIABLE**
- Los adapters usan convención `*Adapter`
- Las dependencias siempre fluyen hacia adentro: infrastructure → domain
