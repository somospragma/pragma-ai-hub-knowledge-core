---
id: backend-skill-node-lambda-resiliencia
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Resiliencia — Node Lambda

## Propósito

Guía de implementación de patrones de resiliencia en funciones Lambda con TypeScript: Circuit Breaker, Retry con backoff exponencial, Timeouts adaptados a Lambda, y manejo de cold starts.

---

## 1. Circuit Breaker en Lambda

En Lambda, el circuit breaker se implementa con estado externo (DynamoDB/Parameter Store) ya que las instancias son efímeras.

### Circuit Breaker con estado en memoria (warm starts)

```typescript
import CircuitBreaker from 'opossum';

// Inicializar fuera del handler para persistir en warm starts
const breakers = new Map<string, CircuitBreaker<any[], any>>();

function getOrCreateBreaker<T>(name: string, action: (...args: any[]) => Promise<T>): CircuitBreaker<any[], T> {
  if (!breakers.has(name)) {
    const breaker = new CircuitBreaker(action, {
      timeout: 5000,
      errorThresholdPercentage: 50,
      resetTimeout: 30000,
      volumeThreshold: 3  // Menor threshold para Lambda (menos tráfico por instancia)
    });
    breaker.fallback(() => ({ status: 'FALLBACK', message: 'Service temporarily unavailable' }));
    breakers.set(name, breaker);
  }
  return breakers.get(name)!;
}

export const handler = async (event: any) => {
  const paymentBreaker = getOrCreateBreaker('payment-service', callPaymentApi);
  try {
    const result = await paymentBreaker.fire(event.body);
    return { statusCode: 200, body: JSON.stringify(result) };
  } catch (error) {
    return { statusCode: 503, body: JSON.stringify({ error: 'Service unavailable' }) };
  }
};
```

### Circuit Breaker con estado en DynamoDB (distribuido)

```typescript
import { DynamoDBDocumentClient, GetCommand, UpdateCommand } from '@aws-sdk/lib-dynamodb';

interface CircuitState {
  serviceName: string;
  state: 'CLOSED' | 'OPEN' | 'HALF_OPEN';
  failureCount: number;
  lastFailureTime: string;
  openedAt?: string;
}

export class DistributedCircuitBreaker {
  constructor(
    private docClient: DynamoDBDocumentClient,
    private tableName: string,
    private config: { failureThreshold: number; resetTimeoutMs: number }
  ) {}

  async canExecute(serviceName: string): Promise<boolean> {
    const state = await this.getState(serviceName);
    if (state.state === 'CLOSED') return true;
    if (state.state === 'OPEN') {
      const elapsed = Date.now() - new Date(state.openedAt!).getTime();
      if (elapsed > this.config.resetTimeoutMs) {
        await this.setState(serviceName, 'HALF_OPEN');
        return true; // Permitir un intento
      }
      return false;
    }
    return true; // HALF_OPEN permite intentos
  }

  async recordSuccess(serviceName: string): Promise<void> {
    await this.setState(serviceName, 'CLOSED', 0);
  }

  async recordFailure(serviceName: string): Promise<void> {
    const state = await this.getState(serviceName);
    const newCount = state.failureCount + 1;
    if (newCount >= this.config.failureThreshold) {
      await this.setState(serviceName, 'OPEN', newCount);
    } else {
      await this.updateFailureCount(serviceName, newCount);
    }
  }

  private async getState(serviceName: string): Promise<CircuitState> {
    const response = await this.docClient.send(new GetCommand({
      TableName: this.tableName,
      Key: { pk: `CIRCUIT#${serviceName}`, sk: 'STATE' }
    }));
    return response.Item as CircuitState || { serviceName, state: 'CLOSED', failureCount: 0, lastFailureTime: '' };
  }

  private async setState(serviceName: string, state: string, failureCount?: number): Promise<void> {
    await this.docClient.send(new UpdateCommand({
      TableName: this.tableName,
      Key: { pk: `CIRCUIT#${serviceName}`, sk: 'STATE' },
      UpdateExpression: 'SET #state = :state, failureCount = :count, openedAt = :now',
      ExpressionAttributeNames: { '#state': 'state' },
      ExpressionAttributeValues: { ':state': state, ':count': failureCount ?? 0, ':now': new Date().toISOString() }
    }));
  }
}
```

---

## 2. Retry con Backoff Exponencial

### Utilidad de retry para Lambda

```typescript
interface RetryConfig {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  multiplier: number;
  jitterFactor: number;
}

const defaultConfig: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 200,   // Menor delay inicial para Lambda (timeout limitado)
  maxDelayMs: 5000,      // Menor delay máximo
  multiplier: 2,
  jitterFactor: 0.5
};

export async function withRetry<T>(operation: () => Promise<T>, config: Partial<RetryConfig> = {}): Promise<T> {
  const cfg = { ...defaultConfig, ...config };
  let lastError: Error;

  for (let attempt = 0; attempt < cfg.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (attempt < cfg.maxAttempts - 1) {
        const delay = Math.min(cfg.initialDelayMs * Math.pow(cfg.multiplier, attempt), cfg.maxDelayMs);
        const jitter = delay * cfg.jitterFactor * (Math.random() * 2 - 1);
        await new Promise(resolve => setTimeout(resolve, Math.max(0, delay + jitter)));
      }
    }
  }
  throw lastError!;
}
```

### Retry con awareness del timeout de Lambda

```typescript
import { Context } from 'aws-lambda';

export async function withRetryAndTimeout<T>(
  operation: () => Promise<T>,
  context: Context,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const cfg = { ...defaultConfig, ...config };
  let lastError: Error;

  for (let attempt = 0; attempt < cfg.maxAttempts; attempt++) {
    // Verificar si queda tiempo suficiente para reintentar
    const remainingMs = context.getRemainingTimeInMillis();
    const estimatedTimeNeeded = cfg.initialDelayMs * Math.pow(cfg.multiplier, attempt) + 5000; // 5s buffer

    if (remainingMs < estimatedTimeNeeded) {
      console.warn(`Not enough time for retry attempt ${attempt + 1}. Remaining: ${remainingMs}ms`);
      break;
    }

    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;
      if (attempt < cfg.maxAttempts - 1) {
        const delay = Math.min(cfg.initialDelayMs * Math.pow(cfg.multiplier, attempt), cfg.maxDelayMs);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  throw lastError!;
}
```

---

## 3. Timeouts Adaptados a Lambda

### Timeout utility con context awareness

```typescript
import { Context } from 'aws-lambda';

export async function withTimeout<T>(operation: () => Promise<T>, timeoutMs: number): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error('Operation timed out')), timeoutMs);
  });
  return Promise.race([operation(), timeoutPromise]);
}

// Timeout basado en el tiempo restante de Lambda
export async function withLambdaTimeout<T>(operation: () => Promise<T>, context: Context, bufferMs = 2000): Promise<T> {
  const remainingMs = context.getRemainingTimeInMillis();
  const operationTimeout = remainingMs - bufferMs; // Dejar buffer para cleanup

  if (operationTimeout <= 0) {
    throw new Error('Not enough time remaining in Lambda execution');
  }

  return withTimeout(operation, operationTimeout);
}
```

### Combinación resiliente completa

```typescript
export async function resilientCall<T>(
  operation: () => Promise<T>,
  context: Context,
  options: { operationTimeoutMs?: number; retryConfig?: Partial<RetryConfig> } = {}
): Promise<T> {
  const timeoutMs = options.operationTimeoutMs || 5000;
  return withRetryAndTimeout(
    () => withTimeout(operation, timeoutMs),
    context,
    options.retryConfig
  );
}

// Uso en handler
export const handler = async (event: APIGatewayProxyEvent, context: Context) => {
  const result = await resilientCall(
    () => externalService.call(event.body),
    context,
    { operationTimeoutMs: 5000, retryConfig: { maxAttempts: 2 } }
  );
  return { statusCode: 200, body: JSON.stringify(result) };
};
```

---

## 4. Manejo de Cold Starts

### Lazy initialization con caché

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

// Inicialización eager de clientes ligeros
const dynamoClient = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(dynamoClient);

// Lazy initialization de recursos pesados
let heavyResource: HeavyResource | null = null;

async function getHeavyResource(): Promise<HeavyResource> {
  if (!heavyResource) {
    heavyResource = await HeavyResource.initialize();
  }
  return heavyResource;
}

export const handler = async (event: any) => {
  // Clientes ligeros ya están listos
  // Recursos pesados se inicializan solo cuando se necesitan
  const resource = await getHeavyResource();
  // ...
};
```

### Provisioned Concurrency para eliminar cold starts

```yaml
# template.yaml
Resources:
  CriticalFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: handler.handler
      AutoPublishAlias: live
      ProvisionedConcurrencyConfig:
        ProvisionedConcurrentExecutions: 5
```

### Warming strategy (keep-alive)

```typescript
export const handler = async (event: any, context: Context) => {
  // Detectar invocación de warming
  if (event.source === 'serverless-plugin-warmup' || event.warmup) {
    console.log('Warming invocation');
    return { statusCode: 200, body: 'Warmed' };
  }

  // Lógica normal
  return processEvent(event);
};
```

---

## Reglas Importantes para Lambda

- **Cold starts**: Inicializar clientes AWS fuera del handler; usar lazy init para recursos pesados
- **Timeout awareness**: Siempre considerar `context.getRemainingTimeInMillis()` antes de reintentar
- **Circuit breaker**: En Lambda, preferir estado distribuido (DynamoDB) o aceptar estado por instancia
- **Retry delays**: Usar delays menores que en Express (el timeout de Lambda es limitado)
- **Buffer de timeout**: Dejar 2-3 segundos de buffer antes del timeout de Lambda para cleanup
- **Provisioned Concurrency**: Usar para funciones críticas que no toleran cold starts
- **Memory**: Más memoria = más CPU = cold starts más rápidos
- **Bulkhead**: En Lambda, la concurrencia reservada (`ReservedConcurrentExecutions`) actúa como bulkhead nativo
