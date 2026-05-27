# Pact Broker / Pactflow — Setup y `can-i-deploy`

El broker es el corazón de la operación Pact: almacena pacts, registra resultados de verificación, y bloquea deploys incompatibles.

## Pactflow (SaaS managed) vs Pact Broker self-hosted

| Característica                       | Pactflow (managed)        | Pact Broker self-hosted    |
| ------------------------------------ | ------------------------- | -------------------------- |
| Setup                                | Trivial (registrar cuenta)| Docker + Postgres          |
| Mantenimiento                        | Cero                      | Updates, backups, monitoring |
| SSO/SAML                             | Si (Enterprise)           | Manual (depende del despliegue)|
| Visualizations (network graph)       | Si                        | Limitadas                  |
| Audit log                            | Si                        | Manual                     |
| Costo                                | $$ (per pacticipant)      | Solo infra                 |
| On-premise (compliance regulada)     | No                        | Si                         |

**Recomendación Pragma:**
- Clientes pequeños / proyectos iniciales: **Pactflow Starter** (free tier).
- Clientes enterprise con muchos pacticipants: **Pactflow Enterprise**.
- Clientes bancarios con datos sensibles que no pueden salir on-premise: **Self-hosted en Kubernetes**.

## Self-hosted con Docker

```yaml
# docker-compose.yml
version: '3'
services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_USER: pact
      POSTGRES_PASSWORD: pact
      POSTGRES_DB: pact
    volumes:
      - pact-pg:/var/lib/postgresql/data

  pact-broker:
    image: pactfoundation/pact-broker:latest
    ports:
      - "9292:9292"
    environment:
      PACT_BROKER_DATABASE_URL: "postgres://pact:pact@postgres/pact"
      PACT_BROKER_BASIC_AUTH_USERNAME: admin
      PACT_BROKER_BASIC_AUTH_PASSWORD: ${BROKER_ADMIN_PASS}
      PACT_BROKER_BASIC_AUTH_READ_ONLY_USERNAME: readonly
      PACT_BROKER_BASIC_AUTH_READ_ONLY_PASSWORD: ${BROKER_RO_PASS}
    depends_on:
      - postgres

volumes:
  pact-pg:
```

Para producción: Helm chart `pact-broker` en Kubernetes con backup automatizado de Postgres.

## Publicar contratos

```bash
# Desde consumer CI
pact-broker publish ./pacts \
  --consumer-app-version $(git rev-parse HEAD) \
  --branch $(git rev-parse --abbrev-ref HEAD) \
  --tag $(git rev-parse --abbrev-ref HEAD) \
  --broker-base-url https://pactflow.cliente.io \
  --broker-token $PACT_BROKER_TOKEN
```

**Convenciones de versioning:**
- `--consumer-app-version`: SHA del commit (inmutable).
- `--branch`: nombre del branch (mutable, indica latest del branch).
- `--tag`: tag adicional (`feature/X`, `prod`, `qa`).

## Promoción a ambientes (recommended workflow)

En lugar de tags ad-hoc, usar el modelo de **environments** + `record-deployment` / `record-release` (Pactflow workflow moderno):

```bash
# Crear ambiente (una vez)
pact-broker create-environment --name prod --production

# Cuando deploy exitoso en prod:
pact-broker record-deployment \
  --pacticipant web-app \
  --version $(git rev-parse HEAD) \
  --environment prod
```

Esto reemplaza el viejo modelo de tags (`stage`, `prod`) por estado real de deployment.

## Webhooks — re-verificación automática

Cuando un consumer publica un pact nuevo, el broker dispara un webhook al provider para que re-verifique:

```bash
pact-broker create-webhook \
  https://github.com/org/users-service/dispatches \
  --request POST \
  --header "Authorization: Bearer $GH_TOKEN" \
  --header "Accept: application/vnd.github.v3+json" \
  --data '{"event_type":"contract-changed","client_payload":{"pact_url":"${pactbroker.pactUrl}"}}' \
  --provider users-service \
  --contract-content-changed
```

GitHub Actions recibe el `repository_dispatch` y corre el verifier contra el nuevo pact.

```yaml
on:
  repository_dispatch:
    types: [contract-changed]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: mvn pact:verify -Dpact.url=${{ github.event.client_payload.pact_url }}
```

## `can-i-deploy` — el gate clave

Antes de deploy a un ambiente, preguntar al broker si la versión es compatible con TODAS sus dependencias en ese ambiente:

```bash
pact-broker can-i-deploy \
  --pacticipant web-app \
  --version $(git rev-parse HEAD) \
  --to-environment prod \
  --broker-base-url https://pactflow.cliente.io \
  --broker-token $PACT_BROKER_TOKEN
```

Exit code 0 = puede deployar; no-zero = bloquea el deploy.

Casos que bloquea:
- Consumer cambió y no existe verification result del provider para el nuevo pact.
- Provider cambió y no verifica un pact existente del consumer en prod.
- Falta verification del pacticipant a verificar.

## Pipeline con can-i-deploy (GitHub Actions)

```yaml
deploy-prod:
  needs: [build, test]
  steps:
    - name: Can I deploy?
      run: |
        npx @pact-foundation/pact-cli broker can-i-deploy \
          --pacticipant=web-app \
          --version=${{ github.sha }} \
          --to-environment=prod \
          --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
          --broker-token=${{ secrets.PACT_BROKER_TOKEN }}

    - name: Deploy
      run: ./deploy.sh prod

    - name: Record deployment
      run: |
        npx @pact-foundation/pact-cli broker record-deployment \
          --pacticipant=web-app \
          --version=${{ github.sha }} \
          --environment=prod \
          --broker-base-url=${{ secrets.PACT_BROKER_URL }} \
          --broker-token=${{ secrets.PACT_BROKER_TOKEN }}
```

## Anti-patterns

- Publicar pacts de branches feature al `prod` tag — contamina los gates.
- `can-i-deploy` solo en el consumer — el provider también debe correrlo antes de deploy.
- Self-hosted sin backup automatizado — perder Postgres = perder toda la historia de contratos.
- No usar webhooks — los providers verifican manualmente y los breaking changes se detectan tarde.
- Tags ad-hoc en lugar de environments — pierde el modelo de deployment real.
