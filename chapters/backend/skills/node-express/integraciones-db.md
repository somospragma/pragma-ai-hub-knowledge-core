---
id: backend-skill-node-express-integraciones-db
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Integraciones con Bases de Datos — Node Express

## Propósito

Guía de implementación para integrar bases de datos en microservicios Node.js/Express con TypeScript: PostgreSQL (pg), MongoDB (driver nativo), DynamoDB (AWS SDK v3), SQL Server (mssql) y Oracle (node-oracledb).

---

## 1. PostgreSQL con pg

### Dependencias

```json
{
  "dependencies": {
    "pg": "^8.11.0",
    "@types/pg": "^8.10.0"
  }
}
```

### Cliente con Connection Pool

```typescript
import { Pool, PoolConfig } from 'pg';

export class PostgresClient {
  private pool: Pool;

  constructor(config: { host: string; port: number; database: string; user: string; password: string; ssl?: boolean }) {
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
    this.pool.on('error', (err) => console.error('Pool error:', err));
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

### Repositorio CRUD

```typescript
export class CustomerRepository {
  constructor(private db: PostgresClient) {}

  async findById(id: string): Promise<Customer | null> {
    return this.db.queryOne<Customer>(
      'SELECT id, name, email, status, created_at as "createdAt" FROM customers WHERE id = $1',
      [id]
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
}
```

### Manejo de errores

```typescript
import { DatabaseError } from 'pg';

async createCustomer(data: CreateCustomerDto): Promise<Customer> {
  try {
    return await this.repo.create(data);
  } catch (error) {
    if (error instanceof DatabaseError) {
      if (error.code === '23505') throw new ConflictError('Customer already exists');
      if (error.code === '23503') throw new BadRequestError('Invalid reference');
    }
    throw error;
  }
}
```

---

## 2. MongoDB con Driver Nativo

### Dependencias

```json
{
  "dependencies": {
    "mongodb": "^6.0.0"
  }
}
```

### Cliente con Connection Pool

```typescript
import { MongoClient, Db, Collection } from 'mongodb';

export class MongoConnectionManager {
  private client: MongoClient | null = null;
  private db: Db | null = null;

  async connect(config: { uri: string; database: string }): Promise<void> {
    this.client = new MongoClient(config.uri, {
      maxPoolSize: 50,
      minPoolSize: 5,
      maxIdleTimeMS: 60000,
      retryWrites: true,
      retryReads: true
    });
    await this.client.connect();
    this.db = this.client.db(config.database);
  }

  getCollection<T>(name: string): Collection<T> {
    if (!this.db) throw new Error('Database not connected');
    return this.db.collection<T>(name);
  }

  async close(): Promise<void> {
    if (this.client) await this.client.close();
  }
}
```

### Repositorio con Aggregations

```typescript
export class CustomerRepository {
  private collection: Collection<Customer>;

  constructor(connectionManager: MongoConnectionManager) {
    this.collection = connectionManager.getCollection<Customer>('customers');
  }

  async findById(customerId: string): Promise<Customer | null> {
    return this.collection.findOne({ customerId });
  }

  async upsert(customer: Customer): Promise<Customer> {
    const result = await this.collection.findOneAndUpdate(
      { customerId: customer.customerId },
      { $set: { name: customer.name, email: customer.email, status: customer.status },
        $setOnInsert: { createdDate: new Date() } },
      { upsert: true, returnDocument: 'after' }
    );
    return result!;
  }

  async aggregateByStatus(): Promise<{ _id: string; count: number }[]> {
    return this.collection.aggregate([
      { $group: { _id: '$status', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]).toArray();
  }

  async createIndexes(): Promise<void> {
    await this.collection.createIndexes([
      { key: { customerId: 1 }, unique: true },
      { key: { email: 1 } },
      { key: { status: 1, createdDate: -1 } }
    ]);
  }
}
```

---

## 3. DynamoDB con AWS SDK v3

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.400.0",
    "@aws-sdk/lib-dynamodb": "^3.400.0"
  }
}
```

### Cliente DocumentClient

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand, QueryCommand, TransactWriteCommand } from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
```

### Repositorio con Single-Table Design

```typescript
export class CustomerRepository {
  constructor(private tableName: string) {}

  async findById(customerId: string): Promise<Customer | null> {
    const command = new GetCommand({
      TableName: this.tableName,
      Key: { pk: `CUSTOMER#${customerId}`, sk: 'PROFILE' }
    });
    const response = await docClient.send(command);
    return response.Item as Customer || null;
  }

  async findByStatus(status: string): Promise<Customer[]> {
    const command = new QueryCommand({
      TableName: this.tableName,
      IndexName: 'GSI1',
      KeyConditionExpression: 'gsi1pk = :status',
      ExpressionAttributeValues: { ':status': `STATUS#${status}` }
    });
    const response = await docClient.send(command);
    return response.Items as Customer[] || [];
  }

  async create(customer: Omit<Customer, 'pk' | 'sk'>): Promise<Customer> {
    const id = crypto.randomUUID();
    const item: Customer = {
      pk: `CUSTOMER#${id}`, sk: 'PROFILE',
      ...customer,
      gsi1pk: `STATUS#${customer.status}`,
      gsi1sk: new Date().toISOString()
    };
    const command = new PutCommand({
      TableName: this.tableName,
      Item: item,
      ConditionExpression: 'attribute_not_exists(pk)'
    });
    await docClient.send(command);
    return item;
  }
}
```

### Transacciones

```typescript
async createOrderWithItems(customerId: string, items: OrderItem[]): Promise<string> {
  const orderId = crypto.randomUUID();
  const transactItems = [
    { Put: { TableName: this.tableName, Item: { pk: `ORDER#${orderId}`, sk: 'METADATA', customerId, status: 'PENDING' }, ConditionExpression: 'attribute_not_exists(pk)' } },
    ...items.map((item, i) => ({ Put: { TableName: this.tableName, Item: { pk: `ORDER#${orderId}`, sk: `ITEM#${i}`, ...item } } }))
  ];
  await docClient.send(new TransactWriteCommand({ TransactItems: transactItems }));
  return orderId;
}
```

---

## 4. SQL Server con mssql

### Dependencias

```json
{
  "dependencies": {
    "mssql": "^10.0.0"
  }
}
```

### Cliente con Connection Pool

```typescript
import sql from 'mssql';

export class SqlServerConnectionManager {
  private pool: sql.ConnectionPool | null = null;

  async initialize(config: sql.config): Promise<void> {
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

### Repositorio con parámetros tipados

```typescript
export class CustomerRepository {
  constructor(private connectionManager: SqlServerConnectionManager) {}

  async findById(customerId: string): Promise<Customer | null> {
    const pool = this.connectionManager.getPool();
    const result = await pool.request()
      .input('customerId', sql.VarChar(50), customerId)
      .query<Customer>(`SELECT customer_id AS customerId, name, email, status FROM customers WHERE customer_id = @customerId`);
    return result.recordset[0] || null;
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
        .query(`INSERT INTO customers (customer_id, name, email, status) VALUES (@customerId, @name, @email, @status)`);
      await transaction.commit();
    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }
}
```

---

## 5. Oracle con node-oracledb

### Dependencias

```json
{
  "dependencies": {
    "oracledb": "^6.0.0"
  }
}
```

### Cliente con Connection Pool

```typescript
import oracledb from 'oracledb';

export class OracleConnectionManager {
  private pool: oracledb.Pool | null = null;

  async initialize(config: { user: string; password: string; connectString: string; poolMin: number; poolMax: number }): Promise<void> {
    oracledb.outFormat = oracledb.OUT_FORMAT_OBJECT;
    oracledb.autoCommit = false;
    this.pool = await oracledb.createPool({
      user: config.user, password: config.password,
      connectString: config.connectString,
      poolMin: config.poolMin, poolMax: config.poolMax,
      poolTimeout: 60, queueTimeout: 30000
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

### Stored Procedures

```typescript
async callStoredProcedure(status: string): Promise<Customer[]> {
  const connection = await this.connectionManager.getConnection();
  try {
    const result = await connection.execute(
      `BEGIN CUSTOMER_PKG.GET_CUSTOMERS_BY_STATUS(:p_status, :p_cursor); END;`,
      { p_status: status, p_cursor: { type: oracledb.CURSOR, dir: oracledb.BIND_OUT } }
    );
    const cursor = result.outBinds.p_cursor;
    const customers: Customer[] = [];
    let row;
    while ((row = await cursor.getRow())) { customers.push(row as Customer); }
    await cursor.close();
    return customers;
  } finally {
    await connection.close();
  }
}
```

---

## Reglas Importantes

- **Connection pooling**: Siempre usar Pool, nunca conexiones directas
- **Timeouts**: Configurar `connectionTimeoutMillis` e `idleTimeoutMillis`
- **Prepared statements**: Usar parámetros (`$1`, `@param`, `:param`) para prevenir SQL injection
- **Transacciones**: Usar BEGIN/COMMIT/ROLLBACK para operaciones atómicas
- **DynamoDB**: Usar DocumentClient para serialización automática
- **Graceful shutdown**: Cerrar pools en `SIGTERM`

```typescript
process.on('SIGTERM', async () => {
  await db.close();
  process.exit(0);
});
```
