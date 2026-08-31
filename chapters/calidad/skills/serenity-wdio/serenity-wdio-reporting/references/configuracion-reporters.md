# Configuración de reporters y crew de Serenity

## Crew de Serenity (base compartida)

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

| Componente | Función |
|---|---|
| `@serenity-js/console-reporter` | Imprime resultado en stdout |
| `@serenity-js/serenity-bdd` | Genera el JSON consumido por `serenity-bdd run` |
| `ArtifactArchiver` | Persiste screenshots, JSON y otros artefactos en `target/site/serenity` |

## Photographer (solo web)

```typescript
// configs/wdio.web.conf.ts
serenity: {
  crew: [
    ...(shared.serenity?.crew ?? []),
    [
      '@serenity-js/web:Photographer',
      {
        strategy: 'TakePhotosOfFailures',
        // strategy: 'TakePhotosOfInteractions',  // más completo, más lento
      },
    ],
  ],
},
```

| Strategy | Cuándo toma screenshots | Costo |
|---|---|---|
| `TakePhotosOfFailures` | Solo cuando una interaction falla | Bajo (default recomendado) |
| `TakePhotosOfInteractions` | Antes y después de cada interaction | Alto |

El Photographer NO debe activarse en mobile — depende de window handles que rompen en NATIVE_APP.

## Reporters WDIO (independientes del crew Serenity)

```typescript
// configs/wdio.web.conf.ts
reporters: [
  'spec',
  ['allure', { outputDir: 'allure-results' }],
  'json',
  ['video', {
    saveAllVideos: true,
    videoSlowdownMultiplier: 1,
    videoRenderTimeout: 30,
    outputDir: 'allure-results',
    addConsoleLogs: true,
  }],
],
```

## Configuración del video reporter

```typescript
['video', {
  saveAllVideos: true,           // false = solo en falla (recomendado en CI)
  videoSlowdownMultiplier: 1,    // 1 = velocidad real, 3 = 3x más lento
  videoRenderTimeout: 30,        // segundos máx para renderizar
  outputDir: 'allure-results',   // se integra con Allure si apunta ahí
  addConsoleLogs: true,          // console.log del navegador en el video
}],
```

El video reporter usa ffmpeg internamente. Verificar que está instalado: `ffmpeg -version`.

## Estructura del directorio target/

```
target/site/serenity/
├── index.html                         # entrada del reporte
├── home.html
├── reports/
│   ├── 4e7a... .json                  # JSON crudo por escenario
│   └── ...
├── *.png                              # screenshots de Photographer
└── style/, js/, images/               # assets del template
```

No commitear `target/`. Incluirlo en `.gitignore`.
