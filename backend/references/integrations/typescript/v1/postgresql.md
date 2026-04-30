<!-- keywords: postgresql, pg, connection pooling, database, typescript, nodejs -->
# PostgreSQL Integration - TypeScript

## Purpose

Implement integration with PostgreSQL in TypeScript/Node.js using the pg client with connection pooling.

## Scope of Application

- Node.js/TypeScript projects that require PostgreSQL
- Implementation with Express, Fastify, or NestJS
- Serverless applications with Lambda

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "pg": "^8.11.0",
    "@types/pg": "^8.10.0"
  }
}
```

### Client with Connection Pool

```typescript
import { Pool, PoolConfig, QueryResult } from 'pg';

interface DatabaseConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
  ssl?: boolean;
}

export class PostgresClient {
  private pool: Pool;

  constructor(config: DatabaseConfig) {
    const poolConfig: PoolConfig = {
      host: config.host,
      port: config.port,
      database: config.database,
      user: config.user,
      password: config.password,
      ssl: config.ssl ? { rejectUnauthorized: false } : undefined,
      max: 20,
      min: 5,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000
    };

    this.pool = new Pool(poolConfig);

    this.pool.on('error', (err) => {
      console.error('Unexpected pool error:', err);
    });
  }

  async query<T>(sql: string, params?: any[]): Promise<T[]> {
    const result = await this.pool.query(sql, params);
    return result.rows as T[];
  }

  async queryOne<T>(sql: string, params?: any[]): Promise<T | null> {
    const rows = await this.query<T>(sql, params);
    return rows[0] || null;
  }

  async transaction<T>(callback: (client: any) => Promise<T>): Promise<T> {
    const client = await this.pool.connect();
    
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async close(): Promise<void> {
    await this.pool.end();
  }
}
```

### CRUD Operations

```typescript
interface Customer {
  id: string;
  name: string;
  email: string;
  status: string;
  createdAt: Date;
}

export class CustomerRepository {
  constructor(private db: PostgresClient) {}

  async findById(id: string): Promise<Customer | null> {
    return this.db.queryOne<Customer>(
      'SELECT id, name, email, status, created_at as "createdAt" FROM customers WHERE id = $1',
      [id]
    );
  }

  async findByStatus(status: string): Promise<Customer[]> {
    return this.db.query<Customer>(
      'SELECT id, name, email, status, created_at as "createdAt" FROM customers WHERE status = $1',
      [status]
    );
  }

  async create(customer: Omit<Customer, 'id' | 'createdAt'>): Promise<Customer> {
    const result = await this.db.query<Customer>(
      `INSERT INTO customers (id, name, email, status, created_at) 
       VALUES (gen_random_uuid(), $1, $2, $3, NOW()) 
       RETURNING id, name, email, status, created_at as "createdAt"`,
      [customer.name, customer.email, customer.status]
    );
    return result[0];
  }

  async update(id: string, updates: Partial<Customer>): Promise<Customer | null> {
    const fields: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    if (updates.name) {
      fields.push(`name = ${paramIndex++}`);
      values.push(updates.name);
    }
    if (updates.email) {
      fields.push(`email = ${paramIndex++}`);
      values.push(updates.email);
    }
    if (updates.status) {
      fields.push(`status = ${paramIndex++}`);
      values.push(updates.status);
    }

    values.push(id);

    const result = await this.db.query<Customer>(
      `UPDATE customers SET ${fields.join(', ')} 
       WHERE id = ${paramIndex} 
       RETURNING id, name, email, status, created_at as "createdAt"`,
      values
    );
    return result[0] || null;
  }

  async delete(id: string): Promise<boolean> {
    const result = await this.db.query(
      'DELETE FROM customers WHERE id = $1 RETURNING id',
      [id]
    );
    return result.length > 0;
  }
}
```

### Transactions

```typescript
async createWithOrder(
  customer: Omit<Customer, 'id' | 'createdAt'>
): Promise<Customer> {
  return this.db.transaction(async (client) => {
    const customerResult = await client.query(
      `INSERT INTO customers (id, name, email, status, created_at) 
       VALUES (gen_random_uuid(), $1, $2, $3, NOW()) 
       RETURNING *`,
      [customer.name, customer.email, customer.status]
    );
    
    const newCustomer = customerResult.rows[0];
    
    await client.query(
      `INSERT INTO orders (id, customer_id, amount, status) 
       VALUES (gen_random_uuid(), $1, 0, 'PENDING')`,
      [newCustomer.id]
    );
    
    return newCustomer;
  });
}
```

### Error handling

```typescript
import { DatabaseError } from 'pg';

export class CustomerService {
  constructor(private repo: CustomerRepository) {}

  async createCustomer(data: CreateCustomerDto): Promise<Customer> {
    try {
      return await this.repo.create(data);
    } catch (error) {
      if (error instanceof DatabaseError) {
        if (error.code === '23505') { // unique_violation
          throw new ConflictError('Customer with this email already exists');
        }
        if (error.code === '23503') { // foreign_key_violation
          throw new BadRequestError('Invalid reference');
        }
      }
      throw error;
    }
  }
}
```

## Important Rules

- Connection pooling: Always use Pool, never direct Client
- Timeouts: Configure connectionTimeoutMillis and idleTimeoutMillis
- Prepared statements: Use $1, $2 parameters to prevent SQL injection
- Transactions: Use BEGIN/COMMIT/ROLLBACK for atomic operations

## Example

```typescript
// Full usage with Express
import express from 'express';

const app = express();
const db = new PostgresClient({
  host: process.env.DB_HOST!,
  port: parseInt(process.env.DB_PORT!),
  database: process.env.DB_NAME!,
  user: process.env.DB_USER!,
  password: process.env.DB_PASSWORD!,
  ssl: process.env.DB_SSL === 'true'
});

const customerRepo = new CustomerRepository(db);

app.get('/customers/:id', async (req, res) => {
  const customer = await customerRepo.findById(req.params.id);
  if (!customer) {
    return res.status(404).json({ error: 'Customer not found' });
  }
  res.json(customer);
});

app.post('/customers', async (req, res) => {
  const customer = await customerRepo.create(req.body);
  res.status(201).json(customer);
});

// Cleanup on shutdown
process.on('SIGTERM', async () => {
  await db.close();
  process.exit(0);
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
