<!-- keywords: api versioning, url versioning, middleware, express routers, version extraction, backward compatibility, typescript, nodejs -->
# API Versioning Strategies - TypeScript Implementation

## Purpose

Implementation of REST API versioning in Node.js/TypeScript with Express, including version extraction middleware and versioned routers.

## Reference

Main language-agnostic document: [../versioning-strategies.md](../versioning-strategies.md)

## Middleware and Versioned Routers

```typescript
// version-middleware.ts
import { Router, Request, Response, NextFunction } from 'express';

interface VersionedRequest extends Request {
  apiVersion: number;
}

// Middleware to extract version
export function versionMiddleware(req: VersionedRequest, res: Response, next: NextFunction) {
  // Extract from URL path
  const pathMatch = req.path.match(/^\/v(\d+)\//);
  if (pathMatch) {
    req.apiVersion = parseInt(pathMatch[1]);
    return next();
  }

  // Extract from header
  const headerVersion = req.header('Api-Version');
  if (headerVersion) {
    req.apiVersion = parseInt(headerVersion);
    return next();
  }

  // Default to latest version
  req.apiVersion = 2;
  next();
}

// Versioned router
const v1Router = Router();
const v2Router = Router();

// V1 Routes (deprecated)
v1Router.get('/orders', (req: Request, res: Response) => {
  res.set({
    'Deprecation': 'true',
    'Sunset': 'Sat, 01 Jun 2024 00:00:00 GMT',
    'Link': '</v2/orders>; rel="successor-version"'
  });

  const orders = orderService.listOrdersV1();
  res.json(orders);
});

// V2 Routes (current)
v2Router.get('/orders', async (req: Request, res: Response) => {
  const { page = 0, size = 20 } = req.query;
  const orders = await orderService.listOrdersV2(Number(page), Number(size));
  res.json(orders);
});

// Mount routers
app.use('/v1', v1Router);
app.use('/v2', v2Router);
```

## Scope of Application

_(No additional information required for this section.)_

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
