<!-- keywords: input validation, zod, schema validation, sanitization, typescript -->
# Input Validation — TypeScript Implementation

## Purpose

Implementation guide for input validation in TypeScript using Zod, with functional examples.

## Libraries and dependencies

```json
{
  "dependencies": {
    "zod": "^3.22.4",
    "isomorphic-dompurify": "^1.9.0",
    "validator": "^13.11.0"
  },
  "devDependencies": {
    "@types/validator": "^13.11.0"
  }
}
```

## Step by Step / Guidelines

### Validation schemas with Zod

```typescript
import { z } from 'zod';

const phoneRegex = /^\+?[1-9]\d{1,14}$/;
const currencyRegex = /^[A-Z]{3}$/;

export const OrderItemSchema = z.object({
  productId: z.string()
    .min(1, 'Product ID is required')
    .max(50, 'Product ID too long')
    .regex(/^[a-zA-Z0-9-]+$/, 'Invalid product ID format'),
  
  quantity: z.number()
    .int('Quantity must be integer')
    .min(1, 'Quantity must be at least 1')
    .max(1000, 'Quantity cannot exceed 1000'),
  
  unitPrice: z.number()
    .positive('Price must be positive')
    .max(999999.99, 'Price exceeds maximum')
    .transform(val => Math.round(val * 100) / 100)
});

```typescript
export const OrderRequestSchema = z.object({
  customerId: z.string()
    .min(1, 'Customer ID is required')
    .max(50)
    .regex(/^[a-zA-Z0-9-]+$/, 'Invalid customer ID format'),
  
  items: z.array(OrderItemSchema)
    .min(1, 'Order must have at least 1 item')
    .max(100, 'Order cannot have more than 100 items'),
  
  currency: z.string()
    .regex(currencyRegex, 'Currency must be 3-letter ISO code'),
  
  notificationEmail: z.string()
    .email('Invalid email format')
    .optional(),
  
  phoneNumber: z.string()
    .regex(phoneRegex, 'Invalid phone number')
    .optional(),
  
  deliveryDate: z.string()
    .datetime()
    .refine(date => new Date(date) > new Date(), {
      message: 'Delivery date must be in the future'
    })
    .optional()
});

export type OrderRequest = z.infer<typeof OrderRequestSchema>;
```

### Validation middleware

```typescript
import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';

export function validate<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        const errors = error.errors.map(e => ({
          field: e.path.join('.'),
          message: e.message
        }));
        
        res.status(400).json({
          type: 'https://api.company.com/errors/validation-error',
          title: 'Validation Error',
          status: 400,
          detail: 'Request validation failed',
          errors
        });
      } else {
        next(error);
      }
    }
  };
}

// Usage in router
router.post('/orders', validate(OrderRequestSchema), orderController.create);
```

### Sanitization

```typescript
import DOMPurify from 'isomorphic-dompurify';
import validator from 'validator';

export function sanitizeHtml(input: string): string {
  return DOMPurify.sanitize(input, {
    ALLOWED_TAGS: ['b', 'i', 'u', 'br'],
    ALLOWED_ATTR: []
  });
}

export function sanitizeForLog(input: string): string {
  return input
    .replace(/[\r\n]/g, ' ')
    .replace(/[^\x20-\x7E]/g, '');
}

export function escapeHtml(input: string): string {
  return validator.escape(input);
}
```

## Mocks and fixtures

### Validation test

```typescript
describe('OrderRequestSchema', () => {
  it('should validate valid request', () => {
    const validRequest = {
      customerId: 'cust-123',
      items: [{ productId: 'prod-1', quantity: 2, unitPrice: 25.00 }],
      currency: 'USD'
    };

    const result = OrderRequestSchema.safeParse(validRequest);
    expect(result.success).toBe(true);
  });

  it('should reject invalid request', () => {
    const invalidRequest = {
      customerId: '',
      items: [],
      currency: 'INVALID'
    };

    const result = OrderRequestSchema.safeParse(invalidRequest);
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.errors.length).toBeGreaterThan(0);
    }
  });
});
```

## Scope of Application

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
