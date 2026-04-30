<!-- keywords: rfc7807, error handling, problem details, http error, rest api errors, express, middleware, typescript, nodejs -->
# RFC 7807 Error Handling - TypeScript Implementation

## Purpose

Implement the RFC 7807 standard for error handling in Node.js/TypeScript applications with Express.

## Scope of Application

- When implementing error handling middleware in Express
- When creating consistent error responses in REST APIs
- When integrating validation with RFC 7807 responses

## Main content

### Dependencies

```json
{
  "dependencies": {
    "express": "^4.18.2"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "typescript": "^5.3.0"
  }
}
```

### RFC 7807 Error Model

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

### ProblemDetail Builder

```typescript
class ProblemDetailBuilder {
  private problem: Partial<ProblemDetail> = {
    timestamp: new Date().toISOString(),
    errors: []
  };

  type(errorType: ErrorType): this {
    const config = ERROR_CONFIG[errorType];
    this.problem.type = `https://api.example.com/errors/${errorType}`;
    this.problem.title = config.title;
    this.problem.status = config.status;
    return this;
  }

  detail(detail: string): this {
    this.problem.detail = detail;
    return this;
  }

  instance(instance: string): this {
    this.problem.instance = instance;
    return this;
  }

  traceId(traceId: string): this {
    this.problem.traceId = traceId;
    return this;
  }

  addError(field: string, message: string): this {
    this.problem.errors!.push({ field, message });
    return this;
  }

  build(): ProblemDetail {
    if (!this.problem.errors?.length) {
      delete this.problem.errors;
    }
    return this.problem as ProblemDetail;
  }
}
```

### Custom Exception

```typescript
class AppError extends Error {
  constructor(
    public errorType: ErrorType,
    public detail: string,
    public errors?: FieldError[]
  ) {
    super(detail);
    this.name = 'AppError';
  }
}

class ResourceNotFoundError extends AppError {
  constructor(resourceType: string, resourceId: string) {
    super(
      ErrorType.RESOURCE_NOT_FOUND,
      `${resourceType} with id '${resourceId}' not found`
    );
  }
}

class ValidationError extends AppError {
  constructor(errors: FieldError[]) {
    super(ErrorType.VALIDATION_ERROR, 'Request validation failed', errors);
  }
}
```

### Error Handling Middleware

```typescript
import { Request, Response, NextFunction } from 'express';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const traceId = req.headers['x-trace-id'] as string;

  if (err instanceof AppError) {
    const builder = new ProblemDetailBuilder()
      .type(err.errorType)
      .detail(err.detail)
      .instance(req.path);

    if (traceId) {
      builder.traceId(traceId);
    }

    err.errors?.forEach(e => builder.addError(e.field, e.message));

    const problem = builder.build();

    res
      .status(problem.status)
      .contentType('application/problem+json')
      .json(problem);
    return;
  }

  // Unhandled error
  console.error('Unexpected error:', err);

  const problem = new ProblemDetailBuilder()
    .type(ErrorType.INTERNAL_ERROR)
    .detail('An unexpected error occurred')
    .instance(req.path)
    .traceId(traceId || '')
    .build();

  res
    .status(500)
    .contentType('application/problem+json')
    .json(problem);
}
```

### Express Configuration

```typescript
import express from 'express';

const app = express();

app.use(express.json());

// Routes
app.get('/api/v1/customers/:id', async (req, res, next) => {
  try {
    const customer = await customerService.findById(req.params.id);
    if (!customer) {
      throw new ResourceNotFoundError('Customer', req.params.id);
    }
    res.json(customer);
  } catch (error) {
    next(error);
  }
});

// Error middleware at the end
app.use(errorHandler);
```

## Important Rules

- Use `application/problem+json` as Content-Type
- Propagate traceId from headers for correlation
- Do not expose internal details in production errors
- Use `next(error)` to pass errors to the middleware

## Example

```typescript
// Controller with validation
app.post('/api/v1/customers', async (req, res, next) => {
  try {
    const errors: FieldError[] = [];
    
    if (!req.body.email) {
      errors.push({ field: 'email', message: 'Email is required' });
    }
    if (!req.body.name) {
      errors.push({ field: 'name', message: 'Name is required' });
    }
    
    if (errors.length > 0) {
      throw new ValidationError(errors);
    }
    
    const customer = await customerService.create(req.body);
    res.status(201).json(customer);
  } catch (error) {
    next(error);
  }
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
