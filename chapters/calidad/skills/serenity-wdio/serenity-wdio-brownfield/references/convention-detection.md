# Detección de convenciones — serenity-wdio brownfield

## Qué detectar

| Campo | Fuente / cómo se infiere | Ejemplo |
|---|---|---|
| `context` | Declarado por el usuario y confirmado contra la estructura (`features/web` vs `features/mobile`) y las capabilities | `web` \| `mobile` \| `hibrido` |
| `serenity_version` | `package.json` → `@serenity-js/core` | `^3.31.10` |
| `wdio_version` | `package.json` → `webdriverio` / `@wdio/cli` | `^9.x` |
| `cucumber_version` | `package.json` → `@cucumber/cucumber` | `^11.x` |
| `screenplay_layers_present` | Subdirectorios reales bajo `features/web` y `features/mobile` | `[Tasks, UI, Questions, Interactions, shared]` |
| `ui_mapping_style` | Web usa `PageElement.located(By...)`; mobile usa selectores `string` | `page-element` \| `string-selector` |
| `features_dir` | Path resuelto de los `.feature` | `features/web/Features/`, `features/mobile/android/Features/` |
| `step_definitions_dir` | Path resuelto de los steps | `features/step-definitions/web/` |
| `feature_naming_pattern` | Naming de los `.feature` existentes | `practice-form.feature`, `login.feature` |
| `channel_tags` | Tags de canal observados a nivel Feature | `@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop` |
| `suite_tags` | Tags de suite observados | `@smoke`, `@regression` |
| `scenario_type_tags` | Tags de tipo a nivel Scenario | `@happy-path`, `@negative`, `@edge-case` |
| `default_timeout` | `setDefaultTimeout(...)` en cada step file | `120000`, `200000` |
| `mode_env_map` | Correspondencia `--mode` → `.env.<modo>` en `scripts/run.mjs` | `web → .env.web`, `api → .env.api` |
| `enforce_classic` | `wdio:enforceWebDriverClassic` presente en capabilities web | `true` |
| `documented_workarounds` | Parches comentados en `wdio.shared.conf.ts` | window handles `NATIVE_APP` |

## Algoritmo

1. **Leer `package.json`**: confirmar versiones de Serenity/JS, WebdriverIO, Cucumber, TypeScript y reporters. Anotar dependencias para no duplicarlas.
2. **Leer `configs/wdio.shared.conf.ts`**: hooks, timeouts, reporters y workarounds documentados (window handles `NATIVE_APP`).
3. **Leer el `configs/wdio.<modo>.conf.ts` del `context`**: patrón de merge, `specs`, `capabilities` (incluido `wdio:enforceWebDriverClassic` en web), `cucumberOpts`.
4. **Leer `scripts/run.mjs`**: modos válidos de `--mode` y `--platform`, y el mapa `mode → .env.<modo>`.
5. **Listar un `.feature` representativo por módulo**: primera línea (`# language:` si existe), tags de canal/suite/tipo, naming del archivo.
6. **Listar un UI Mapping representativo**: web con `PageElement.located(By.xpath|css)` o mobile con selectores `string` (Accessibility ID). Verificar coherencia con el `context`. Si no coincide, reportar al usuario antes de continuar.
7. **Consolidar el objeto de convenciones** y usarlo como contrato para los archivos nuevos.

## Salida sugerida

```json
{
  "context": "web",
  "serenity_version": "^3.31.10",
  "wdio_version": "^9.0.0",
  "cucumber_version": "^11.0.0",
  "screenplay_layers_present": ["Tasks", "UI", "Questions", "shared"],
  "ui_mapping_style": "page-element",
  "features_dir": "features/web/Features/",
  "step_definitions_dir": "features/step-definitions/web/",
  "feature_naming_pattern": "{kebab-case}.feature",
  "channel_tags": ["@web"],
  "suite_tags": ["@smoke", "@regression"],
  "scenario_type_tags": ["@happy-path", "@negative"],
  "default_timeout": 120000,
  "mode_env_map": { "web": ".env.web", "api": ".env.api" },
  "enforce_classic": true,
  "documented_workarounds": ["native-app-window-handles"]
}
```

## Regla de prioridad

Si el proyecto declara un naming, tags, timeouts o estructura distintos del estándar del chapter, **el proyecto manda**. El brownfield respeta las convenciones existentes; no realinea el proyecto al estándar del chapter.
