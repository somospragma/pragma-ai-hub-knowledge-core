<!-- keywords: parameter store, aws ssm, configuration management, sdk v3, caching, typescript -->
# AWS Parameter Store Patterns - TypeScript Implementation

## Purpose

Implement configuration management with AWS Parameter Store in TypeScript using AWS SDK v3 with caching.

## Scope of Application

- When developing in Node.js/TypeScript.
- When dynamic configuration in Lambda is needed.
- To implement feature flags.
- When using Lambda Powertools.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-ssm": "^3.0.0",
    "@aws-lambda-powertools/parameters": "^1.0.0",
    "node-cache": "^5.1.2"
  }
}
```

### Implementation with Caching

```typescript
import { SSMClient, GetParameterCommand, GetParametersByPathCommand } from '@aws-sdk/client-ssm';
import NodeCache from 'node-cache';

interface ParameterConfig {
  environment: string;
  appName: string;
  cacheTtlSeconds: number;
}

export class ParameterStoreService {
  private client: SSMClient;
  private cache: NodeCache;
  private config: ParameterConfig;

  constructor(config: ParameterConfig) {
    this.client = new SSMClient({});
    this.cache = new NodeCache({ stdTTL: config.cacheTtlSeconds });
    this.config = config;
  }

  async getParameter(name: string, decrypt: boolean = true): Promise<string> {
    const fullPath = this.buildPath(name);
    
    const cached = this.cache.get<string>(fullPath);
    if (cached !== undefined) {
      return cached;
    }

    const command = new GetParameterCommand({
      Name: fullPath,
      WithDecryption: decrypt
    });

    const response = await this.client.send(command);
    const value = response.Parameter?.Value;

    if (!value) {
      throw new Error(`Parameter not found: ${fullPath}`);
    }

    this.cache.set(fullPath, value);
    return value;
  }

  async getParameterAs<T>(name: string): Promise<T> {
    const value = await this.getParameter(name);
    return JSON.parse(value) as T;
  }

  async getParametersByPath(path: string): Promise<Map<string, string>> {
    const fullPath = this.buildPath(path);
    const parameters = new Map<string, string>();

    let nextToken: string | undefined;

    do {
      const command = new GetParametersByPathCommand({
        Path: fullPath,
        Recursive: true,
        WithDecryption: true,
        NextToken: nextToken
      });

      const response = await this.client.send(command);
      
      response.Parameters?.forEach(param => {
        if (param.Name && param.Value) {
          const key = param.Name.replace(fullPath, '').replace(/^\//, '');
          parameters.set(key, param.Value);
        }
      });

      nextToken = response.NextToken;
    } while (nextToken);

    return parameters;
  }

  private buildPath(name: string): string {
    if (name.startsWith('/')) {
      return name;
    }
    return `/${this.config.appName}/${this.config.environment}/${name}`;
  }

  invalidateCache(name?: string): void {
    if (name) {
      this.cache.del(this.buildPath(name));
    } else {
      this.cache.flushAll();
    }
  }
}
```

### Dynamic Configuration with Polling

```typescript
interface AppConfig {
  logLevel: string;
  apiTimeout: number;
  featureFlags: Record<string, boolean>;
  database: {
    host: string;
    port: number;
  };
}

export class DynamicConfigService {
  private parameterService: ParameterStoreService;
  private currentConfig: AppConfig | null = null;
  private refreshInterval: NodeJS.Timeout | null = null;

  constructor(parameterService: ParameterStoreService) {
    this.parameterService = parameterService;
  }

  async initialize(): Promise<void> {
    await this.refresh();
    this.startPolling();
  }

  async refresh(): Promise<void> {
    const params = await this.parameterService.getParametersByPath('/config');
    
    this.currentConfig = {
      logLevel: params.get('log-level') || 'INFO',
      apiTimeout: parseInt(params.get('api-timeout') || '30'),
      featureFlags: JSON.parse(params.get('feature-flags') || '{}'),
      database: {
        host: params.get('database/host') || 'localhost',
        port: parseInt(params.get('database/port') || '5432')
      }
    };
  }

  private startPolling(): void {
    this.refreshInterval = setInterval(async () => {
      try {
        await this.refresh();
      } catch (error) {
        console.error('Failed to refresh config:', error);
      }
    }, 5 * 60 * 1000);
  }

  getConfig(): AppConfig {
    if (!this.currentConfig) {
      throw new Error('Configuration not initialized');
    }
    return this.currentConfig;
  }

  isFeatureEnabled(feature: string): boolean {
    return this.currentConfig?.featureFlags[feature] ?? false;
  }

  stop(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }
}
```

### Lambda with Lambda Powertools

```typescript
import { getParameter, getParameters } from '@aws-lambda-powertools/parameters/ssm';

export const handler = async (event: any) => {
  const logLevel = await getParameter('/myapp/prod/log-level', {
    maxAge: 300
  });

  const dbConfig = await getParameters('/myapp/prod/database', {
    recursive: true,
    decrypt: true,
    maxAge: 300
  });

  console.log('Log level:', logLevel);
  console.log('DB Host:', dbConfig['/myapp/prod/database/host']);

  return {
    statusCode: 200,
    body: JSON.stringify({ message: 'Success' })
  };
};
```

## Important Rules

- Use caching to reduce calls to Parameter Store.
- Implement polling for dynamic configuration.
- Use Lambda Powertools for automatic caching in Lambda.
- Organize parameters by environment using hierarchies.

## Example

```typescript
// Usage in Express
import express from 'express';

const app = express();
const configService = new DynamicConfigService(
  new ParameterStoreService({
    environment: 'prod',
    appName: 'myapp',
    cacheTtlSeconds: 300
  })
);

await configService.initialize();

app.get('/features/:feature', (req, res) => {
  const enabled = configService.isFeatureEnabled(req.params.feature);
  res.json({ feature: req.params.feature, enabled });
});
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
