<!-- keywords: sqlserver, sql server, mssql, database, microsoft, typescript, nodejs -->
# SQL Server Integration - TypeScript

## Purpose

Implement integration with SQL Server in TypeScript using the mssql package.

## Scope of Application

- Node.js/TypeScript projects that require SQL Server
- Implementation with Express, Fastify, or NestJS

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "mssql": "^10.0.0"
  }
}
```

### Client with Connection Pool

```typescript
import sql from 'mssql';

interface SqlServerConfig {
  server: string;
  database: string;
  user: string;
  password: string;
  port: number;
  options: {
    encrypt: boolean;
    trustServerCertificate: boolean;
  };
  pool: {
    min: number;
    max: number;
    idleTimeoutMillis: number;
  };
}

class SqlServerConnectionManager {
  private pool: sql.ConnectionPool | null = null;
  
  async initialize(config: SqlServerConfig): Promise<void> {
    this.pool = await new sql.ConnectionPool(config).connect();
  }
  
  getPool(): sql.ConnectionPool {
    if (!this.pool) throw new Error('Pool not initialized');
    return this.pool;
  }
  
  async close(): Promise<void> {
    if (this.pool) await this.pool.close();
  }
}
```


### CRUD Operations

```typescript
interface Customer {
  customerId: string;
  name: string;
  email: string;
  status: string;
  createdDate?: Date;
}

class CustomerRepository {
  constructor(private connectionManager: SqlServerConnectionManager) {}
  
  async findById(customerId: string): Promise<Customer | null> {
    const pool = this.connectionManager.getPool();
    
    const result = await pool.request()
      .input('customerId', sql.VarChar(50), customerId)
      .query<Customer>(`
        SELECT customer_id AS customerId, name, email, status, 
               created_date AS createdDate
        FROM customers WHERE customer_id = @customerId
      `);
    
    return result.recordset[0] || null;
  }
  
  async findByStatus(status: string): Promise<Customer[]> {
    const pool = this.connectionManager.getPool();
    
    const result = await pool.request()
      .input('status', sql.VarChar(20), status)
      .query<Customer>(`
        SELECT customer_id AS customerId, name, email, status
        FROM customers WHERE status = @status
        ORDER BY created_date DESC
      `);
    
    return result.recordset;
  }
  
  async saveWithTransaction(customer: Customer): Promise<void> {
    const pool = this.connectionManager.getPool();
    const transaction = new sql.Transaction(pool);
    
    try {
      await transaction.begin();
      
      await new sql.Request(transaction)
        .input('customerId', sql.VarChar(50), customer.customerId)
        .input('name', sql.NVarChar(100), customer.name)
        .input('email', sql.VarChar(255), customer.email)
        .input('status', sql.VarChar(20), customer.status)
        .query(`
          INSERT INTO customers (customer_id, name, email, status, created_date)
          VALUES (@customerId, @name, @email, @status, GETDATE())
        `);
      
      await transaction.commit();
    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }
}
```

## Important Rules

- Use connection pooling with ConnectionPool
- Use typed parameters to prevent SQL injection
- Handle transactions explicitly
- Configure encrypt=true for RDS

## Example

```typescript
const sqlServer = new SqlServerConnectionManager();
await sqlServer.initialize({
  server: process.env.SQL_SERVER!,
  database: process.env.SQL_DATABASE!,
  user: process.env.SQL_USER!,
  password: process.env.SQL_PASSWORD!,
  port: 1433,
  options: { encrypt: true, trustServerCertificate: false },
  pool: { min: 5, max: 20, idleTimeoutMillis: 30000 }
});

const repo = new CustomerRepository(sqlServer);
const customer = await repo.findById('123');
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
