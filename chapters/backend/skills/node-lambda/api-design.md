---
id: backend-skill-node-lambda-api-design
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Diseño de APIs — Node Lambda

## Propósito

Guía de implementación de diseño de APIs REST en funciones Lambda con TypeScript: estándares REST con API Gateway, error handling RFC 7807, versionamiento, OpenAPI y AsyncAPI.

---

## 1. REST Standards con API Gateway

### Handler con respuesta estándar

```typescript
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

// Helper de respuesta
function apiResponse(statusCode: number, body: any, headers?: Record<string, string>): APIGatewayProxyResult {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      ...headers
    },
    body: JSON.stringify(body)
  };
}

// GET /customers — Listado con paginación
export const listCustomers = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const page = parseInt(event.queryStringParameters?.page || '0');
  const size = parseInt(event.queryStringParameters?.size || '20');
  const status = event.queryStringParameters?.status;

  const result = await customerService.findAll({ page, size, status });
  const totalPages = Math.ceil(result.total / size);

  return apiResponse(200, {
    data: result.items,
    pagination: { page, pageSize: size, totalItems: result.total, totalPages },
    _links: {
      self: `/customers?page=${page}&size=${size}`,
      first: `/customers?page=0&size=${size}`,
      last: `/customers?page=${totalPages - 1}&size=${size}`,
      ...(page > 0 && { prev: `/customers?page=${page - 1}&size=${size}` }),
      ...(page < totalPages - 1 && { next: `/customers?page=${page + 1}&size=${size}` })
    }
  });
};

// GET /customers/{id} — Detalle
export const getCustomer = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const id = event.pathParameters?.id;
  if (!id) return apiResponse(400, { error: 'Customer ID is required' });

  const customer = await customerService.findById(id);
  if (!customer) {
    return apiResponse(404, {
      type: 'https://api.example.com/errors/not-found',
      title: 'Customer Not Found',
      status: 404,
      detail: `Customer with id '${id}' not found`
    });
  }

  return apiResponse(200, customer);
};

// POST /customers — Creación
export const createCustomer = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const body = JSON.parse(event.body || '{}');
  const validation = CreateCustomerSchema.safeParse(body);

  if (!validation.success) {
    return apiResponse(400, {
      type: 'https://api.example.com/errors/validation-error',
      title: 'Validation Error',
      status: 400,
      errors: validation.error.errors.map(e => ({ field: e.path.join('.'), message: e.message }))
    });
  }

  const customer = await customerService.create(validation.data);
  return apiResponse(201, customer, { 'Location': `/customers/${customer.id}` });
};
```

---

## 2. Error Handling RFC 7807

### Modelo de error para Lambda

```typescript
interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  traceId?: string;
  timestamp: string;
  errors?: Array<{ field: string; message: string }>;
}

enum ErrorType {
  VALIDATION_ERROR = 'validation-error',
  RESOURCE_NOT_FOUND = 'resource-not-found',
  CONFLICT = 'conflict',
  UNAUTHORIZED = 'unauthorized',
  FORBIDDEN = 'forbidden',
  INTERNAL_ERROR = 'internal-error',
  SERVICE_UNAVAILABLE = 'service-unavailable'
}

const ERROR_CONFIG: Record<ErrorType, { title: string; status: number }> = {
  [ErrorType.VALIDATION_ERROR]: { title: 'Validation Error', status: 400 },
  [ErrorType.RESOURCE_NOT_FOUND]: { title: 'Resource Not Found', status: 404 },
  [ErrorType.CONFLICT]: { title: 'Resource Conflict', status: 409 },
  [ErrorType.UNAUTHORIZED]: { title: 'Unauthorized', status: 401 },
  [ErrorType.FORBIDDEN]: { title: 'Forbidden', status: 403 },
  [ErrorType.INTERNAL_ERROR]: { title: 'Internal Server Error', status: 500 },
  [ErrorType.SERVICE_UNAVAILABLE]: { title: 'Service Unavailable', status: 503 }
};
```

### Excepciones personalizadas

```typescript
class AppError extends Error {
  constructor(public errorType: ErrorType, public detail: string, public fieldErrors?: Array<{ field: string; message: string }>) {
    super(detail);
    this.name = 'AppError';
  }
}

class ResourceNotFoundError extends AppError {
  constructor(resourceType: string, resourceId: string) {
    super(ErrorType.RESOURCE_NOT_FOUND, `${resourceType} with id '${resourceId}' not found`);
  }
}

class ValidationError extends AppError {
  constructor(errors: Array<{ field: string; message: string }>) {
    super(ErrorType.VALIDATION_ERROR, 'Request validation failed', errors);
  }
}
```

### Error handler wrapper para Lambda

```typescript
type LambdaHandler = (event: APIGatewayProxyEvent) => Promise<APIGatewayProxyResult>;

export function withErrorHandling(handler: LambdaHandler): LambdaHandler {
  return async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
    try {
      return await handler(event);
    } catch (error) {
      const traceId = event.requestContext?.requestId || '';

      if (error instanceof AppError) {
        const config = ERROR_CONFIG[error.errorType];
        const problem: ProblemDetail = {
          type: `https://api.example.com/errors/${error.errorType}`,
          title: config.title,
          status: config.status,
          detail: error.detail,
          instance: event.path,
          traceId,
          timestamp: new Date().toISOString(),
          ...(error.fieldErrors && { errors: error.fieldErrors })
        };
        return {
          statusCode: config.status,
          headers: { 'Content-Type': 'application/problem+json' },
          body: JSON.stringify(problem)
        };
      }

      console.error('Unexpected error:', error);
      return {
        statusCode: 500,
        headers: { 'Content-Type': 'application/problem+json' },
        body: JSON.stringify({
          type: 'https://api.example.com/errors/internal-error',
          title: 'Internal Server Error',
          status: 500,
          detail: 'An unexpected error occurred',
          traceId,
          timestamp: new Date().toISOString()
        })
      };
    }
  };
}

// Uso
export const handler = withErrorHandling(async (event) => {
  const id = event.pathParameters?.id;
  const customer = await customerService.findById(id!);
  if (!customer) throw new ResourceNotFoundError('Customer', id!);
  return apiResponse(200, customer);
});
```

---

## 3. Versionamiento con API Gateway

### template.yaml con stages versionados

```yaml
Resources:
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      EndpointConfiguration: REGIONAL

  # V1 (deprecated)
  GetCustomersV1:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/functions/v1/get-customers/handler.handler
      Events:
        Api:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /v1/customers
            Method: GET

  # V2 (current)
  GetCustomersV2:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src/functions/v2/get-customers/handler.handler
      Events:
        Api:
          Type: Api
          Properties:
            RestApiId: !Ref ApiGateway
            Path: /v2/customers
            Method: GET
```

### Handler V1 con headers de deprecación

```typescript
export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const customers = await customerService.listV1();

  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Deprecation': 'true',
      'Sunset': 'Sat, 01 Jun 2025 00:00:00 GMT',
      'Link': '</v2/customers>; rel="successor-version"'
    },
    body: JSON.stringify(customers)
  };
};
```

---

## 4. AsyncAPI — Validación de Mensajes

### Validador para eventos Lambda

```typescript
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

const orderCreatedSchema = {
  type: 'object',
  required: ['eventId', 'eventType', 'timestamp', 'data'],
  properties: {
    eventId: { type: 'string', format: 'uuid' },
    eventType: { const: 'OrderCreated' },
    timestamp: { type: 'string', format: 'date-time' },
    data: {
      type: 'object',
      required: ['orderId', 'customerId', 'totalAmount'],
      properties: {
        orderId: { type: 'string' },
        customerId: { type: 'string' },
        totalAmount: { type: 'number', minimum: 0 }
      }
    }
  }
};

const validateOrderCreated = ajv.compile(orderCreatedSchema);

export function validateMessage(message: unknown): { valid: boolean; errors?: string[] } {
  const valid = validateOrderCreated(message);
  if (valid) return { valid: true };
  return { valid: false, errors: validateOrderCreated.errors?.map(e => `${e.instancePath} ${e.message}`) };
}

// Uso en handler SQS
export const handler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  const failures: SQSBatchResponse['batchItemFailures'] = [];

  for (const record of event.Records) {
    const message = JSON.parse(record.body);
    const validation = validateMessage(message);

    if (!validation.valid) {
      console.error('Invalid message:', validation.errors);
      failures.push({ itemIdentifier: record.messageId });
      continue;
    }

    await processValidMessage(message);
  }

  return { batchItemFailures: failures };
};
```

---

## 5. OpenAPI con SAM

### template.yaml con definición OpenAPI

```yaml
Resources:
  ApiGateway:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      DefinitionBody:
        openapi: "3.0.0"
        info:
          title: Customer API
          version: "2.0.0"
        paths:
          /v2/customers:
            get:
              summary: List customers
              parameters:
                - name: page
                  in: query
                  schema: { type: integer, minimum: 0 }
                - name: size
                  in: query
                  schema: { type: integer, minimum: 1, maximum: 100 }
              responses:
                "200":
                  description: Success
              x-amazon-apigateway-integration:
                type: aws_proxy
                httpMethod: POST
                uri: !Sub "arn:aws:apigateway:${AWS::Region}:lambda:path/2015-03-31/functions/${ListCustomersFunction.Arn}/invocations"
```

---

## Reglas Importantes para Lambda API Design

- **Content-Type**: Usar `application/problem+json` para errores RFC 7807
- **Error wrapper**: Usar `withErrorHandling` para centralizar manejo de errores en todos los handlers
- **Paginación**: Incluir metadata y links HATEOAS en respuestas de listado
- **Versionamiento**: Usar path-based (`/v1/`, `/v2/`) con funciones Lambda separadas por versión
- **Deprecation headers**: Marcar versiones deprecated con `Deprecation`, `Sunset` y `Link`
- **Validación**: Validar con Zod antes de invocar use case; retornar errores RFC 7807
- **Trace ID**: Usar `event.requestContext.requestId` como trace ID
- **CORS**: Configurar headers CORS en cada respuesta o en API Gateway
- **AsyncAPI**: Validar mensajes con Ajv antes de procesar; enviar a DLQ si inválidos
- **OpenAPI**: Definir spec en `template.yaml` para validación automática en API Gateway
