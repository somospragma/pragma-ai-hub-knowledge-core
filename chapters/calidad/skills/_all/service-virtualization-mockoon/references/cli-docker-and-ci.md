
# CLI, Docker y CI

Componente: `@mockoon/cli` (npm, requiere Node >= 18). Mismo data file que la app desktop. Comandos: `start`, `import`, `export`, `validate`, `dockerize`.

## Local

```bash
npm install -g @mockoon/cli

# Levantar (foreground)
mockoon-cli start --data mocks/mockoon/environment.json --port 3010 \
  --faker-seed 12345 --admin-api-token "$MOCKOON_ADMIN_API_TOKEN"

# Background: NO existe `mockoon-cli stop` (el modo demonio se eliminó en v4).
mockoon-cli start --data mocks/mockoon/environment.json --port 3010 & 
MOCK_PID=$!
# ... correr la suite ...
kill $MOCK_PID
```

Flags relevantes: `--faker-locale`, `--faker-seed`, `--watch` (recarga al cambiar el data file), `--log-transaction` (log request/response completo — solo para debug), `--repair` (migra data files de versiones viejas), `--disable-admin-api`.

## Healthcheck

No hay endpoint de health dedicado. Patrón: curl a una ruta conocida del mock con reintentos antes de arrancar la suite:

```bash
for i in $(seq 1 15); do
  curl -sf http://localhost:3010/api/health-probe && break
  sleep 1
done
```

(Declarar una ruta `GET /health-probe` estática en el environment para este fin.)

## Docker

Imagen oficial `mockoon/cli` (base node alpine):

```bash
docker run -d --name sut-mock \
  --mount type=bind,source="$PWD/mocks/mockoon/environment.json",target=/data/environment.json,readonly \
  -p 3010:3010 mockoon/cli:latest --data /data/environment.json --port 3010

# Detener
docker stop sut-mock && docker rm sut-mock
```

`mockoon-cli dockerize --data mocks/mockoon/environment.json --port 3010 --output ./Dockerfile` genera un Dockerfile autocontenido si el pipeline prefiere build propio.

## GitHub Actions

Acción oficial (vigente: `@v3`):

```yaml
steps:
  - uses: actions/checkout@v6
  - name: Run Mockoon mock
    uses: mockoon/cli-action@v3
    with:
      version: "latest"
      data-file: "./mocks/mockoon/environment.json"
      port: 3010
      extra-args: "--faker-seed 12345"
  - name: Run suite against mock
    run: mvn test -Dkarate.env=mock
```

## Azure DevOps

Sin task oficial; usar script step o container:

```yaml
steps:
  - script: |
      npm install -g @mockoon/cli
      mockoon-cli start --data mocks/mockoon/environment.json --port 3010 --faker-seed 12345 &
      for i in $(seq 1 15); do curl -sf http://localhost:3010/api/health-probe && break; sleep 1; done
    displayName: "Start Mockoon mock"
  - script: mvn test -Dkarate.env=mock
    displayName: "Run suite against mock"
```

Integrar estos jobs en los pipelines del chapter según `[[calidad-cicd-integration]]`: el job del mock es un paso previo del stage de tests **de construcción**; los stages de certificación apuntan al ambiente real y NO levantan mock.

## Logs y evidencia

- Logs JSON (Pino) en stdout y `~/.mockoon-cli/logs/{mock-name}.log`: `requestMethod`, `requestPath`, `responseStatus`, `requestProxied`. Headers sensibles (authorization, cookie, api keys) se redactan automáticamente.
- Para "verify" de invocaciones (¿el test llamó al endpoint N veces?): consultar `GET /mockoon-admin/logs?page=1&limit=50` con el bearer token del Admin API.
- Adjuntar el log del mock a `.evidence/` cuando el triage de un fallo necesite demostrar qué recibió/respondió el mock (`[[calidad-failure-triage-and-classification]]`).
