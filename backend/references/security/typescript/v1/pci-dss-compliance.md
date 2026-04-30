<!-- keywords: pci-dss, compliance, pan encryption, sanitization middleware, card validation, typescript, nodejs -->
# PCI-DSS Compliance - TypeScript Implementation

## Purpose

Implement PCI-DSS compliance controls in Node.js/TypeScript using AWS SDK, including PAN encryption, sanitization middleware, and card data validation.

## Scope of Application

- When developing payment services in Node.js.
- When PCI-compliant encryption needs to be implemented.
- To configure sensitive data sanitization middleware.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "@aws-sdk/client-kms": "^3.400.0",
    "express": "^4.18.0",
    "class-validator": "^0.14.0"
  }
}
```

### Implementation

```typescript
// PCI-compliant encryption service
import { KMSClient, EncryptCommand, DecryptCommand } from '@aws-sdk/client-kms';
import crypto from 'crypto';

interface EncryptedData {
  ciphertext: string;
  iv: string;
  authTag: string;
  keyId: string;
}

export class PciEncryptionService {
  private kmsClient: KMSClient;
  private keyId: string;

  constructor(keyId: string) {
    this.kmsClient = new KMSClient({});
    this.keyId = keyId;
  }

  async encryptPan(pan: string): Promise<EncryptedData> {
    // Generate DEK (Data Encryption Key) with KMS
    const dataKey = await this.generateDataKey();
    
    // Encrypt PAN with AES-256-GCM
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', dataKey.plaintext, iv);
    
    let ciphertext = cipher.update(pan, 'utf8', 'base64');
    ciphertext += cipher.final('base64');
    const authTag = cipher.getAuthTag();

    // Clear key from memory
    dataKey.plaintext.fill(0);

    return {
      ciphertext,
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64'),
      keyId: dataKey.encryptedKey
    };
  }

  async decryptPan(encrypted: EncryptedData): Promise<string> {
    // Decrypt DEK with KMS
    const dataKey = await this.decryptDataKey(encrypted.keyId);
    
    // Decrypt PAN
    const decipher = crypto.createDecipheriv(
      'aes-256-gcm',
      dataKey,
      Buffer.from(encrypted.iv, 'base64')
    );
    decipher.setAuthTag(Buffer.from(encrypted.authTag, 'base64'));
    
    let pan = decipher.update(encrypted.ciphertext, 'base64', 'utf8');
    pan += decipher.final('utf8');
    
    // Clear key from memory
    dataKey.fill(0);
    
    return pan;
  }

  private async generateDataKey(): Promise<{ plaintext: Buffer; encryptedKey: string }> {
    const command = new GenerateDataKeyCommand({
      KeyId: this.keyId,
      KeySpec: 'AES_256'
    });
    const response = await this.kmsClient.send(command);
    
    return {
      plaintext: Buffer.from(response.Plaintext!),
      encryptedKey: Buffer.from(response.CiphertextBlob!).toString('base64')
    };
  }

  private async decryptDataKey(encryptedKey: string): Promise<Buffer> {
    const command = new DecryptCommand({
      CiphertextBlob: Buffer.from(encryptedKey, 'base64')
    });
    const response = await this.kmsClient.send(command);
    return Buffer.from(response.Plaintext!);
  }
}
```

```typescript
// Sanitization middleware for Express
import { Request, Response, NextFunction } from 'express';

const PAN_REGEX = /\b(?:\d{4}[-\s]?){3}\d{4}\b/g;
const SENSITIVE_FIELDS = ['pan', 'cardNumber', 'cvv', 'cvc', 'securityCode'];

export function pciSanitizationMiddleware(
  req: Request, 
  res: Response, 
  next: NextFunction
): void {
  // Sanitize body for logs
  const sanitizedBody = sanitizeObject(req.body);
  (req as any).sanitizedBody = sanitizedBody;
  
  // Intercept res.json to sanitize responses in logs
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
    if (SENSITIVE_FIELDS.includes(key.toLowerCase())) {
      sanitized[key] = '[REDACTED]';
    } else if (typeof value === 'string') {
      sanitized[key] = value.replace(PAN_REGEX, '[PAN-REDACTED]');
    } else if (typeof value === 'object') {
      sanitized[key] = sanitizeObject(value);
    } else {
      sanitized[key] = value;
    }
  }
  
  return sanitized;
}
```

```typescript
// Luhn validator
export function validateLuhn(pan: string): boolean {
  const digits = pan.replace(/\D/g, '');
  
  if (digits.length < 13 || digits.length > 19) {
    return false;
  }
  
  let sum = 0;
  let alternate = false;
  
  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10);
    
    if (alternate) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    
    sum += digit;
    alternate = !alternate;
  }
  
  return sum % 10 === 0;
}

// Card data DTO
export interface CardData {
  pan: string;
  expiryMonth: number;
  expiryYear: number;
  cvv: string;
}

export function maskPan(pan: string): string {
  if (!pan || pan.length < 4) return '****';
  return '*'.repeat(pan.length - 4) + pan.slice(-4);
}
```

### Configuration

```typescript
// config/pci.config.ts
export const pciConfig = {
  kmsKeyId: process.env.KMS_KEY_ID!,
  tokenPrefix: 'tok_',
  panMaskChar: '*',
  allowedBins: process.env.ALLOWED_BINS?.split(',') || []
};
```

## Important Rules

- Never log card data without sanitization.
- Clear encryption keys from memory after use.
- CVV must never be stored or transmitted to the backend.
- Use `JSON.stringify` with sanitization for logs.

## Example

```typescript
// Encryption service usage
import { PciEncryptionService } from './pci-encryption';
import { validateLuhn, maskPan } from './validators';

const encryptionService = new PciEncryptionService(process.env.KMS_KEY_ID!);

async function processCard(pan: string): Promise<{ token: string; masked: string }> {
  if (!validateLuhn(pan)) {
    throw new Error('Invalid PAN');
  }
  
  const encrypted = await encryptionService.encryptPan(pan);
  const token = `tok_${crypto.randomUUID().replace(/-/g, '')}`;
  
  // Store token -> encrypted mapping
  await tokenStore.save(token, encrypted);
  
  return {
    token,
    masked: maskPan(pan)
  };
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
