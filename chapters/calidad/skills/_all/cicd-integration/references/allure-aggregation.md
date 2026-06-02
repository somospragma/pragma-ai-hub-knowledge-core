# Allure — Agregación de Reportes por Tecnología

Allure es el dashboard de reportes por defecto en Pragma. Centraliza resultados de múltiples frameworks en una sola UI navegable.

## Karate — `karate-junit5` + Allure JUnit5 adapter

```xml
<!-- pom.xml -->
<dependency>
    <groupId>io.qameta.allure</groupId>
    <artifactId>allure-junit5</artifactId>
    <version>2.27.0</version>
    <scope>test</scope>
</dependency>

<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <configuration>
        <argLine>
            -javaagent:"${settings.localRepository}/org/aspectj/aspectjweaver/1.9.20/aspectjweaver-1.9.20.jar"
        </argLine>
        <systemPropertyVariables>
            <allure.results.directory>${project.build.directory}/allure-results</allure.results.directory>
        </systemPropertyVariables>
    </configuration>
</plugin>
```

Después de la ejecución:
```bash
allure generate target/allure-results --clean -o allure-report
```

## Playwright — `allure-playwright`

```bash
npm i -D allure-playwright
```

```typescript
// playwright.config.ts
export default defineConfig({
  reporter: [
    ['list'],
    ['allure-playwright', {
      detail: true,
      outputFolder: 'allure-results',
      suiteTitle: false,
    }],
  ],
});
```

```typescript
// uso en test
import { allure } from 'allure-playwright';

test('login', async ({ page }) => {
  allure.epic('Auth');
  allure.feature('Login');
  allure.severity('critical');
  // ...
});
```

## K6 — `xk6-allure`

K6 no soporta Allure nativamente; usar el binario custom `xk6-allure`.

```bash
# Build custom k6 con extensión
xk6 build --with github.com/wisaitas/xk6-allure

# Ejecutar
./k6 run --out allure=allure-results load.js
```

Alternativa: convertir summary JSON a Allure-compatible XML con script propio.

## Appium — Serenity + Allure XML

Si la suite usa Serenity BDD (común en Pragma Mobile), Serenity genera reportes JSON que se convierten a Allure:

```xml
<dependency>
    <groupId>io.qameta.allure</groupId>
    <artifactId>allure-junit5</artifactId>
</dependency>
<dependency>
    <groupId>net.serenity-bdd</groupId>
    <artifactId>serenity-rest-assured</artifactId>
</dependency>
```

```gradle
// build.gradle
test {
    systemProperty 'allure.results.directory', "$buildDir/allure-results"
}
```

## Agregación multi-tecnología en pipeline

Ejecutar todas las suites, descargar artifacts, generar Allure consolidado.

### Azure DevOps

```yaml
- stage: AllureReport
  dependsOn: [Karate, Playwright, K6, Appium]
  jobs:
    - job: Aggregate
      steps:
        - download: current
          patterns: '**/allure-results/**'

        - script: |
            mkdir -p combined-results
            cp -r $(Pipeline.Workspace)/*/allure-results/* combined-results/
            allure generate combined-results --clean -o allure-report
          displayName: Generate Allure report

        - task: PublishPipelineArtifact@1
          inputs:
            targetPath: 'allure-report'
            artifact: 'allure-html-report'
```

### GitHub Actions con allure-action

```yaml
- uses: simple-elf/allure-report-action@v1.7
  if: always()
  with:
    allure_results: combined-results
    allure_history: allure-history
    gh_pages: gh-pages
```

## Categories.json — clasificar fallos automáticamente

Colocar `categories.json` en `allure-results/` para agrupar fallos por causa:

```json
[
  {
    "name": "Infrastructure failures",
    "matchedStatuses": ["broken"],
    "messageRegex": ".*(ConnectException|UnknownHostException|TimeoutException).*"
  },
  {
    "name": "Authentication failures",
    "matchedStatuses": ["failed"],
    "messageRegex": ".*(401|403|token expired).*"
  },
  {
    "name": "Schema mismatches",
    "matchedStatuses": ["failed"],
    "messageRegex": ".*(match failed|schema validation).*"
  },
  {
    "name": "Visual regression",
    "matchedStatuses": ["failed"],
    "messageRegex": ".*Screenshot comparison failed.*"
  }
]
```

Esto permite leer el reporte por **tipo de fallo** en lugar de uno por uno — clave para triage rápido en suites grandes.

## Allure Server vs artifact estático

| Modo               | Cuándo usar                                                |
| ------------------ | ---------------------------------------------------------- |
| Artifact estático  | PR builds, nightly ad-hoc, evidencia puntual               |
| Allure Server      | Cliente con history tracking (tendencias, flakiness)       |
| GitHub Pages       | Repos públicos o internos sin Allure Server                |

Para Allure Server (self-hosted Docker), publicar con curl:

```bash
curl -X POST "https://allure.cliente.com/api/result" \
  -F "files[]=@allure-results.zip"
```

## Cross-link con evidencia

El reporte Allure es **evidencia auditable** según `[[calidad-test-evidence-and-traceability]]` — debe quedar archivado con retención según política del cliente (mínimo 90 días en producción).
