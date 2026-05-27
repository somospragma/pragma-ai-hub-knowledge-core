# Secrets en Pipelines — Gestión Segura por Plataforma

Los secretos (`BASE_URL` privadas, `AUTH_TOKEN`, claves de cloud providers, credenciales de devices) NUNCA se commiten en YAML. Cada plataforma CI/CD tiene mecanismos nativos + integración con secret stores externos.

## Azure DevOps

### Variable Groups + Azure Key Vault

```yaml
variables:
  - group: qa-secrets-prod  # variable group ligado a Key Vault

steps:
  - script: |
      echo "Base URL: $BASE_URL"  # OK, llega del group
      curl -H "Authorization: Bearer $AUTH_TOKEN" $BASE_URL/api/health
    env:
      BASE_URL: $(BASE_URL)
      AUTH_TOKEN: $(AUTH_TOKEN)
```

Setup en Azure DevOps UI:
1. `Pipelines > Library > Variable Groups > New`.
2. `Link secrets from Azure Key Vault as variables`.
3. Seleccionar la vault, autorizar el service connection.
4. Importar variables específicas (NO toda la vault).

### Variables secretas locales (sin Key Vault)

Para clientes sin Azure: variables en `Library > Variable Groups` con el toggle **Keep this value secret** activado. Aparecen como `***` en logs.

### NUNCA

```yaml
# MAL - secret hardcodeado
- script: curl -H "Authorization: Bearer eyJhbGc..." $URL

# MAL - log del secret
- script: echo $AUTH_TOKEN  # incluso si es secret, esto lo expone

# MAL - secret en parameter inline
- task: SomeTask@1
  inputs:
    token: 'eyJhbGc...'
```

## GitHub Actions

### Secrets nativos

```yaml
steps:
  - name: Call API
    env:
      BASE_URL: ${{ secrets.BASE_URL }}
      AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}
    run: |
      curl -H "Authorization: Bearer $AUTH_TOKEN" $BASE_URL/api/health
```

Setup: `Settings > Secrets and variables > Actions > New repository secret`.

### Environments con required reviewers

Para secretos de producción:

```yaml
jobs:
  deploy:
    environment: production  # requiere approval manual
    steps:
      - env:
          PROD_TOKEN: ${{ secrets.PROD_TOKEN }}
        run: ./deploy.sh
```

Setup: `Settings > Environments > production > Required reviewers`.

### OIDC para AWS / GCP / Azure (sin static credentials)

Mecanismo recomendado: GitHub emite un token OIDC corto que la nube intercambia por credenciales temporales. **No hay credenciales estáticas en GitHub Secrets**.

```yaml
permissions:
  id-token: write   # OBLIGATORIO para OIDC
  contents: read

steps:
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
      aws-region: us-east-1
      # NO usar access keys

  - run: aws s3 ls  # ya autenticado con creds temporales
```

Equivalente Azure:
```yaml
- uses: azure/login@v2
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    # NO usar client-secret — el role acepta OIDC
```

### Mascarado automático

GitHub Actions enmascara automáticamente cualquier valor de `secrets.X` que aparezca en logs. Pero si el secret es transformado (ej. `echo $TOKEN | base64`), el mascarado se pierde.

```yaml
# MAL
- run: echo $AUTH_TOKEN | base64  # base64 del token aparece en log

# BIEN
- run: |
    ENCODED=$(echo -n $AUTH_TOKEN | base64)
    echo "::add-mask::$ENCODED"  # registrar nuevo mascarado
    # ahora $ENCODED también queda enmascarado
```

## GitLab CI

### Masked + Protected variables

```yaml
# .gitlab-ci.yml
job:
  script:
    - curl -H "Authorization: Bearer $AUTH_TOKEN" $BASE_URL/api/health
```

Setup: `Settings > CI/CD > Variables`:
- **Masked**: oculta el valor en logs (requiere base64-like format, sin espacios).
- **Protected**: solo disponible en branches protected (típicamente `main`, `production`).
- **Expand variable reference**: desactivar si el valor contiene `$`.

### Integración HashiCorp Vault

```yaml
job:
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.cliente.com
  script:
    - export VAULT_TOKEN=$(vault write -field=token auth/jwt/login role=qa-pipeline jwt=$VAULT_ID_TOKEN)
    - export AUTH_TOKEN=$(vault kv get -field=token secret/qa/api)
    - curl -H "Authorization: Bearer $AUTH_TOKEN" $BASE_URL
```

Vault valida el JWT OIDC emitido por GitLab y devuelve un token Vault, que luego lee el secret real. **No hay credenciales estáticas en GitLab.**

## Inyección de variables runtime — `BASE_URL`, `AUTH_TOKEN`, `BACKEND_URL`

Para que las suites usen estos valores:

### Karate (`karate-config.js`)

```javascript
function fn() {
  var env = karate.env || 'qa';
  var config = {
    baseUrl: karate.properties['base.url'] || java.lang.System.getenv('BASE_URL'),
    authToken: karate.properties['auth.token'] || java.lang.System.getenv('AUTH_TOKEN'),
  };
  return config;
}
```

### Playwright (`playwright.config.ts`)

```typescript
export default defineConfig({
  use: {
    baseURL: process.env.BASE_URL,
    extraHTTPHeaders: {
      Authorization: `Bearer ${process.env.AUTH_TOKEN}`,
    },
  },
});
```

### K6 (variables de entorno)

```javascript
const BASE_URL = __ENV.BASE_URL;
const AUTH_TOKEN = __ENV.AUTH_TOKEN;
```

```bash
k6 run --env BASE_URL=$BASE_URL --env AUTH_TOKEN=$AUTH_TOKEN load.js
```

## Tabla resumen

| Plataforma     | Mecanismo simple        | Mecanismo recomendado            | OIDC nube       |
| -------------- | ----------------------- | -------------------------------- | --------------- |
| Azure DevOps   | Variable Groups secret  | Key Vault linked Group           | Workload Identity Federation |
| GitHub Actions | Repository Secrets      | Environments + OIDC              | Sí, nativo      |
| GitLab CI      | Masked + Protected vars | id_tokens + HashiCorp Vault      | Sí, JWT OIDC    |

## Anti-patterns

- `echo $TOKEN` — visible en log incluso si el secret está enmascarado (la salida ya tuvo el valor antes del mascarado).
- Commit de `.env` con tokens reales — git history es permanente; rotar el secret inmediatamente si ocurre.
- Variables no-protected en branches no-protected — un atacante con push a feature branch puede leerlas.
- Service principals con secret en lugar de OIDC — secretos rotables manualmente y leakeables.

## Cross-link con security

Sigue `[[calidad-security-testing]]` para auditoría de secret leakage en pipelines. Combinar con `gitleaks` o `truffleHog` como pre-commit hook + CI step.
