---
id: calidad-results-structure-universal
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "OBLIGATORIO. Convención universal results/{categoría}/{fecha}/ para organización de evidencia en los 4 frameworks. Garantiza diffabilidad, agrupación por HU y compatibilidad con CI."
tags: [evidence, results, structure, universal, mandatory]
enforcement: mandatory
---

# Results Structure — Convención universal `results/{categoría}/{fecha}/`

Convención obligatoria para la organización de evidencia de ejecución en los 4 frameworks. Garantiza diffabilidad entre corridas, agrupación por feature/scenario/HU y compatibilidad con artefactos de CI.

## Estructura obligatoria

| Stack | Estructura `results/` |
|---|---|
| Karate | `results/karate/{YYYY-MM-DD}/{ISO}-{feature-or-tag}/` con `karate-summary.json`, `cucumber.json`, junit XML |
| Playwright | `results/playwright/{YYYY-MM-DD}/{ISO}/` con HTML report, traces, screenshots, `results.json` |
| K6 | `results/{scenario}/{YYYY-MM-DD}/{ISO}-summary.json` + `{ISO}-metadata.json` (ya cubierto en oleada K6) |
| Appium | `results/appium/{YYYY-MM-DD}/{ISO}/` con dir serenity report, screenshots, logs |

Donde:

- `{YYYY-MM-DD}` es la fecha local de inicio de corrida (ej. `2026-06-05`).
- `{ISO}` es timestamp ISO con `:` y `.` reemplazados por `-` (ej. `2026-06-05T10-30-15-123Z`).
- `{feature-or-tag}` (Karate) es el slug del feature o tag principal corrido (ej. `addPet`, `smoke`).
- `{scenario}` (K6) es la categoría del escenario (`linea-base`, `stress`, `soak`).

## Reglas

- `results/` siempre desde **project root**. Nunca `../results`, nunca paths absolutos hardcoded.
- `results/` siempre en `.gitignore` — la evidencia no se commitea (se sube como artefacto de CI o se sincroniza a un bucket).
- El directorio se crea con `mkdir -p` desde el reporter/hook; nunca asumir que existe.
- Sub-paths con `{ISO}` garantizan que corridas concurrentes no se pisan.
- Por dentro de cada corrida: el JSON summary y el `metadata.json` (ver `[execution-metadata-schema](./execution-metadata-schema.md)`) son hermanos.

## Configuración por stack

### Karate

En `karate-config.js` el directorio de reportes se setea vía `karate.configure('reportDir', ...)`; en `pom.xml` Surefire usa `reportsDirectory` para los XML JUnit. Ambos deben apuntar a la misma raíz dinámica:

```javascript
// karate-config.js (fragmento)
var today = new Date().toISOString().slice(0, 10);
var iso = new Date().toISOString().replace(/[:.]/g, '-');
karate.configure('reportDir', 'results/karate/' + today + '/' + iso);
```

```xml
<!-- pom.xml (fragmento) -->
<configuration>
  <reportsDirectory>${project.basedir}/results/karate/${maven.build.timestamp}</reportsDirectory>
</configuration>
<properties>
  <maven.build.timestamp.format>yyyy-MM-dd</maven.build.timestamp.format>
</properties>
```

### Playwright

En `playwright.config.ts` el reporter array apunta a paths estructurados:

```typescript
const today = new Date().toISOString().slice(0, 10);
const iso = new Date().toISOString().replace(/[:.]/g, '-');
const RESULTS_BASE = `results/playwright/${today}/${iso}`;

export default defineConfig({
  outputDir: `${RESULTS_BASE}/test-output`,
  reporter: [
    ['html', { open: 'never', outputFolder: `${RESULTS_BASE}/html` }],
    ['json', { outputFile: `${RESULTS_BASE}/results.json` }],
    ['junit', { outputFile: `${RESULTS_BASE}/junit.xml` }],
    ['list'],
  ],
  // ...
});
```

### K6

Cubierto en [[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder) y la oleada K6 paralela. `handleSummary()` devuelve un objeto cuyas claves son los paths a persistir:

```javascript
return {
  [`results/${scenario}/${today}/${iso}-summary.json`]: JSON.stringify(data, null, 2),
  [`results/${scenario}/${today}/${iso}-metadata.json`]: JSON.stringify(metadata, null, 2),
  stdout: textSummary(data, { indent: ' ', enableColors: true }),
};
```

### Appium

Serenity expone el system property `serenity.outputDirectory`. En `build.gradle` se setea dinámico por fecha y se garantiza que el plugin `aggregate` lo respete:

```groovy
def today = new Date().format('yyyy-MM-dd')
def iso = new Date().format("yyyy-MM-dd'T'HH-mm-ss-SSS'Z'", TimeZone.getTimeZone('UTC'))
def resultsDir = "$rootDir/results/appium/$today/$iso"

test {
  useJUnitPlatform()
  systemProperty 'serenity.outputDirectory', resultsDir
  systemProperty 'serenity.report.dir', resultsDir
  systemProperties System.getProperties()
}

serenity {
  outputDirectory = file(resultsDir)
  reports = ['single-page-html']
}
```

## Cross-links

`[[calidad-test-evidence-and-traceability]]`, `[[calidad-delivery-gate-contract]]`, `[execution-metadata-schema](./execution-metadata-schema.md)`, `[environment-blocker-evidence](./environment-blocker-evidence.md)`.
