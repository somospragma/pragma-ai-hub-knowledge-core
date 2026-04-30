<!-- keywords: rest api, api design, http methods, status codes, resource naming, express, typescript, nodejs -->
# REST Standards — TypeScript Implementation

## Conceptual reference

For the conceptual REST design standards (naming, HTTP methods, status codes, response structure, and OpenAPI), see [`../rest-standards.md`](../rest-standards.md).

## Technology Stack

- **Runtime:** Node.js
- **Framework:** Express
- **Validation:** `express-validator` (`body`, `query`, `param`, `validationResult`)
- **Typing:** TypeScript with Express types (`Request`, `Response`, `NextFunction`)

## Controller with Express

```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { body, query, param, validationResult } from 'express-validator';

const router = Router();

// Validation middleware
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

// GET /customers
router.get(
  '/',
  [
    query('page').optional().isInt({ min: 0 }),
    query('size').optional().isInt({ min: 1, max: 100 }),
    query('status').optional().isIn(['ACTIVE', 'INACTIVE']),
    validate
  ],
  async (req: Request, res: Response) => {
    const page = parseInt(req.query.page as string) || 0;
    const size = parseInt(req.query.size as string) || 20;
    const status = req.query.status as string;

    const result = await customerService.findAll({ page, size, status });

    res.json({
      data: result.items,
      pagination: {
        page,
        pageSize: size,
        totalItems: result.total,
        totalPages: Math.ceil(result.total / size)
      },
      _links: buildPaginationLinks(req, page, size, result.total)
    });
  }
);

// GET /customers/:id
router.get(
  '/:id',
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

// POST /customers
router.post(
  '/',
  [
    body('name').notEmpty().isLength({ max: 100 }),
    body('email').isEmail(),
    body('phone').optional().matches(/^\+?[1-9]\d{1,14}$/),
    validate
  ],
  async (req: Request, res: Response) => {
    const customer = await customerService.create(req.body);

    res
      .status(201)
      .location(`/api/v1/customers/${customer.id}`)
      .json(customer);
  }
);
```

## Tools and Resources

REST standards and best practices from the backend team — TypeScript implementation with Express/Node.js.

## Purpose

_(No additional information required for this section.)_

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_
