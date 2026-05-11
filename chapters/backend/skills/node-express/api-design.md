---
id: backend-skill-node-express-api-design
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Diseño de APIs — Node Express

## Propósito

Guía de implementación de diseño de APIs REST en microservicios Node.js/Express con TypeScript: estándares REST, error handling RFC 7807, versionamiento, OpenAPI y AsyncAPI.

---

## 1. REST Standards con Express

### Controller con validación

```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { body, query, param, validationResult } from 'express-validator';

const router = Router();

const validate = (req: Request, res: Response, next: NextFunction) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      type: 'https://api.example.com/errors/validation',
      title: 'Validation Error',
      status: 400,
      errors: errors.array()
    });
  }
  next();
};

// GET /customers — Listado con paginación
router.get('/',
  [query('page').optional().isInt({ min: 0 }), query('size').optional().isInt({ min: 1, max: 100 }), query('status').optional().isIn(['ACTIVE', 'INACTIVE']), validate],
  async (req: Request, res: Response) => {
    const page = parseInt(req.query.page as string) || 0;
    const size = parseInt(req.query.size as string) || 20;
    const result = await customerService.findAll({ page, size, status: req.query.status as string });

    res.json({
      data: result.items,
      pagination: { page, pageSize: size, totalItems: result.total, totalPages: Math.ceil(result.total / size) },
      _links: buildPaginationLinks(req, page, size, result.total)
    });
  }
);

// GET /customers/:id — Detalle
router.get('/:id',
  [param('id').notEmpty(), validate],
  async (req: Request, res: Response) => {
    const customer = await customerService.findById(req.params.id);
    if (!customer) {
      return res.status(404).json({
        type: 'https://api.example.com/errors/not-found',
        title: 'Customer Not Found',
        status: 404,
        detail: `Customer with id ${req.params.id} not found`
      });
    }
    res.json(customer);
  }
);

// POST /customers — Creación
router.post('/',
  [body('name').notEmpty().isLength({ max: 100 }), body('email').isEmail(), body('phone').optional().matches(/^\+?[1-9]\d{1,14}$/), validate],
  async (req: Request, res: Response) => {
    const customer = await customerService.create(req.body);
    res.status(201).location(`/api/v1/customers/${customer.id}`).json(customer);
  }
);
```

### Estructura de respuesta estándar

```typescript
// Respuesta exitosa con paginación
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
  _links?: {
    self: string;
    next?: string;
    prev?: string;
    first: string;
    last: string;
  };
}

// Helper para links de paginación
function buildPaginationLinks(req: Request, page: number, size: number, total: number) {
  const baseUrl = `${req.protocol}://${req.get('host')}${req.baseUrl}${req.path}`;
  const totalPages = Math.ceil(total / size);
  return {
    self: `${baseUrl}?page=${page}&size=${size}`,
    first: `${baseUrl}?page=0&size=${size}`,
    last: `${baseUrl}?page=${totalPages - 1}&size=${size}`,
    ...(page > 0 && { prev: `${baseUrl}?page=${page - 1}&size=${size}` }),
    ...(page < totalPages - 1 && { next: `${baseUrl}?page=${page + 1}&size=${size}` })
  };
}
```

---

## 2. Error Handling RFC 7807

### Modelo de error

```typescript
interface ProblemDetail {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  traceId?: string;
  timestamp: string;
  errors?: FieldError[];
}

interface FieldError {
  field: string;
  message: string;
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
```

### Builder de ProblemDetail

```typescript
class ProblemDetailBuilder {
  private problem: Partial<ProblemDetail> = { timestamp: new Date().toISOString() };

  type(errorType: ErrorType): this {
    this.problem.type = `https://api.example.com/errors/${errorType}`;
    this.problem.title = ERROR_CONFIG[errorType].title;
    this.problem.status = ERROR_CONFIG[errorType].status;
    return this;
  }
  detail(detail: string): this { this.problem.detail = detail; return this; }
  instance(instance: string): this { this.problem.instance = instance; return this; }
  traceId(traceId: string): this { this.problem.traceId = traceId; return this; }
  addError(field: string, message: string): this {
    if (!this.problem.errors) this.problem.errors = [];
    this.problem.errors.push({ field, message });
    return this;
  }
  build(): ProblemDetail { return this.problem as ProblemDetail; }
}
```

### Excepciones personalizadas

```typescript
class AppError extends Error {
  constructor(public errorType: ErrorType, public detail: string, public errors?: FieldError[]) {
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
  constructor(errors: FieldError[]) {
    super(ErrorType.VALIDATION_ERROR, 'Request validation failed', errors);
  }
}
```

### Middleware de error handling

```typescript
import { Request, Response, NextFunction } from 'express';

export function errorHandler(err: Error, req: Request, res: Response, next: NextFunction): void {
  const traceId = req.headers['x-trace-id'] as string;

  if (err instanceof AppError) {
    const builder = new ProblemDetailBuilder()
      .type(err.errorType)
      .detail(err.detail)
      .instance(req.path);
    if (traceId) builder.traceId(traceId);
    err.errors?.forEach(e => builder.addError(e.field, e.message));
    const problem = builder.build();
    res.status(problem.status).contentType('application/problem+json').json(problem);
    return;
  }

  console.error('Unexpected error:', err);
  const problem = new ProblemDetailBuilder()
    .type(ErrorType.INTERNAL_ERROR)
    .detail('An unexpected error occurred')
    .instance(req.path)
    .build();
  res.status(500).contentType('application/problem+json').json(problem);
}

// Registrar al final de las rutas
app.use(errorHandler);
```

---

## 3. Versionamiento de API

### Middleware de extracción de versión

```typescript
import { Router, Request, Response, NextFunction } from 'express';

interface VersionedRequest extends Request {
  apiVersion: number;
}

export function versionMiddleware(req: VersionedRequest, res: Response, next: NextFunction) {
  const pathMatch = req.path.match(/^\/v(\d+)\//);
  if (pathMatch) { req.apiVersion = parseInt(pathMatch[1]); return next(); }
  const headerVersion = req.header('Api-Version');
  if (headerVersion) { req.apiVersion = parseInt(headerVersion); return next(); }
  req.apiVersion = 2; // Default a última versión
  next();
}
```

### Routers versionados

```typescript
const v1Router = Router();
const v2Router = Router();

// V1 (deprecated)
v1Router.get('/orders', (req: Request, res: Response) => {
  res.set({
    'Deprecation': 'true',
    'Sunset': 'Sat, 01 Jun 2025 00:00:00 GMT',
    'Link': '</v2/orders>; rel="successor-version"'
  });
  const orders = orderService.listOrdersV1();
  res.json(orders);
});

// V2 (current)
v2Router.get('/orders', async (req: Request, res: Response) => {
  const { page = 0, size = 20 } = req.query;
  const orders = await orderService.listOrdersV2(Number(page), Number(size));
  res.json(orders);
});

app.use('/v1', v1Router);
app.use('/v2', v2Router);
```

---

## 4. AsyncAPI — Validación de Mensajes

### Dependencias

```json
{
  "dependencies": {
    "ajv": "^8.12.0",
    "ajv-formats": "^2.1.1"
  }
}
```

### Validador de mensajes

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
      required: ['orderId', 'customerId', 'items', 'totalAmount'],
      properties: {
        orderId: { type: 'string' },
        customerId: { type: 'string' },
        items: { type: 'array', items: { type: 'object', required: ['productId', 'quantity', 'unitPrice'] } },
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
```

---

## 5. OpenAPI — Documentación

### Configuración con swagger-jsdoc

```json
{
  "dependencies": {
    "swagger-jsdoc": "^6.2.8",
    "swagger-ui-express": "^5.0.0"
  }
}
```

```typescript
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

const options = {
  definition: {
    openapi: '3.0.0',
    info: { title: 'Customer API', version: '2.0.0', description: 'API de gestión de clientes' },
    servers: [{ url: '/api/v2' }]
  },
  apis: ['./src/routes/*.ts']
};

const specs = swaggerJsdoc(options);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(specs));
```

---

## Reglas Importantes

- **Content-Type**: Usar `application/problem+json` para errores RFC 7807
- **Paginación**: Siempre incluir metadata de paginación y links HATEOAS
- **Versionamiento**: Preferir URL path (`/v1/`, `/v2/`); marcar versiones deprecated con headers `Deprecation` y `Sunset`
- **Validación**: Usar `express-validator` o Zod en middleware antes del controller
- **Trace ID**: Propagar `x-trace-id` desde headers para correlación
- **Status codes**: 201 para creación con header `Location`, 204 para delete, 404 para not found
- **AsyncAPI**: Validar mensajes con Ajv antes de procesar eventos
