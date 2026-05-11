---
id: backend-skill-node-lambda-seguridad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-lambda
---

# Seguridad — Node Lambda

## Propósito

Guía de implementación de controles de seguridad en funciones Lambda con TypeScript: mTLS con API Gateway, Secrets Manager, Parameter Store, PCI-DSS compliance, SOC2 audit logging y data masking.

---

## 1. mTLS con API Gateway

En Lambda, mTLS se configura a nivel de API Gateway (no en el código de la función).

### Validación de certificado en handler

```typescript
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

export const handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {
  // API Gateway pasa info del certificado en requestContext
  const clientCert = event.requestContext?.identity?.clientCert;

  if (!clientCert) {
    return { statusCode: 401, body: JSON.stringify({ error: 'Client certificate required' }) };
  }

  // Validar CN del certificado
  const allowedCNs = new Set((process.env.ALLOWED_CLIENTS || '').split(','));
  const cn = clientCert.subjectDN?.match(/CN=([^,]+)/)?.[1];

  if (!cn || !allowedCNs.has(cn)) {
    return { statusCode: 403, body: JSON.stringify({ error: 'Unauthorized client' }) };
  }

  // Continuar con lógica de negocio
  return { statusCode: 200, body: JSON.stringify({ message: 'Authorized', client: cn }) };
};
```

### Cliente mTLS para llamadas salientes desde Lambda

```typescript
import https from 'https';
import axios, { AxiosInstance } from 'axios';

// Cargar certificados desde Secrets Manager o variables de entorno
export function createMtlsClient(cert: string, key: string, ca: string): AxiosInstance {
  const httpsAgent = new https.Agent({
    cert: Buffer.from(cert),
    key: Buffer.from(key),
    ca: Buffer.from(ca),
    rejectUnauthorized: true
  });
  return axios.create({ httpsAgent, timeout: 30000 });
}
```

---

## 2. AWS Secrets Manager

### Servicio con caché (optimizado para Lambda)

```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

// Inicializar fuera del handler
const secretsClient = new SecretsManagerClient({});
const secretsCache = new Map<string, { value: string; expiry: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutos

export class SecretsService {
  async getSecret(secretId: string): Promise<string> {
    const cached = secretsCache.get(secretId);
    if (cached && Date.now() < cached.expiry) return cached.value;

    const command = new GetSecretValueCommand({ SecretId: secretId });
    const response = await secretsClient.send(command);
    const value = response.SecretString;
    if (!value) throw new Error(`Secret ${secretId} has no string value`);

    secretsCache.set(secretId, { value, expiry: Date.now() + CACHE_TTL_MS });
    return value;
  }

  async getSecretAs<T>(secretId: string): Promise<T> {
    const secretString = await this.getSecret(secretId);
    return JSON.parse(secretString) as T;
  }
}

// Uso en handler con lazy initialization
const secretsService = new SecretsService();
let dbPool: any = null;

export const handler = async (event: any) => {
  if (!dbPool) {
    const creds = await secretsService.getSecretAs<{ host: string; port: number; user: string; password: string; database: string }>(process.env.DB_SECRET_ARN!);
    dbPool = new Pool({ host: creds.host, port: creds.port, user: creds.user, password: creds.password, database: creds.database, max: 1 });
  }
  // Usar dbPool...
};
```

---

## 3. AWS Parameter Store

### Servicio con Lambda Powertools

```typescript
import { getParameter, getParameters } from '@aws-lambda-powertools/parameters/ssm';

export const handler = async (event: any) => {
  // Parámetro individual con caché automático
  const logLevel = await getParameter('/myapp/prod/log-level', { maxAge: 300 });

  // Múltiples parámetros por path
  const dbConfig = await getParameters('/myapp/prod/database', {
    recursive: true,
    decrypt: true,
    maxAge: 300
  });

  console.log('Log level:', logLevel);
  console.log('DB Host:', dbConfig['/myapp/prod/database/host']);

  return { statusCode: 200, body: JSON.stringify({ message: 'Success' }) };
};
```

### Servicio manual con caché

```typescript
import { SSMClient, GetParameterCommand, GetParametersByPathCommand } from '@aws-sdk/client-ssm';

const ssmClient = new SSMClient({});
const paramCache = new Map<string, { value: string; expiry: number }>();
const PARAM_CACHE_TTL = 5 * 60 * 1000;

export class ParameterStoreService {
  async getParameter(name: string, decrypt = true): Promise<string> {
    const cached = paramCache.get(name);
    if (cached && Date.now() < cached.expiry) return cached.value;

    const response = await ssmClient.send(new GetParameterCommand({ Name: name, WithDecryption: decrypt }));
    const value = response.Parameter?.Value;
    if (!value) throw new Error(`Parameter not found: ${name}`);

    paramCache.set(name, { value, expiry: Date.now() + PARAM_CACHE_TTL });
    return value;
  }
}
```

---

## 4. PCI-DSS Compliance en Lambda

### Encriptación de PAN con KMS

```typescript
import { KMSClient, GenerateDataKeyCommand, DecryptCommand } from '@aws-sdk/client-kms';
import crypto from 'crypto';

const kmsClient = new KMSClient({});
const KMS_KEY_ID = process.env.KMS_KEY_ID!;

export class PciEncryptionService {
  async encryptPan(pan: string): Promise<{ ciphertext: string; iv: string; authTag: string; keyId: string }> {
    const response = await kmsClient.send(new GenerateDataKeyCommand({ KeyId: KMS_KEY_ID, KeySpec: 'AES_256' }));
    const plaintext = Buffer.from(response.Plaintext!);
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', plaintext, iv);
    let ciphertext = cipher.update(pan, 'utf8', 'base64');
    ciphertext += cipher.final('base64');
    const authTag = cipher.getAuthTag();
    plaintext.fill(0);
    return { ciphertext, iv: iv.toString('base64'), authTag: authTag.toString('base64'), keyId: Buffer.from(response.CiphertextBlob!).toString('base64') };
  }
}

export function validateLuhn(pan: string): boolean {
  const digits = pan.replace(/\D/g, '');
  if (digits.length < 13 || digits.length > 19) return false;
  let sum = 0, alternate = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10);
    if (alternate) { digit *= 2; if (digit > 9) digit -= 9; }
    sum += digit;
    alternate = !alternate;
  }
  return sum % 10 === 0;
}

export function maskPan(pan: string): string {
  return pan.length < 4 ? '****' : '*'.repeat(pan.length - 4) + pan.slice(-4);
}
```

### Sanitización en respuestas Lambda

```typescript
const SENSITIVE_FIELDS = ['pan', 'cardNumber', 'cvv', 'cvc', 'securityCode'];

function sanitizeForLog(obj: any): any {
  if (!obj || typeof obj !== 'object') return obj;
  const sanitized: any = Array.isArray(obj) ? [] : {};
  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_FIELDS.includes(key.toLowerCase())) sanitized[key] = '[REDACTED]';
    else if (typeof value === 'object') sanitized[key] = sanitizeForLog(value);
    else sanitized[key] = value;
  }
  return sanitized;
}
```

---

## 5. SOC2 Audit Logging

```typescript
import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { KinesisClient, PutRecordCommand } from '@aws-sdk/client-kinesis';

const dynamodb = new DynamoDBClient({});
const kinesis = new KinesisClient({});

interface AuditEvent {
  eventId: string;
  timestamp: string;
  eventType: string;
  actor: { userId: string; userType: string; sourceIp: string };
  resource: { type: string; id: string };
  action: { type: string; status: 'SUCCESS' | 'FAILURE' };
}

export class AuditService {
  async logEvent(params: Omit<AuditEvent, 'eventId' | 'timestamp'>): Promise<void> {
    const event: AuditEvent = { eventId: crypto.randomUUID(), timestamp: new Date().toISOString(), ...params };
    await Promise.all([
      dynamodb.send(new PutItemCommand({
        TableName: process.env.AUDIT_TABLE!,
        Item: { pk: { S: `EVENT#${event.eventId}` }, sk: { S: event.timestamp }, data: { S: JSON.stringify(event) }, ttl: { N: String(Math.floor(Date.now() / 1000) + 7 * 365 * 24 * 60 * 60) } }
      })),
      kinesis.send(new PutRecordCommand({
        StreamName: process.env.AUDIT_STREAM!,
        Data: Buffer.from(JSON.stringify(event)),
        PartitionKey: event.actor.userId
      }))
    ]);
  }
}
```

---

## 6. Data Masking

```typescript
type DataType = 'PAN' | 'EMAIL' | 'PHONE' | 'SSN' | 'NAME';

export class DataMaskingService {
  private strategies: Map<DataType, (value: string) => string> = new Map([
    ['PAN', (pan) => '*'.repeat(Math.max(0, pan.length - 4)) + pan.slice(-4)],
    ['EMAIL', (email) => { const [l, d] = email.split('@'); return `${l[0]}***${l[l.length-1]}@${d}`; }],
    ['PHONE', (phone) => `***-***-${phone.replace(/\D/g, '').slice(-4)}`],
    ['SSN', (ssn) => `***-**-${ssn.replace(/\D/g, '').slice(-4)}`],
    ['NAME', (name) => name.split(' ').map(p => `${p[0]}${'*'.repeat(p.length-1)}`).join(' ')]
  ]);

  mask(value: string | null, type: DataType): string {
    if (!value) return '';
    return this.strategies.get(type)?.(value) || value;
  }
}
```

---

## Reglas Importantes para Lambda

- **Secrets fuera del handler**: Inicializar clientes de Secrets Manager/SSM fuera del handler
- **Caché en memoria**: Usar caché con TTL para reducir llamadas a Secrets Manager/Parameter Store
- **Lambda Powertools**: Preferir `@aws-lambda-powertools/parameters` para caché automático
- **mTLS**: Configurar en API Gateway; validar CN en el handler si es necesario
- **PCI-DSS**: Nunca loguear datos de tarjeta; limpiar claves de memoria
- **SOC2**: Retención de 7 años; persistencia dual (DynamoDB + Kinesis)
- **IAM**: Usar least privilege en el rol de Lambda (solo permisos necesarios)
- **Environment variables**: Usar variables de entorno encriptadas con KMS para datos sensibles
