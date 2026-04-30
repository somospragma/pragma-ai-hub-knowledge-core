<!-- keywords: data masking, tokenization, pii, pci, sensitive data, decorators, express middleware, typescript, nodejs -->
# Data Masking and Tokenization - TypeScript Implementation

## Purpose

Implement PII/PCI data masking in Node.js/TypeScript using decorators, Express middleware, and configurable strategies.

## Scope of Application

- When developing Node.js services that handle sensitive data.
- When masking middleware for Express is needed.
- To configure masking decorators in classes.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "reflect-metadata": "^0.1.13",
    "express": "^4.18.0"
  }
}
```

### Implementation

```typescript
// Masking service
type DataType = 'PAN' | 'EMAIL' | 'PHONE' | 'SSN' | 'NAME';

export class DataMaskingService {
  private strategies: Map<DataType, (value: string) => string>;

  constructor() {
    this.strategies = new Map([
      ['PAN', this.maskPan.bind(this)],
      ['EMAIL', this.maskEmail.bind(this)],
      ['PHONE', this.maskPhone.bind(this)],
      ['SSN', this.maskSsn.bind(this)],
      ['NAME', this.maskName.bind(this)]
    ]);
  }

  mask(value: string | null | undefined, type: DataType): string {
    if (!value) return '';
    const strategy = this.strategies.get(type);
    return strategy ? strategy(value) : value;
  }

  maskObject<T extends object>(obj: T, fields: Record<keyof T, DataType>): T {
    const masked = { ...obj };
    for (const [field, type] of Object.entries(fields)) {
      if (field in masked && typeof masked[field as keyof T] === 'string') {
        (masked as any)[field] = this.mask(
          masked[field as keyof T] as string, 
          type as DataType
        );
      }
    }
    return masked;
  }

  private maskPan(pan: string): string {
    if (pan.length < 4) return '****';
    return '*'.repeat(pan.length - 4) + pan.slice(-4);
  }

  private maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (!domain || local.length <= 2) return `***@${domain || '***'}`;
    return `${local[0]}***${local[local.length - 1]}@${domain}`;
  }

  private maskPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 4) return '****';
    return `***-***-${digits.slice(-4)}`;
  }

  private maskSsn(ssn: string): string {
    const digits = ssn.replace(/\D/g, '');
    if (digits.length < 4) return '***-**-****';
    return `***-**-${digits.slice(-4)}`;
  }

  private maskName(name: string): string {
    const parts = name.split(' ');
    return parts.map(part => 
      part.length <= 2 ? part : `${part[0]}${'*'.repeat(part.length - 1)}`
    ).join(' ');
  }
}
```

```typescript
// Decorator for masking in classes
import 'reflect-metadata';

const MASKED_METADATA_KEY = Symbol('masked');

export function Masked(type: DataType, options?: { inResponse?: boolean; inLogs?: boolean }) {
  return function (target: any, propertyKey: string) {
    const existingMasked = Reflect.getMetadata(MASKED_METADATA_KEY, target) || {};
    existingMasked[propertyKey] = { type, ...options };
    Reflect.defineMetadata(MASKED_METADATA_KEY, existingMasked, target);
  };
}

// Usage
class CustomerDto {
  id: string;
  name: string;

  @Masked('EMAIL', { inResponse: true })
  email: string;

  @Masked('PHONE', { inResponse: true })
  phone: string;

  @Masked('PAN', { inResponse: true, inLogs: true })
  cardNumber: string;
}
```

```typescript
// Masking middleware for Express
import { Request, Response, NextFunction } from 'express';

export function maskingMiddleware(maskingService: DataMaskingService) {
  return (req: Request, res: Response, next: NextFunction) => {
    const originalJson = res.json.bind(res);

    res.json = (body: any) => {
      const maskedBody = maskResponseBody(body, maskingService);
      return originalJson(maskedBody);
    };

    next();
  };
}
```

### Configuration

```typescript
export const maskingConfig = {
  enabled: true,
  defaultMaskChar: '*',
  types: {
    pan: { showLast: 4 },
    email: { showFirst: 1, showLast: 1 },
    phone: { showLast: 4 }
  }
};
```

## Important Rules

- Use decorators to declare maskable fields.
- Implement middleware for automatic masking in responses.
- Consider context (logs vs response) when masking.

## Example

```typescript
const maskingService = new DataMaskingService();

const customer = {
  id: '123',
  email: 'john.doe@example.com',
  phone: '+1-555-123-4567',
  cardNumber: '4111111111111111'
};

const masked = maskingService.maskObject(customer, {
  email: 'EMAIL',
  phone: 'PHONE',
  cardNumber: 'PAN'
});
// { id: '123', email: 'j***e@example.com', phone: '***-***-4567', cardNumber: '************1111' }
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
