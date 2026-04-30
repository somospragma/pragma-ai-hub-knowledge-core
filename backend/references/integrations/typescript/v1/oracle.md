<!-- keywords: oracle, database, node-oracledb, typescript, nodejs -->
# Oracle Database Integration - TypeScript

## Purpose

Implement integration with Oracle Database in TypeScript using node-oracledb.

## Scope of Application

- Node.js/TypeScript projects that require Oracle
- Implementation with Express, Fastify, or NestJS
- Working with stored procedures

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "oracledb": "^6.0.0"
  }
}
```

### Client with Connection Pool

```typescript
import oracledb from 'oracledb';

interface OracleConfig {
  user: string;
  password: string;
  connectString: string;
  poolMin: number;
  poolMax: number;
}

class OracleConnectionManager {
  private pool: oracledb.Pool | null = null;
  
  async initialize(config: OracleConfig): Promise<void> {
    oracledb.outFormat = oracledb.OUT_FORMAT_OBJECT;
    oracledb.autoCommit = false;
    
    this.pool = await oracledb.createPool({
      user: config.user,
      password: config.password,
      connectString: config.connectString,
      poolMin: config.poolMin,
      poolMax: config.poolMax,
      poolTimeout: 60,
      queueTimeout: 30000
    });
  }
  
  async getConnection(): Promise<oracledb.Connection> {
    if (!this.pool) throw new Error('Pool not initialized');
    return this.pool.getConnection();
  }
  
  async close(): Promise<void> {
    if (this.pool) await this.pool.close(10);
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
}

class CustomerRepository {
  constructor(private connectionManager: OracleConnectionManager) {}
  
  async findById(customerId: string): Promise<Customer | null> {
    const connection = await this.connectionManager.getConnection();
    
    try {
      const result = await connection.execute<Customer>(
        `SELECT customer_id AS "customerId", name, email, status
         FROM customers WHERE customer_id = :customerId`,
        { customerId },
        { outFormat: oracledb.OUT_FORMAT_OBJECT }
      );
      
      return result.rows?.[0] || null;
    } finally {
      await connection.close();
    }
  }
  
  async callStoredProcedure(status: string): Promise<Customer[]> {
    const connection = await this.connectionManager.getConnection();
    
    try {
      const result = await connection.execute(
        `BEGIN CUSTOMER_PKG.GET_CUSTOMERS_BY_STATUS(:p_status, :p_cursor); END;`,
        {
          p_status: status,
          p_cursor: { type: oracledb.CURSOR, dir: oracledb.BIND_OUT }
        }
      );
      
      const cursor = result.outBinds.p_cursor;
      const customers: Customer[] = [];
      let row;
      
      while ((row = await cursor.getRow())) {
        customers.push(row as Customer);
      }
      
      await cursor.close();
      return customers;
    } finally {
      await connection.close();
    }
  }
  
  async saveWithTransaction(customer: Customer): Promise<void> {
    const connection = await this.connectionManager.getConnection();
    
    try {
      await connection.execute(
        `INSERT INTO customers (customer_id, name, email, status, created_date)
         VALUES (:customerId, :name, :email, :status, SYSDATE)`,
        customer
      );
      await connection.commit();
    } catch (error) {
      await connection.rollback();
      throw error;
    } finally {
      await connection.close();
    }
  }
}
```

## Important Rules

- Use connection pooling with createPool
- Close REF CURSOR cursors after use
- Use bind variables to prevent SQL injection
- Handle transactions explicitly

## Example

```typescript
const oracle = new OracleConnectionManager();
await oracle.initialize({
  user: process.env.ORACLE_USER!,
  password: process.env.ORACLE_PASSWORD!,
  connectString: process.env.ORACLE_CONNECT_STRING!,
  poolMin: 2,
  poolMax: 10
});

const repo = new CustomerRepository(oracle);
const customer = await repo.findById('123');
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
