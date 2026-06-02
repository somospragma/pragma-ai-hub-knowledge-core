---
id: calidad-test-evidence-and-traceability
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: Configura evidencia (reportes, traces, summaries) y trazabilidad requisito → test → resultado por framework.
tags: [evidence, traceability, reports, karate, k6, playwright, appium, serenity]
---

# Test Evidence and Traceability — Reportes y Tags por Framework

## Cuándo aplicar

Aplica este skill como paso final de la generación (paso 7 de `[[calidad-route-test-generation]]`), una vez que los archivos de prueba y la infraestructura están persistidos.

Su propósito doble:

1. **Evidencia**: que cada ejecución produzca artefactos auditables (reportes HTML, traces, videos, JSON summaries) en rutas conocidas y consistentes.
2. **Trazabilidad**: que cada test enlace requisito → caso → ejecución → decisión, vía tags explícitos.

## Evidencia por framework

### Karate

- Reportes: `target/karate-reports/` (HTML por feature + `karate-summary.html`).
- Activar JUnit XML: `karate.options="--output-junit=target/karate-reports"` (configurado en `TestRunner.java`).
- Cada `Feature` declara tags `@user-story:HUT-123` para enlazar con Jira u otra herramienta ALM.
- Para CI: publicar `target/karate-reports/karate-summary.html` como artifact.

### K6

- Implementar `handleSummary()` en cada script para exportar JSON con timestamp a `results/`.
- Formato de archivo: `${ISO}-summary.json` (ej. `2026-05-27T14-32-10-summary.json`).
- Snippet de referencia:

```javascript
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.2/index.js';

export function handleSummary(data) {
  const iso = new Date().toISOString().replace(/[:.]/g, '-');
  return {
    [`results/${iso}-summary.json`]: JSON.stringify(data, null, 2),
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}
```

- Thresholds en `options` para que K6 marque la ejecución como fallida si se superan SLAs (ej. `http_req_duration: ['p(95)<500']`).

### Playwright

- En `playwright.config.ts`:

```ts
export default defineConfig({
  reporter: [['html', { outputFolder: 'playwright-report', open: 'never' }]],
  use: {
    trace: 'on-first-retry',
    video: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

- Reporte: `npx playwright show-report` abre `playwright-report/index.html`.
- Traces (`trace.zip`) se abren con `npx playwright show-trace path/to/trace.zip` — clave para auditoría de fallos en CI.

### Appium + Serenity (Screenplay, V2)

- `./gradlew aggregate` genera el reporte single-page Serenity en `target/site/serenity/index.html`.
- Cada método anotado con `@Step("...")` aparece como paso narrado en el reporte.
- Configuración en `serenity.properties`:

```properties
serenity.project.name=${project_name}
serenity.report.encoding=UTF-8
serenity.take.screenshots=AFTER_EACH_STEP
serenity.test.root=com.client.qa.mobile
```

- Las screenshots se asocian automáticamente a cada `@Step` y quedan visibles en el reporte agregado.

## Trazabilidad — Convención de tags

Aplica la misma convención de tags **en todos los frameworks** (Karate `@`, Cucumber `@`, Playwright `test.describe.parallel('@tag', ...)` o `test('... @tag', ...)`, K6 vía `tags` en `options`):

| Tag                       | Propósito                                                       | Ejemplo                  |
|---------------------------|-----------------------------------------------------------------|--------------------------|
| `@user-story:<ID>`        | Liga el test a la historia de usuario en Jira/ALM               | `@user-story:HUT-123`    |
| `@requirement:<ID>`       | Liga a un requisito funcional formal                            | `@requirement:RF-045`    |
| `@smoke`                  | Suite mínima de humo, ejecutable en cada commit                 | `@smoke`                 |
| `@regression`             | Suite completa de regresión                                     | `@regression`            |
| `@critical`               | Camino crítico de negocio (transferencias, pagos, autenticación) | `@critical`              |
| `@negative`               | Escenario de validación de error o regla de negocio             | `@negative`              |
| `@performance`            | (K6) marca tipo de prueba (load/stress/spike/soak)              | `@performance:load`      |

## Cadena requisito → test → resultado → decisión

1. **Requisito**: documentado en Jira/Confluence con ID estable (`HUT-123`, `RF-045`).
2. **Test**: nombrado y tagueado con esos IDs (`@user-story:HUT-123`).
3. **Resultado**: reporte ejecutado (`karate-reports/`, `playwright-report/`, `results/*-summary.json`, `target/site/serenity/`) con timestamp y commit.
4. **Decisión**: el equipo (lead QA, dev lead, PO) consume el reporte y decide bloquear/promover el release. Esta decisión queda registrada en el ticket de Jira referenciado.

## Restricciones

- **NUNCA** entregar tests sin tags de trazabilidad: como mínimo `@user-story` o `@requirement`.
- **NUNCA** desactivar reportes para "ahorrar tiempo de CI": son la única evidencia auditable.
- **NUNCA** reportar "todo verde" si solo corrió `@smoke`. Documenta qué suite se ejecutó.
- En clientes con políticas de retención (compliance, auditoría externa, certificaciones ISO/SOC), los reportes y summaries deben **archivarse** (S3, artifactory, o equivalente) según política de retención del cliente.
- Encadena con `[[calidad-route-test-generation]]` como paso final.
