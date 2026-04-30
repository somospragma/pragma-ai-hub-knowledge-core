<!-- keywords: mongodb, nosql, document database, connection pooling, typescript, nodejs -->
# MongoDB Integration - TypeScript

## Purpose

Implement integration with MongoDB in TypeScript using the official driver with connection pooling.

## Scope of Application

- Node.js/TypeScript projects that require MongoDB
- Implementation with Express, Fastify, or NestJS
- Applications with high concurrency

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "mongodb": "^6.0.0"
  }
}
```

### Client with Connection Pool

```typescript
import { MongoClient, Db, Collection } from 'mongodb';

interface MongoConfig {
  uri: string;
  database: string;
  options?: {
    maxPoolSize?: number;
    minPoolSize?: number;
    maxIdleTimeMS?: number;
  };
}

class MongoConnectionManager {
  private client: MongoClient | null = null;
  private db: Db | null = null;
  
  async connect(config: MongoConfig): Promise<void> {
    this.client = new MongoClient(config.uri, {
      maxPoolSize: config.options?.maxPoolSize ?? 50,
      minPoolSize: config.options?.minPoolSize ?? 5,
      maxIdleTimeMS: config.options?.maxIdleTimeMS ?? 60000,
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


### CRUD Operations

```typescript
interface Customer {
  _id?: string;
  customerId: string;
  name: string;
  email: string;
  status: string;
  createdDate: Date;
  addresses?: Address[];
}

class CustomerRepository {
  private collection: Collection<Customer>;
  
  constructor(connectionManager: MongoConnectionManager) {
    this.collection = connectionManager.getCollection<Customer>('customers');
  }
  
  async findById(customerId: string): Promise<Customer | null> {
    return this.collection.findOne({ customerId });
  }
  
  async findByStatus(status: string): Promise<Customer[]> {
    return this.collection
      .find({ status })
      .sort({ createdDate: -1 })
      .toArray();
  }
  
  async aggregateByStatus(): Promise<{ _id: string; count: number }[]> {
    return this.collection.aggregate([
      { $group: { _id: '$status', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]).toArray();
  }
  
  async upsert(customer: Customer): Promise<Customer> {
    const result = await this.collection.findOneAndUpdate(
      { customerId: customer.customerId },
      {
        $set: {
          name: customer.name,
          email: customer.email,
          status: customer.status
        },
        $setOnInsert: { createdDate: new Date() }
      },
      { upsert: true, returnDocument: 'after' }
    );
    
    return result!;
  }
  
  async textSearch(searchText: string): Promise<Customer[]> {
    return this.collection
      .find(
        { $text: { $search: searchText } },
        { projection: { score: { $meta: 'textScore' } } }
      )
      .sort({ score: { $meta: 'textScore' } })
      .limit(50)
      .toArray();
  }
  
  async createIndexes(): Promise<void> {
    await this.collection.createIndexes([
      { key: { customerId: 1 }, unique: true },
      { key: { email: 1 } },
      { key: { status: 1, createdDate: -1 } },
      { key: { name: 'text', email: 'text' } }
    ]);
  }
}
```

### Error handling

```typescript
import { MongoServerError } from 'mongodb';

async create(customer: Customer): Promise<Customer> {
  try {
    await this.collection.insertOne(customer);
    return customer;
  } catch (error) {
    if (error instanceof MongoServerError && error.code === 11000) {
      throw new ConflictError('Customer already exists');
    }
    throw error;
  }
}
```

## Important Rules

- Use connection pooling with MongoClient
- Create indexes for frequently queried fields
- Use aggregations for complex queries
- Implement retry for transient errors

## Example

```typescript
// Usage with Express
const app = express();
const mongo = new MongoConnectionManager();

await mongo.connect({
  uri: process.env.MONGO_URI!,
  database: process.env.MONGO_DB!
});

const customerRepo = new CustomerRepository(mongo);

app.get('/customers/:id', async (req, res) => {
  const customer = await customerRepo.findById(req.params.id);
  if (!customer) return res.status(404).json({ error: 'Not found' });
  res.json(customer);
});

process.on('SIGTERM', async () => {
  await mongo.close();
  process.exit(0);
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
