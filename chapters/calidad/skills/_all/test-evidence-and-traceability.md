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

## Los screenshots del reporte se miran antes de concluir

La evidencia visual no es un adjunto para el informe: es **la fuente que corrige las conclusiones equivocadas**. Un mensaje de error dice qué se rompió; el screenshot dice qué estaba pasando en pantalla, que casi nunca es lo mismo.

Verificado en campo, dos veredictos publicados y falsos que se cayeron al abrir las imágenes del mismo reporte que ya se tenía:

| Veredicto por texto y reloj | Lo que mostraba el screenshot |
|---|---|
| "El backend respondió hace 37 s y la app sigue en login: es un rechazo silencioso" | El botón con el spinner girando: la aplicación seguía procesando, el entorno era lento |
| "El escenario falla al buscar el elemento" | El escritorio del sistema con un diálogo del sistema operativo encima de la aplicación |

**Regla dura: ningún diagnóstico se cierra sin haber mirado las capturas de la corrida que se está diagnosticando.** Aplica al reporte propio y al que llega de un pipeline ajeno. Cuando la captura contradice la hipótesis, gana la captura.

### Cómo llegar a las imágenes cuando el reporte es un archivo único

Los reportes autocontenidos embeben las imágenes en base64 y pesan decenas de megabytes, lo que hace inviable leerlos enteros. Se extraen a archivos y se miran uno por uno:

```bash
# Localizar las imágenes embebidas sin abrir el archivo completo
grep -o 'data:image/[a-z]*;base64,[A-Za-z0-9+/=]*' reporte.html | head
```

Cada bloque se decodifica a su archivo y se abre. Los dos que siempre importan son **la captura del step que falló** y **la del cierre del escenario**, segundos después: la diferencia entre ambas es la que revela si la aplicación avanzaba, si apareció una pantalla no contemplada o si quedó algo encima.

Cuando el reporte no trae capturas del momento del fallo, eso es un hallazgo en sí mismo y se corrige antes de seguir diagnosticando: sin ellas, cada fallo cuesta una sesión de conjeturas.

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
