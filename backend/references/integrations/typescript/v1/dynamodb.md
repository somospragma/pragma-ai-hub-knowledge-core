<!-- keywords: dynamodb, aws, nosql, sdk v3, document client, typescript, nodejs -->
# DynamoDB Integration - TypeScript

## Purpose

Implement integration with DynamoDB in TypeScript using AWS SDK v3 with DocumentClient.

## Scope of Application

- Node.js/TypeScript projects that require DynamoDB
- Serverless applications with Lambda
- APIs with Express, Fastify, or NestJS

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-dynamodb": "^3.400.0",
    "@aws-sdk/lib-dynamodb": "^3.400.0"
  }
}
```

### DynamoDB Client

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { 
  DynamoDBDocumentClient, 
  GetCommand, 
  PutCommand, 
  QueryCommand,
  TransactWriteCommand
} from '@aws-sdk/lib-dynamodb';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);
```

### CRUD Operations

```typescript
interface Customer {
  pk: string;
  sk: string;
  name: string;
  email: string;
  status: string;
  gsi1pk: string;
  gsi1sk: string;
}

export class CustomerRepository {
  constructor(private tableName: string) {}

  async findById(customerId: string): Promise<Customer | null> {
    const command = new GetCommand({
      TableName: this.tableName,
      Key: {
        pk: `CUSTOMER#${customerId}`,
        sk: 'PROFILE'
      }
    });

    const response = await docClient.send(command);
    return response.Item as Customer || null;
  }

  async findByStatus(status: string): Promise<Customer[]> {
    const command = new QueryCommand({
      TableName: this.tableName,
      IndexName: 'GSI1',
      KeyConditionExpression: 'gsi1pk = :status',
      ExpressionAttributeValues: {
        ':status': `STATUS#${status}`
      }
    });

    const response = await docClient.send(command);
    return response.Items as Customer[] || [];
  }


  async create(
    customer: Omit<Customer, 'pk' | 'sk' | 'gsi1pk' | 'gsi1sk'>
  ): Promise<Customer> {
    const id = crypto.randomUUID();
    const item: Customer = {
      pk: `CUSTOMER#${id}`,
      sk: 'PROFILE',
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

### Transactions

```typescript
interface Order {
  pk: string;
  sk: string;
  customerId: string;
  amount: number;
  status: string;
}

export class OrderService {
  constructor(private tableName: string) {}

  async createOrderWithItems(
    customerId: string,
    items: Array<{ productId: string; quantity: number; price: number }>
  ): Promise<string> {
    const orderId = crypto.randomUUID();
    const totalAmount = items.reduce(
      (sum, item) => sum + item.price * item.quantity, 0
    );

    const transactItems = [
      {
        Put: {
          TableName: this.tableName,
          Item: {
            pk: `ORDER#${orderId}`,
            sk: 'METADATA',
            customerId,
            amount: totalAmount,
            status: 'PENDING',
            createdAt: new Date().toISOString()
          },
          ConditionExpression: 'attribute_not_exists(pk)'
        }
      },
      ...items.map((item, index) => ({
        Put: {
          TableName: this.tableName,
          Item: {
            pk: `ORDER#${orderId}`,
            sk: `ITEM#${index}`,
            ...item
          }
        }
      }))
    ];

    const command = new TransactWriteCommand({ TransactItems: transactItems });
    await docClient.send(command);

    return orderId;
  }
}
```

### Error handling

```typescript
import { ConditionalCheckFailedException } from '@aws-sdk/client-dynamodb';

async create(customer: CustomerInput): Promise<Customer> {
  try {
    return await this.repository.create(customer);
  } catch (error) {
    if (error instanceof ConditionalCheckFailedException) {
      throw new ConflictError('Customer already exists');
    }
    throw error;
  }
}
```

## Important Rules

- Use DocumentClient for automatic serialization
- Implement retry for ProvisionedThroughputExceededException
- Use TransactWriteCommand for atomic operations
- Design composite keys for single-table design

## Example

```typescript
// Lambda handler
export const handler = async (event: APIGatewayEvent) => {
  const repo = new CustomerRepository(process.env.TABLE_NAME!);
  
  if (event.httpMethod === 'GET') {
    const id = event.pathParameters?.id;
    const customer = await repo.findById(id!);
    
    if (!customer) {
      return { statusCode: 404, body: JSON.stringify({ error: 'Not found' }) };
    }
    return { statusCode: 200, body: JSON.stringify(customer) };
  }
  
  if (event.httpMethod === 'POST') {
    const body = JSON.parse(event.body!);
    const customer = await repo.create(body);
    return { statusCode: 201, body: JSON.stringify(customer) };
  }
};
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
