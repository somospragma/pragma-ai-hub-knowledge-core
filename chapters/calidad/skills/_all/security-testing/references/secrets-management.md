# Secrets Management — Inyección de credenciales en suites de prueba

Las suites Karate, k6, Playwright y Appium necesitan tokens, API keys, certs y credenciales de servicio. **Nunca** se commitean en el repositorio. Esta es la política y las herramientas estándar del chapter.

## Regla cero

- **NUNCA** commitear: tokens, API keys, refresh tokens, claves privadas (`.pem`, `.p12`, `.key`), `.env` con valores reales, dumps de DB, archivos `kubeconfig`, credenciales de proveedores cloud.
- **NUNCA** loguear secretos a stdout/CI logs (los runners archivan logs por días).
- **NUNCA** usar credenciales de producción en ambientes de prueba.
- Si un secreto se filtra accidentalmente: rotar **inmediatamente** y proceder con incident response.

## Herramientas estándar

| Herramienta              | Caso de uso                                       |
|--------------------------|---------------------------------------------------|
| **SOPS + age/AWS KMS**   | Secretos versionados (cifrados) en el mismo repo  |
| **HashiCorp Vault**      | Cliente con Vault corporativo; secret per-env     |
| **AWS Secrets Manager**  | Cliente sobre AWS; integración nativa con IAM     |
| **GCP Secret Manager**   | Cliente sobre GCP                                 |
| **GitHub OIDC**          | Federar identidad runner → cloud sin static creds |
| **GitHub Secrets**       | Inyección simple en GitHub Actions                |
| **1Password CLI**        | Desarrollo local, secretos individuales           |

## SOPS + age

Cifra archivos YAML/JSON/ENV con claves age (o AWS KMS, GCP KMS, etc.) y los commitea encriptados.

```bash
# Setup
brew install sops age
age-keygen -o ~/.config/sops/age/keys.txt

# .sops.yaml
creation_rules:
  - path_regex: secrets/.*\.yaml$
    age: age1xyz...

# Encriptar
sops -e -i secrets/dev.yaml

# Desencriptar en runtime
sops -d secrets/dev.yaml > /tmp/dev.yaml
```

En CI (GitHub Actions):

```yaml
- name: Decrypt secrets
  env:
    SOPS_AGE_KEY: ${{ secrets.SOPS_AGE_KEY }}
  run: |
    mkdir -p ~/.config/sops/age
    echo "$SOPS_AGE_KEY" > ~/.config/sops/age/keys.txt
    sops -d secrets/dev.yaml > secrets/dev.decrypted.yaml
```

## Vault

```bash
# Login al runner via JWT/OIDC (no token estático)
vault write auth/jwt/login role=qa-runner jwt="$ACTIONS_ID_TOKEN_REQUEST_TOKEN"

# Leer un secreto
TOKEN=$(vault kv get -field=api_token secret/qa/dev/api)
export API_TOKEN="$TOKEN"
```

## AWS Secrets Manager + GitHub OIDC

GitHub OIDC permite que el runner asuma un rol AWS sin guardar `AWS_ACCESS_KEY_ID` estática.

```yaml
permissions:
  id-token: write
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/qa-runner
          aws-region: us-east-1
      - name: Fetch secret
        run: |
          export API_TOKEN=$(aws secretsmanager get-secret-value \
            --secret-id qa/dev/api-token --query SecretString --output text)
          echo "::add-mask::$API_TOKEN"
          echo "API_TOKEN=$API_TOKEN" >> $GITHUB_ENV
```

## Rotación

| Tipo                       | Frecuencia recomendada                  |
|----------------------------|-----------------------------------------|
| API tokens de prueba       | 90 días                                 |
| Service accounts cloud     | 90 días                                 |
| Certificados mTLS          | Antes de expiración del cert            |
| Refresh tokens             | Rotación automática (OAuth2)            |
| Claves SOPS (age)          | Anual o ante rotación de personas       |
| Tras incidente             | Inmediato                               |

## Inyección a cada framework

### Karate

`karate-config.js` lee de `karate.properties` y `env`:

```javascript
function fn() {
  return {
    baseUrl: karate.properties['base.url'] || 'https://api-dev.example.com',
    apiToken: karate.properties['api.token'] || java.lang.System.getenv('API_TOKEN'),
  };
}
```

En CI:

```bash
mvn test -Dapi.token="$API_TOKEN"
```

### k6

k6 lee variables de entorno con `__ENV`:

```javascript
import http from 'k6/http';

export default function () {
  http.get(`${__ENV.BASE_URL}/me`, {
    headers: { Authorization: `Bearer ${__ENV.API_TOKEN}` },
  });
}
```

Ejecución:

```bash
BASE_URL=https://api-dev.example.com API_TOKEN="$API_TOKEN" k6 run script.js
```

### Playwright

`playwright.config.ts` + `process.env`:

```typescript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    baseURL: process.env.BASE_URL,
    extraHTTPHeaders: {
      Authorization: `Bearer ${process.env.API_TOKEN ?? ''}`,
    },
  },
});
```

### Appium / Java

Variables de entorno via `System.getenv`:

```java
public class Config {
  public static final String API_TOKEN = System.getenv("API_TOKEN");
  public static final String DEVICE_FARM_TOKEN = System.getenv("DEVICE_FARM_TOKEN");
}
```

## Detección de secretos commiteados

Hooks de pre-commit y CI:

- **gitleaks** (`gitleaks protect --staged`) — pre-commit local.
- **trufflehog** — escaneo profundo en PR.
- **GitHub secret scanning** — habilitado a nivel org.

```yaml
- name: gitleaks
  uses: gitleaks/gitleaks-action@v2
```

## Restricciones

- Ningún secreto en repositorio en claro. Si SOPS/Vault no están disponibles, usa GitHub Secrets como mínimo.
- Las suites deben fallar **temprano y explícitamente** si un secreto requerido no está presente (no caer en defaults inseguros).
- Encadena con `[[calidad-mandatory-inputs-protocol]]` para confirmar la ruta de secretos al inicio de la conversación.
