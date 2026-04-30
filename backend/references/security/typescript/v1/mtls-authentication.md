<!-- keywords: mtls, mutual tls, certificate, authentication, https, axios, typescript, nodejs -->
# mTLS Authentication - TypeScript Implementation

## Purpose

Implement Mutual TLS (mTLS) authentication in Node.js/TypeScript using the native https module and axios for secure HTTP clients.

## Scope of Application

- When developing Node.js microservices that require secure communication.
- When configuring Express servers with client certificate validation.
- To implement HTTP clients with mutual certificates.

## Main Content

### Dependencies

```json
{
  "dependencies": {
    "axios": "^1.6.0",
    "express": "^4.18.0",
    "@types/node": "^20.0.0"
  }
}
```

### Implementation

```typescript
// mTLS client with Node.js
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

  return axios.create({
    httpsAgent,
    timeout: 30000
  });
}
```

```typescript
// Express server with mTLS
import express, { Request, Response, NextFunction } from 'express';
import https from 'https';
import fs from 'fs';

const app = express();

// Client certificate validation middleware
app.use((req: Request, res: Response, next: NextFunction) => {
  const cert = (req.socket as any).getPeerCertificate();
  
  if (!cert || Object.keys(cert).length === 0) {
    return res.status(401).json({ error: 'Client certificate required' });
  }
  
  if (!(req as any).client.authorized) {
    return res.status(403).json({ error: 'Unauthorized certificate' });
  }
  
  // Add CN to request for later use
  (req as any).clientCN = cert.subject.CN;
  next();
});

// HTTPS server configuration with mTLS
const serverOptions: https.ServerOptions = {
  cert: fs.readFileSync('/certs/server.crt'),
  key: fs.readFileSync('/certs/server.key'),
  ca: fs.readFileSync('/certs/ca.crt'),
  requestCert: true,
  rejectUnauthorized: true
};

const server = https.createServer(serverOptions, app);

server.listen(443, () => {
  console.log('mTLS server listening on port 443');
});
```

```typescript
// Certificate validator with whitelist
interface CertificateInfo {
  subject: {
    CN: string;
    O?: string;
  };
  issuer: {
    CN: string;
  };
  valid_from: string;
  valid_to: string;
}

export class CertificateValidator {
  private allowedCNs: Set<string>;

  constructor(allowedClients: string[]) {
    this.allowedCNs = new Set(allowedClients);
  }

  validate(cert: CertificateInfo): void {
    // Verify CN is in the whitelist
    if (!this.allowedCNs.has(cert.subject.CN)) {
      throw new Error(`Unauthorized client: ${cert.subject.CN}`);
    }

    // Verify expiration
    const validTo = new Date(cert.valid_to);
    if (validTo < new Date()) {
      throw new Error('Expired certificate');
    }
  }

  isAuthorized(cn: string): boolean {
    return this.allowedCNs.has(cn);
  }
}
```

### Configuration

```typescript
// config/mtls.config.ts
export const mtlsConfig = {
  server: {
    certPath: process.env.SERVER_CERT_PATH || '/certs/server.crt',
    keyPath: process.env.SERVER_KEY_PATH || '/certs/server.key',
    caPath: process.env.CA_CERT_PATH || '/certs/ca.crt'
  },
  client: {
    certPath: process.env.CLIENT_CERT_PATH || '/certs/client.crt',
    keyPath: process.env.CLIENT_KEY_PATH || '/certs/client.key',
    caPath: process.env.CA_CERT_PATH || '/certs/ca.crt'
  },
  allowedClients: (process.env.ALLOWED_CLIENTS || 'service-a,service-b').split(',')
};
```

## Important Rules

- Never disable `rejectUnauthorized` in production.
- Load certificates securely from Secrets Manager in cloud environments.
- Implement mTLS connection logging for auditing.
- Always validate the client certificate CN.

## Example

```typescript
// mTLS client usage
import { createMtlsClient } from './mtls-client';
import { mtlsConfig } from './config/mtls.config';

const client = createMtlsClient({
  certPath: mtlsConfig.client.certPath,
  keyPath: mtlsConfig.client.keyPath,
  caPath: mtlsConfig.client.caPath
});

async function callSecureService(): Promise<void> {
  try {
    const response = await client.get('https://api.internal.example.com/data');
    console.log('Response:', response.data);
  } catch (error) {
    console.error('mTLS call error:', error);
  }
}
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
