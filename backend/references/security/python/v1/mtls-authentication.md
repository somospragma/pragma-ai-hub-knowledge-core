<!-- keywords: mtls, mutual tls, certificate, authentication, requests, fastapi, python -->
# mTLS Authentication - Python Implementation

## Purpose

Implement Mutual TLS (mTLS) authentication in Python using requests for HTTP clients and FastAPI for servers with certificate validation.

## Scope of Application

- When developing Python microservices that require secure communication.
- When configuring FastAPI servers with client certificate validation.
- To implement HTTP clients with mutual certificates.

## Main Content

### Dependencies

```txt
# requirements.txt
requests>=2.31.0
urllib3>=2.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
```

### Implementation

```python
# mTLS client with requests
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from typing import Optional

class MtlsAdapter(HTTPAdapter):
    """HTTP adapter with mTLS support."""
    
    def __init__(self, cert_path: str, key_path: str, ca_path: str):
        self.cert_path = cert_path
        self.key_path = key_path
        self.ca_path = ca_path
        super().__init__()
    
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.load_cert_chain(self.cert_path, self.key_path)
        ctx.load_verify_locations(self.ca_path)
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)


def create_mtls_session(
    cert_path: str, 
    key_path: str, 
    ca_path: str
) -> requests.Session:
    """Creates an HTTP session with mTLS configured."""
    session = requests.Session()
    adapter = MtlsAdapter(cert_path, key_path, ca_path)
    session.mount('https://', adapter)
    return session
```

```python
# FastAPI server with mTLS
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Set
import ssl

class MtlsMiddleware(BaseHTTPMiddleware):
    """Middleware for client certificate validation."""
    
    def __init__(self, app, allowed_cns: List[str]):
        super().__init__(app)
        self.allowed_cns: Set[str] = set(allowed_cns)
    
    async def dispatch(self, request: Request, call_next):
        # Get client certificate
        transport = request.scope.get('transport')
        if not transport:
            raise HTTPException(status_code=401, detail="Certificate required")
        
        client_cert = transport.get_extra_info('peercert')
        
        if not client_cert:
            raise HTTPExceptio
n(status_code=401, detail="Certificate required")
        
        # Extract CN from certificate
        cn = self._extract_cn(client_cert)
        
        if cn not in self.allowed_cns:
            raise HTTPException(
                status_code=403, 
                detail=f"Unauthorized client: {cn}"
            )
        
        # Add CN to request state
        request.state.client_cn = cn
        return await call_next(request)
    
    def _extract_cn(self, cert: dict) -> str:
        """Extracts the Common Name from the certificate."""
        subject = dict(x[0] for x in cert.get('subject', []))
        return subject.get('commonName', '')


# Application configuration
app = FastAPI()
app.add_middleware(
    MtlsMiddleware, 
    allowed_cns=['service-a', 'service-b', 'service-c']
)

@app.get("/secure-endpoint")
async def secure_endpoint(request: Request):
    return {
        "message": "Authorized access",
        "client": request.state.client_cn
    }
```

```python
# Certificate validator
from dataclasses import dataclass
from datetime import datetime
from typing import Set, Dict, Any

@dataclass
class CertificateInfo:
    cn: str
    organization: str
    valid_from: datetime
    valid_to: datetime
    issuer_cn: str

class CertificateValidator:
    """Certificate validator with whitelist."""
    
    def __init__(self, allowed_clients: list[str]):
        self.allowed_cns: Set[str] = set(allowed_clients)
    
    def validate(self, cert_dict: Dict[str, Any]) -> CertificateInfo:
        """Validates a certificate and returns its information."""
        cert_info = self._parse_certificate(cert_dict)
        
        # Verify CN against whitelist
        if cert_info.cn not in self.allowed_cns:
            raise ValueError(f"Unauthorized client: {cert_info.cn}")
        
        # Verify expiration
        if cert_info.valid_to < datetime.utcnow():
            raise ValueError("Expired certificate")
        
        return cert_info
    
    def _parse_certificate(self, cert_dict: Dict[str, Any]) -> CertificateInfo:
        subject = dict(x[0] for x in cert_dict.get('subject', []))
        issuer = dict(x[0] for x in cert_dict.get('issuer', []))
        
        return CertificateInfo(
            cn=subject.get('commonName', ''),
            organization=subject.get('organizationName', ''),
            valid_from=datetime.strptime(
                cert_dict['notBefore'], '%b %d %H:%M:%S %Y %Z'
            ),
            valid_to=datetime.strptime(
                cert_dict['notAfter'], '%b %d %H:%M:%S %Y %Z'
            ),
            issuer_cn=issuer.get('commonName', '')
        )
```

### Configuration

```python
# config.py
import os
from dataclasses import dataclass
from typing import List

@dataclass
class MtlsConfig:
    cert_path: str
    key_path: str
    ca_path: str
    allowed_clients: List[str]

def load_mtls_config() -> MtlsConfig:
    return MtlsConfig(
        cert_path=os.environ.get('CLIENT_CERT_PATH', '/certs/client.crt'),
        key_path=os.environ.get('CLIENT_KEY_PATH', '/certs/client.key'),
        ca_path=os.environ.get('CA_CERT_PATH', '/certs/ca.crt'),
        allowed_clients=os.environ.get(
            'ALLOWED_CLIENTS', 'service-a,service-b'
        ).split(',')
    )
```

## Important Rules

- Never disable certificate verification in production.
- Use environment variables for certificate paths.
- Implement mTLS connection logging for auditing.
- Handle SSL errors securely without exposing internal details.

## Example

```python
# mTLS client usage
from config import load_mtls_config

config = load_mtls_config()
session = create_mtls_session(
    cert_path=config.cert_path,
    key_path=config.key_path,
    ca_path=config.ca_path
)

# Call to secure service
response = session.get('https://api.internal.example.com/data')
print(f"Response: {response.json()}")
```

## Step by Step / Guidelines

_(No additional information required for this section.)_

## Verification Checklist

_(No additional information required for this section.)_

## Tools and Resources

_(No additional information required for this section.)_
