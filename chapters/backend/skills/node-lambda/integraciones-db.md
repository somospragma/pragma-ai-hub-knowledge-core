---
id: backend-skill-node-lambda-integraciones-db
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Integraciones con Bases de Datos — Node Lambda

## Propósito

Guía de implementación para integrar bases de datos en funciones Lambda con TypeScript: DynamoDB (single-table design), Aurora Serverless (PostgreSQL), MongoDB y conexiones optimizadas para serverless.

---

## 1. DynamoDB — Single-Table Design

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.400.0",
    "@aws-sdk/lib-dynamodb": "^3.400.0"
  }
}
```

### Cliente (reutilizable entre invocaciones)

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, GetCommand, PutCommand, QueryCommand, TransactWriteCommand, UpdateCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';

// Inicializar FUERA del handler para reutilizar entre invocaciones
const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client, {
  marshallOptions: { removeUndefinedValues: true }
});

const TABLE_NAME = process.env.TABLE_NAME!;
```

### Repositorio con Single-Table Design

```typescript
interface Customer {
  pk: string;
  sk: string;
  customerId: string;
  name: string;
  email: string;
  status: string;
  gsi1pk: string;
  gsi1sk: string;
}

export class CustomerDynamoAdapter implements CustomerGateway {
  async findById(customerId: string): Promise<Customer | null> {
    const response = await docClient.send(new GetCommand({
      TableName: TABLE_NAME,
      Key: { pk: `CUSTOMER#${customerId}`, sk: 'PROFILE' }
    }));
    return response.Item as Customer || null;
  }

  async findByStatus(status: string): Promise<Customer[]> {
    const response = await docClient.send(new QueryCommand({
      TableName: TABLE_NAME,
      IndexName: 'GSI1',
      KeyConditionExpression: 'gsi1pk = :status',
      ExpressionAttributeValues: { ':status': `STATUS#${status}` }
    }));
    return response.Items as Customer[] || [];
  }

  async create(customer: Omit<Customer, 'pk' | 'sk' | 'gsi1pk' | 'gsi1sk'>): Promise<Customer> {
    const id = crypto.randomUUID();
    const item: Customer = {
      pk: `CUSTOMER#${id}`, sk: 'PROFILE',
      customerId: id, ...customer,
      gsi1pk: `STATUS#${customer.status}`,
      gsi1sk: new Date().toISOString()
    };
    await docClient.send(new PutCommand({
      TableName: TABLE_NAME, Item: item,
      ConditionExpression: 'attribute_not_exists(pk)'
    }));
    return item;
  }

  async update(customerId: string, updates: Partial<Customer>): Promise<Customer> {
    const expressions: string[] = [];
    const names: Record<string, string> = {};
    const values: Record<string, any> = {};

    Object.entries(updates).forEach(([key, value], i) => {
      expressions.push(`#f${i} = :v${i}`);
      names[`#f${i}`] = key;
      values[`:v${i}`] = value;
    });

    const response = await docClient.send(new UpdateCommand({
      TableName: TABLE_NAME,
      Key: { pk: `CUSTOMER#${customerId}`, sk: 'PROFILE' },
      UpdateExpression: `SET ${expressions.join(', ')}`,
      ExpressionAttributeNames: names,
      ExpressionAttributeValues: values,
      ReturnValues: 'ALL_NEW'
    }));
    return response.Attributes as Customer;
  }
}
```

### Transacciones DynamoDB

```typescript
async createOrderWithItems(customerId: string, items: Array<{ productId: string; quantity: number; price: number }>): Promise<string> {
  const orderId = crypto.randomUUID();
  const totalAmount = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  const transactItems = [
    {
      Put: {
        TableName: TABLE_NAME,
        Item: { pk: `ORDER#${orderId}`, sk: 'METADATA', customerId, amount: totalAmount, status: 'PENDING', createdAt: new Date().toISOString() },
        ConditionExpression: 'attribute_not_exists(pk)'
      }
    },
    ...items.map((item, index) => ({
      Put: { TableName: TABLE_NAME, Item: { pk: `ORDER#${orderId}`, sk: `ITEM#${index}`, ...item } }
    }))
  ];

  await docClient.send(new TransactWriteCommand({ TransactItems: transactItems }));
  return orderId;
}
```

### Manejo de errores DynamoDB

```typescript
import { ConditionalCheckFailedException, ProvisionedThroughputExceededException } from '@aws-sdk/client-dynamodb';

async create(customer: CustomerInput): Promise<Customer> {
  try {
    return await this.adapter.create(customer);
  } catch (error) {
    if (error instanceof ConditionalCheckFailedException) {
      throw new ConflictError('Customer already exists');
    }
    if (error instanceof ProvisionedThroughputExceededException) {
      // Implementar retry con backoff
      throw new ServiceUnavailableError('Database throttled');
    }
    throw error;
  }
}
```

---

## 2. Aurora Serverless (PostgreSQL)

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-rds-data": "^3.400.0"
  }
}
```

### Cliente con Data API (sin connection pool)

```typescript
import { RDSDataClient, ExecuteStatementCommand, BatchExecuteStatementCommand } from '@aws-sdk/client-rds-data';

// Inicializar fuera del handler
const rdsClient = new RDSDataClient({});
const CLUSTER_ARN = process.env.CLUSTER_ARN!;
const SECRET_ARN = process.env.SECRET_ARN!;
const DATABASE = process.env.DATABASE!;

export class AuroraRepository {
  async query<T>(sql: string, parameters?: Array<{ name: string; value: any }>): Promise<T[]> {
    const command = new ExecuteStatementCommand({
      resourceArn: CLUSTER_ARN,
      secretArn: SECRET_ARN,
      database: DATABASE,
      sql,
      parameters: parameters?.map(p => ({
        name: p.name,
        value: typeof p.value === 'string' ? { stringValue: p.value } :
               typeof p.value === 'number' ? { longValue: p.value } :
               { stringValue: String(p.value) }
      }))
    });
    const response = await rdsClient.send(command);
    return this.mapRecords<T>(response.records || [], response.columnMetadata || []);
  }

  private mapRecords<T>(records: any[][], columns: any[]): T[] {
    return records.map(row => {
      const obj: any = {};
      columns.forEach((col, i) => {
        obj[col.name] = row[i].stringValue || row[i].longValue || row[i].booleanValue || null;
      });
      return obj as T;
    });
  }
}
```

### Uso en Lambda

```typescript
const auroraRepo = new AuroraRepository();

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const customers = await auroraRepo.query<Customer>(
    'SELECT id, name, email FROM customers WHERE status = :status',
    [{ name: 'status', value: 'ACTIVE' }]
  );
  return { statusCode: 200, body: JSON.stringify(customers) };
};
```

---

## 3. PostgreSQL con pg (conexión directa)

### Dependencias

```json
{
  "dependencies": {
    "pg": "^8.11.0",
    "@types/pg": "^8.10.0"
  }
}
```

### Conexión optimizada para Lambda

```typescript
import { Pool } from 'pg';

// Pool fuera del handler para reutilizar en warm starts
let pool: Pool | null = null;

function getPool(): Pool {
  if (!pool) {
    pool = new Pool({
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT || '5432'),
      database: process.env.DB_NAME,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      max: 1,  // Lambda: 1 conexión por instancia
      min: 0,
      idleTimeoutMillis: 120000,
      connectionTimeoutMillis: 5000
    });
  }
  return pool;
}

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const db = getPool();
  const result = await db.query('SELECT * FROM customers WHERE id = $1', [event.pathParameters?.id]);
  return { statusCode: 200, body: JSON.stringify(result.rows[0] || null) };
};
```

---

## 4. MongoDB con Driver Nativo

### Conexión optimizada para Lambda

```typescript
import { MongoClient, Db } from 'mongodb';

let cachedClient: MongoClient | null = null;
let cachedDb: Db | null = null;

async function connectToDatabase(): Promise<Db> {
  if (cachedDb) return cachedDb;

  cachedClient = new MongoClient(process.env.MONGO_URI!, {
    maxPoolSize: 1,
    minPoolSize: 0,
    maxIdleTimeMS: 120000
  });
  await cachedClient.connect();
  cachedDb = cachedClient.db(process.env.MONGO_DB);
  return cachedDb;
}

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  const db = await connectToDatabase();
  const customer = await db.collection('customers').findOne({ customerId: event.pathParameters?.id });
  if (!customer) return { statusCode: 404, body: JSON.stringify({ error: 'Not found' }) };
  return { statusCode: 200, body: JSON.stringify(customer) };
};
```

---

## Reglas Importantes para Lambda

- **Inicialización fuera del handler**: Clientes de DB se crean fuera del handler para reutilizar en warm starts
- **Connection pool mínimo**: En Lambda usar `max: 1` para PostgreSQL/MongoDB (una conexión por instancia)
- **DynamoDB preferido**: Para serverless, DynamoDB es la opción nativa sin gestión de conexiones
- **Aurora Data API**: Elimina necesidad de connection pool; ideal para Lambda
- **Cold starts**: Minimizar dependencias y usar lazy initialization
- **Timeouts**: Configurar `connectionTimeoutMillis` menor al timeout de Lambda
- **VPC**: Si se usa RDS/Aurora, la Lambda debe estar en VPC (aumenta cold start)
- **Retry**: Implementar retry para `ProvisionedThroughputExceededException` en DynamoDB
