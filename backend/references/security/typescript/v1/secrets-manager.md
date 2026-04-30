<!-- keywords: secrets manager, aws, secret rotation, sdk v3, caching, credentials, typescript -->
# AWS Secrets Manager Patterns - TypeScript Implementation

## Purpose

Implement secrets management with AWS Secrets Manager in TypeScript using AWS SDK v3 with caching.

## Scope of Application

- When developing in Node.js/TypeScript.
- When secret access in Lambda is needed.
- To implement credential caching.
- When configuring dynamic database connections.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-secrets-manager": "^3.0.0",
    "node-cache": "^5.1.2"
  }
}
```

### Implementation with Caching

```typescript
import { 
  SecretsManagerClient, 
  GetSecretValueCommand,
  GetSecretValueCommandOutput 
} from '@aws-sdk/client-secrets-manager';
import NodeCache from 'node-cache';

interface SecretsCacheConfig {
  ttlSeconds: number;
  checkPeriod: number;
}

export class SecretsService {
  private client: SecretsManagerClient;
  private cache: NodeCache;

  constructor(config: SecretsCacheConfig = { ttlSeconds: 3600, checkPeriod: 600 }) {
    this.client = new SecretsManagerClient({});
    this.cache = new NodeCache({
      stdTTL: config.ttlSeconds,
      checkperiod: config.checkPeriod,
      useClones: false
    });
  }

  async getSecret(secretId: string): Promise<string> {
    const cached = this.cache.get<string>(secretId);
    if (cached) {
      return cached;
    }

    const command = new GetSecretValueCommand({ SecretId: secretId });
    const response = await this.client.send(command);
    
    const secretValue = response.SecretString;
    if (!secretValue) {
      throw new Error(`Secret ${secretId} has no string value`);
    }

    this.cache.set(secretId, secretValue);
    
    return secretValue;
  }

  async getSecretAs<T>(secretId: string): Promise<T> {
    const secretString = await this.getSecret(secretId);
    return JSON.parse(secretString) as T;
  }

  invalidateCache(secretId?: string): void {
    if (secretId) {
      this.cache.del(secretId);
    } else {
      this.cache.flushAll();
    }
  }
}
```

### Usage with Types

```typescript
interface DatabaseCredentials {
  username: string;
  password: string;
  host: string;
  port: number;
  dbname: string;
}

interface ApiKeySecret {
  apiKey: string;
  apiSecret: string;
  environment: string;
}

export class ConfigurationService {
  private secretsService: SecretsService;

  constructor() {
    this.secretsService = new SecretsService({ ttlSeconds: 1800, checkPeriod: 300 });
  }

  async getDatabaseConfig(): Promise<DatabaseCredentials> {
    return this.secretsService.getSecretAs<DatabaseCredentials>(
      process.env.DB_SECRET_ARN!
    );
  }

  async getApiKeys(): Promise<ApiKeySecret> {
    return this.secretsService.getSecretAs<ApiKeySecret>(
      process.env.API_SECRET_ARN!
    );
  }

  async createDatabaseConnection(): Promise<Pool> {
    const creds = await this.getDatabaseConfig();
    
    return new Pool({
      host: creds.host,
      port: creds.port,
      user: creds.username,
      password: creds.password,
      database: creds.dbname,
      max: 10,
      idleTimeoutMillis: 30000
    });
  }
}
```

### Lambda Handler with Secrets

```typescript
import { Handler } from 'aws-lambda';

const secretsService = new SecretsService();
let dbPool: Pool | null = null;

export const handler: Handler = async (event) => {
  // Lazy initialization of pool
  if (!dbPool) {
    const creds = await secretsService.getSecretAs<DatabaseCredentials>(
      process.env.DB_SECRET_ARN!
    );
    dbPool = new Pool({
      host: creds.host,
      port: creds.port,
      user: creds.username,
      password: creds.password,
      database: creds.dbname
    });
  }

  const result = await dbPool.query('SELECT * FROM users WHERE id = $1', [event.userId]);
  
  return {
    statusCode: 200,
    body: JSON.stringify(result.rows)
  };
};
```

## Important Rules

- Initialize services outside the handler to reuse between invocations.
- Use caching to reduce latency and costs.
- Do not hardcode secret ARNs; use environment variables.
- Implement lazy initialization for database connections.

## Example

```typescript
// Usage in Express
import express from 'express';

const app = express();
const configService = new ConfigurationService();

app.get('/api/data', async (req, res) => {
  try {
    const pool = await configService.createDatabaseConnection();
    const result = await pool.query('SELECT * FROM data');
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch data' });
  }
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
