---
id: serenity-wdio-reporting
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Configurar e interpretar los reportes del proyecto — Serenity BDD HTML, Allure, Cucumber JSON, wdio-video-reporter — y el crew de Serenity con ArtifactArchiver y Photographer. Cubre artefactos custom, lectura de fallos, screenshots por estrategia y troubleshooting de reportes vacíos.
tags: [serenity-wdio, reporting, allure, serenity-bdd, cucumber-json, video-reporter, photographer, artifacts]
---

## Instrucción

El proyecto genera cuatro tipos de evidencia en cada corrida:

| Reporte | Ubicación | Generador | Cuándo |
|---|---|---|---|
| Serenity BDD HTML | `target/site/serenity/index.html` | `npx serenity-bdd run --features ./features` | Tras cada ejecución |
| Serenity raw JSON | `target/site/serenity/*.json` | `@serenity-js/core:ArtifactArchiver` | Durante la ejecución |
| Allure raw | `allure-results/` | `@wdio/allure-reporter` | Durante la ejecución (web) |
| Cucumber JSON | `reports/cucumber-report.json` | `cucumberOpts.format` | Durante la ejecución |
| Video | `allure-results/<test>.webm` | `wdio-video-reporter` | Cuando un test falla (web) |
| Logs Appium | `logs/appium/` | `@wdio/appium-service` | Mobile |

### Configuración base del crew de Serenity

```typescript
// configs/wdio.shared.conf.ts
serenity: {
  runner: 'cucumber',
  crew: [
    '@serenity-js/console-reporter',
    '@serenity-js/serenity-bdd',
    [ '@serenity-js/core:ArtifactArchiver', { outputDirectory: 'target/site/serenity' } ],
  ],
},
```

### Photographer (solo en web)

```typescript
// configs/wdio.web.conf.ts
serenity: {
  crew: [
    ...(shared.serenity?.crew ?? []),
    [
      '@serenity-js/web:Photographer',
      { strategy: 'TakePhotosOfFailures' },
    ],
  ],
},
```

El Photographer no debe activarse en mobile — depende de window handles que rompen en NATIVE_APP.

### Comandos para generar reportes

```bash
# Serenity BDD HTML
npx serenity-bdd run --features ./features
npm run serenity:report    # alias del proyecto

# Allure HTML
npx allure generate allure-results --clean -o allure-report
npx allure open allure-report

# Limpiar
npm run serenity:clean     # limpia ./target
```

### Anti-patrones

- Activar `Photographer` en config mobile.
- `TakePhotosOfInteractions` en CI (lentitud + storage).
- Commitear `target/`, `allure-results/`, `reports/`.
- Olvidar `npm run serenity:update` al clonar el repo.
- `Log.the(...)` con datos sensibles (credenciales).

Para la configuración completa de reporters WDIO, estrategias del Photographer, lectura de fallos en cada reporte, adjuntar artefactos custom, video reporter, tags de Cucumber para filtrar reportes y troubleshooting detallado, ver las referencias:

- `references/configuracion-reporters.md` — configuración completa de todos los reporters y crew de Serenity.
- `references/lectura-de-fallos.md` — cómo leer fallos en Serenity BDD HTML, Allure y Cucumber JSON, adjuntar artefactos y tags para filtrar.
- `references/troubleshooting-reportes.md` — diagnóstico de síntomas comunes (reporte vacío, sin screenshots, Allure vacío, video no generado).
