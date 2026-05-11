---
id: backend-skill-node-express-seguridad
version: "1.0"
scope: stack
type: skill
chapter: backend
stack: node-express
---

# Seguridad — Node Express

## Propósito

Guía de implementación de controles de seguridad en microservicios Node.js/Express con TypeScript: mTLS, Secrets Manager, Parameter Store, PCI-DSS compliance, SOC2 audit logging y data masking.

---

## 1. mTLS (Mutual TLS)

### Dependencias

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "express": "^4.18.0"
  }
}
```

### Cliente mTLS con Axios

```typescript
import https from 'https';
import fs from 'fs';
import axios, { AxiosInstance } from 'axios';

interface MtlsConfig {
  certPath: string;
  keyPath: string;
  caPath: string;
  passphrase?: string;
}

export function createMtlsClient(config: MtlsConfig): AxiosInstance {
  const httpsAgent = new https.Agent({
    cert: fs.readFileSync(config.certPath),
    key: fs.readFileSync(config.keyPath),
    ca: fs.readFileSync(config.caPath),
    passphrase: config.passphrase,
    rejectUnauthorized: true
  });
  return axios.create({ httpsAgent, timeout: 30000 });
}
```

### Servidor Express con mTLS

```typescript
import express, { Request, Response, NextFunction } from 'express';
import https from 'https';
import fs from 'fs';

const app = express();

app.use((req: Request, res: Response, next: NextFunction) => {
  const cert = (req.socket as any).getPeerCertificate();
  if (!cert || Object.keys(cert).length === 0) {
    return res.status(401).json({ error: 'Client certificate required' });
  }
  if (!(req as any).client.authorized) {
    return res.status(403).json({ error: 'Unauthorized certificate' });
  }
  (req as any).clientCN = cert.subject.CN;
  next();
});

const serverOptions: https.ServerOptions = {
  cert: fs.readFileSync('/certs/server.crt'),
  key: fs.readFileSync('/certs/server.key'),
  ca: fs.readFileSync('/certs/ca.crt'),
  requestCert: true,
  rejectUnauthorized: true
};

https.createServer(serverOptions, app).listen(443);
```

### Validador de certificados con whitelist

```typescript
export class CertificateValidator {
  private allowedCNs: Set<string>;

  constructor(allowedClients: string[]) {
    this.allowedCNs = new Set(allowedClients);
  }

  validate(cert: { subject: { CN: string }; valid_to: string }): void {
    if (!this.allowedCNs.has(cert.subject.CN)) {
      throw new Error(`Unauthorized client: ${cert.subject.CN}`);
    }
    if (new Date(cert.valid_to) < new Date()) {
      throw new Error('Expired certificate');
    }
  }
}
```

---

## 2. AWS Secrets Manager

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-secrets-manager": "^3.400.0",
    "node-cache": "^5.1.2"
  }
}
```

### Servicio con caché

```typescript
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';
import NodeCache from 'node-cache';

export class SecretsService {
  private client: SecretsManagerClient;
  private cache: NodeCache;

  constructor(config: { ttlSeconds: number } = { ttlSeconds: 3600 }) {
    this.client = new SecretsManagerClient({});
    this.cache = new NodeCache({ stdTTL: config.ttlSeconds, checkperiod: 600, useClones: false });
  }

  async getSecret(secretId: string): Promise<string> {
    const cached = this.cache.get<string>(secretId);
    if (cached) return cached;

    const command = new GetSecretValueCommand({ SecretId: secretId });
    const response = await this.client.send(command);
    const value = response.SecretString;
    if (!value) throw new Error(`Secret ${secretId} has no string value`);

    this.cache.set(secretId, value);
    return value;
  }

  async getSecretAs<T>(secretId: string): Promise<T> {
    const secretString = await this.getSecret(secretId);
    return JSON.parse(secretString) as T;
  }

  invalidateCache(secretId?: string): void {
    secretId ? this.cache.del(secretId) : this.cache.flushAll();
  }
}
```

---

## 3. AWS Parameter Store

### Dependencias

```json
{
  "dependencies": {
    "@aws-sdk/client-ssm": "^3.400.0",
    "node-cache": "^5.1.2"
  }
}
```

### Servicio con caché y jerarquías

```typescript
import { SSMClient, GetParameterCommand, GetParametersByPathCommand } from '@aws-sdk/client-ssm';
import NodeCache from 'node-cache';

export class ParameterStoreService {
  private client: SSMClient;
  private cache: NodeCache;

  constructor(private config: { environment: string; appName: string; cacheTtlSeconds: number }) {
    this.client = new SSMClient({});
    this.cache = new NodeCache({ stdTTL: config.cacheTtlSeconds });
  }

  async getParameter(name: string, decrypt = true): Promise<string> {
    const fullPath = `/${this.config.appName}/${this.config.environment}/${name}`;
    const cached = this.cache.get<string>(fullPath);
    if (cached !== undefined) return cached;

    const command = new GetParameterCommand({ Name: fullPath, WithDecryption: decrypt });
    const response = await this.client.send(command);
    const value = response.Parameter?.Value;
    if (!value) throw new Error(`Parameter not found: ${fullPath}`);

    this.cache.set(fullPath, value);
    return value;
  }

  async getParametersByPath(path: string): Promise<Map<string, string>> {
    const fullPath = `/${this.config.appName}/${this.config.environment}/${path}`;
    const parameters = new Map<string, string>();
    let nextToken: string | undefined;
    do {
      const response = await this.client.send(new GetParametersByPathCommand({
        Path: fullPath, Recursive: true, WithDecryption: true, NextToken: nextToken
      }));
      response.Parameters?.forEach(p => {
        if (p.Name && p.Value) parameters.set(p.Name.replace(fullPath, '').replace(/^\//, ''), p.Value);
      });
      nextToken = response.NextToken;
    } while (nextToken);
    return parameters;
  }
}
```

---

## 4. PCI-DSS Compliance

### Encriptación de PAN con KMS

```typescript
import { KMSClient, GenerateDataKeyCommand, DecryptCommand } from '@aws-sdk/client-kms';
import crypto from 'crypto';

interface EncryptedData {
  ciphertext: string;
  iv: string;
  authTag: string;
  keyId: string;
}

export class PciEncryptionService {
  private kmsClient: KMSClient;

  constructor(private keyId: string) {
    this.kmsClient = new KMSClient({});
  }

  async encryptPan(pan: string): Promise<EncryptedData> {
    const dataKey = await this.generateDataKey();
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', dataKey.plaintext, iv);
    let ciphertext = cipher.update(pan, 'utf8', 'base64');
    ciphertext += cipher.final('base64');
    const authTag = cipher.getAuthTag();
    dataKey.plaintext.fill(0); // Limpiar clave de memoria
    return { ciphertext, iv: iv.toString('base64'), authTag: authTag.toString('base64'), keyId: dataKey.encryptedKey };
  }

  private async generateDataKey(): Promise<{ plaintext: Buffer; encryptedKey: string }> {
    const response = await this.kmsClient.send(new GenerateDataKeyCommand({ KeyId: this.keyId, KeySpec: 'AES_256' }));
    return { plaintext: Buffer.from(response.Plaintext!), encryptedKey: Buffer.from(response.CiphertextBlob!).toString('base64') };
  }
}
```

### Middleware de sanitización PCI

```typescript
import { Request, Response, NextFunction } from 'express';

const PAN_REGEX = /\b(?:\d{4}[-\s]?){3}\d{4}\b/g;
const SENSITIVE_FIELDS = ['pan', 'cardNumber', 'cvv', 'cvc', 'securityCode'];

export function pciSanitizationMiddleware(req: Request, res: Response, next: NextFunction): void {
  const sanitizedBody = sanitizeObject(req.body);
  (req as any).sanitizedBody = sanitizedBody;
  const originalJson = res.json.bind(res);
  res.json = (data: any) => {
    console.log('Response:', JSON.stringify(sanitizeObject(data)));
    return originalJson(data);
  };
  next();
}

function sanitizeObject(obj: any): any {
  if (!obj || typeof obj !== 'object') return obj;
  const sanitized: any = Array.isArray(obj) ? [] : {};
  for (const [key, value] of Object.entries(obj)) {
    if (SENSITIVE_FIELDS.includes(key.toLowerCase())) sanitized[key] = '[REDACTED]';
    else if (typeof value === 'string') sanitized[key] = value.replace(PAN_REGEX, '[PAN-REDACTED]');
    else if (typeof value === 'object') sanitized[key] = sanitizeObject(value);
    else sanitized[key] = value;
  }
  return sanitized;
}
```

### Validador Luhn

```typescript
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
  if (!pan || pan.length < 4) return '****';
  return '*'.repeat(pan.length - 4) + pan.slice(-4);
}
```

---

## 5. SOC2 Audit Logging

### Modelo de evento de auditoría

```typescript
interface AuditEvent {
  eventId: string;
  timestamp: string;
  eventType: 'DATA_ACCESS' | 'DATA_MODIFICATION' | 'AUTHENTICATION' | 'AUTHORIZATION' | 'CONFIGURATION_CHANGE';
  actor: { userId: string; userType: 'EMPLOYEE' | 'CUSTOMER' | 'SYSTEM'; ipAddress: string };
  resource: { type: string; id: string; name: string };
  action: { type: string; status: 'SUCCESS' | 'FAILURE'; details: string | null };
}
```

### Servicio de auditoría con DynamoDB + Kinesis

```typescript
import { KinesisClient, PutRecordCommand } from '@aws-sdk/client-kinesis';
import { DynamoDBClient, PutItemCommand } from '@aws-sdk/client-dynamodb';
import { v4 as uuidv4 } from 'uuid';

export class AuditService {
  private kinesis: KinesisClient;
  private dynamodb: DynamoDBClient;

  constructor(private config: { streamName: string; tableName: string }) {
    this.kinesis = new KinesisClient({});
    this.dynamodb = new DynamoDBClient({});
  }

  async logEvent(params: Omit<AuditEvent, 'eventId' | 'timestamp'>): Promise<void> {
    const event: AuditEvent = { eventId: uuidv4(), timestamp: new Date().toISOString(), ...params };
    await Promise.all([this.persistToDynamoDB(event), this.sendToKinesis(event)]);
  }

  private async persistToDynamoDB(event: AuditEvent): Promise<void> {
    const sevenYears = 7 * 365 * 24 * 60 * 60;
    await this.dynamodb.send(new PutItemCommand({
      TableName: this.config.tableName,
      Item: { pk: { S: `EVENT#${event.eventId}` }, sk: { S: event.timestamp }, data: { S: JSON.stringify(event) }, ttl: { N: String(Math.floor(Date.now() / 1000) + sevenYears) } },
      ConditionExpression: 'attribute_not_exists(pk)'
    }));
  }

  private async sendToKinesis(event: AuditEvent): Promise<void> {
    await this.kinesis.send(new PutRecordCommand({
      StreamName: this.config.streamName,
      Data: Buffer.from(JSON.stringify(event)),
      PartitionKey: event.actor.userId
    }));
  }
}
```

---

## 6. Data Masking

### Servicio de enmascaramiento

```typescript
type DataType = 'PAN' | 'EMAIL' | 'PHONE' | 'SSN' | 'NAME';

export class DataMaskingService {
  private strategies: Map<DataType, (value: string) => string>;

  constructor() {
    this.strategies = new Map([
      ['PAN', (pan) => pan.length < 4 ? '****' : '*'.repeat(pan.length - 4) + pan.slice(-4)],
      ['EMAIL', (email) => { const [local, domain] = email.split('@'); return `${local[0]}***${local[local.length - 1]}@${domain}`; }],
      ['PHONE', (phone) => { const digits = phone.replace(/\D/g, ''); return `***-***-${digits.slice(-4)}`; }],
      ['SSN', (ssn) => { const digits = ssn.replace(/\D/g, ''); return `***-**-${digits.slice(-4)}`; }],
      ['NAME', (name) => name.split(' ').map(p => p.length <= 2 ? p : `${p[0]}${'*'.repeat(p.length - 1)}`).join(' ')]
    ]);
  }

  mask(value: string | null | undefined, type: DataType): string {
    if (!value) return '';
    const strategy = this.strategies.get(type);
    return strategy ? strategy(value) : value;
  }

  maskObject<T extends object>(obj: T, fields: Partial<Record<keyof T, DataType>>): T {
    const masked = { ...obj };
    for (const [field, type] of Object.entries(fields)) {
      if (field in masked && typeof masked[field as keyof T] === 'string') {
        (masked as any)[field] = this.mask(masked[field as keyof T] as string, type as DataType);
      }
    }
    return masked;
  }
}
```

---

## Reglas Importantes

- **mTLS**: Nunca deshabilitar `rejectUnauthorized` en producción
- **Secrets**: Inicializar servicios fuera del handler para reutilizar entre invocaciones
- **PCI-DSS**: Nunca loguear datos de tarjeta sin sanitización; CVV nunca se almacena
- **SOC2**: Retención de 7 años; usar `ConditionExpression` para inmutabilidad
- **Data Masking**: Considerar contexto (logs vs response) al enmascarar
- **Claves**: Limpiar claves de encriptación de memoria después de uso
