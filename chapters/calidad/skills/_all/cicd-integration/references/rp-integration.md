# ReportPortal — Integracion como Alternativa a Allure

ReportPortal (RP) es una plataforma de analisis de ejecucion con ML-based failure clustering, history tracking profundo e integracion con Jira/ALM.

## Cuando elegir ReportPortal vs Allure

| Criterio                             | Allure                  | ReportPortal                        |
| ------------------------------------ | ----------------------- | ----------------------------------- |
| Setup                                | Trivial (artifact HTML) | Complejo (Postgres + ES + servicios)|
| Dashboard simple por ejecucion       | Excelente               | Bueno                               |
| History tracking / tendencias        | Limitado (con server)   | Excelente                           |
| Auto-clustering de fallos (AI/ML)    | No                      | Si                                  |
| Integracion Jira/ALM bidireccional   | Plugin externo          | Nativo                              |
| Analisis de flakiness                | Limitado                | Excelente                           |
| Costo                                | Open source             | Open source o SaaS                  |
| Curva de aprendizaje                 | Baja                    | Media-alta                          |

**Recomendacion Pragma:**
- **Allure** por defecto en proyectos cortos (<6 meses) o ad-hoc.
- **ReportPortal** en proyectos largos (>6 meses), suites muy grandes (>1000 tests), o clientes que requieren integración Jira/ALM automatizada para auditoría (financiero, salud, gobierno, certificaciones SOC/ISO).

## Integraciones oficiales por framework

### Karate

```xml
<dependency>
    <groupId>com.epam.reportportal</groupId>
    <artifactId>agent-java-karate</artifactId>
    <version>5.2.2</version>
    <scope>test</scope>
</dependency>
```

```properties
# reportportal.properties
rp.endpoint = https://reportportal.cliente.com
rp.api.key = ${RP_API_KEY}
rp.launch = Karate Regression
rp.project = qa-pragma
rp.attributes = build:${BUILD_NUMBER};env:qa
```

### Playwright

```bash
npm i -D @reportportal/agent-js-playwright
```

```typescript
// playwright.config.ts
const rpConfig = {
  apiKey: process.env.RP_API_KEY,
  endpoint: 'https://reportportal.cliente.com/api/v1',
  project: 'qa-pragma',
  launch: 'Playwright E2E',
  attributes: [{ key: 'env', value: 'qa' }],
};

export default defineConfig({
  reporter: [['@reportportal/agent-js-playwright', rpConfig]],
});
```

### K6

```bash
xk6 build --with github.com/reportportal/xk6-reportportal
./k6 run --out reportportal=... load.js
```

Alternativa: convertir summary K6 a launches RP via API REST (`POST /api/v1/{project}/launch`).

### Appium

```xml
<dependency>
    <groupId>com.epam.reportportal</groupId>
    <artifactId>agent-java-junit5</artifactId>
    <version>5.2.2</version>
</dependency>
```

Funciona igual que cualquier JUnit5. Para Serenity, usar `agent-java-cucumber` si la suite es BDD.

## ML-based failure clustering

RP analiza el stack trace y mensaje de error de cada fallo. Tests que fallan por el mismo motivo se agrupan automaticamente bajo un "defect" comun.

Workflow:
1. Primera vez que aparece un fallo, RP lo marca como `To Investigate`.
2. El QA categoriza: `Product Bug`, `Automation Bug`, `System Issue`, `No Defect`.
3. Siguientes ejecuciones: RP reconoce el patron y categoriza automaticamente.
4. Si el patron se asocia a un Jira ticket, RP enlaza el fallo al ticket.

Beneficio: en suites de 5000 tests con 50 fallos, RP puede identificar que 45 vienen del mismo bug — el triage pasa de horas a minutos.

## Integracion Jira automatizada

Flujo tipico:

1. Test falla → marcado To Investigate.
2. QA categoriza como Product Bug + asigna a componente "Login Service".
3. RP busca tickets abiertos del componente.
4. Si no existe ticket, RP crea uno automaticamente con stack trace, screenshot, link al test en RP, e historial de fallos.
5. Bidireccional: cuando el ticket Jira se cierra, RP marca el test como resolved.

Configuracion en RP UI: `Plugins > Jira > Configure`.

## Deployment

```yaml
# docker-compose.yml minimo
version: '3'
services:
  postgres:
    image: postgres:14
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.0
  rabbitmq:
    image: rabbitmq:3-management
  gateway:
    image: reportportal/service-api:5.10.0
  ui:
    image: reportportal/service-ui:5.10.0
    ports:
      - "8080:8080"
```

Para produccion: usar Helm chart oficial (`reportportal/reportportal`) en Kubernetes.

## Coexistencia Allure + ReportPortal

No son excluyentes:
- Allure HTML como artifact de pipeline (consumo rapido en PR).
- ReportPortal como history-of-record (tendencias, Jira, triage).

Setup: agregar ambos reporters al framework — overhead minimo, beneficio dual.

## Cross-link

- Los reportes RP son evidencia segun `[[calidad-test-evidence-and-traceability]]`.
- Para clientes regulados, RP con audit log activado satisface requisitos de trazabilidad.
