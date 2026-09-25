# Análisis previo obligatorio — serenity-wdio brownfield

El análisis previo es un paso **bloqueante**: no se genera ningún cambio hasta consolidarlo. Su objetivo es entender el proyecto existente lo suficiente para extenderlo sin romper convenciones ni infraestructura.

## Elementos mínimos a identificar

### 1. Estructura de carpetas

Recorrer el árbol bajo `project_root` y mapear la estructura real. La estructura de referencia del arquetipo es:

```
features/
  web/            # Features/, Tasks/, UI/, Questions/, Data/, shared/
  mobile/         # android/ (Features/, Tasks/, UI/), shared/ (Interactions/, Questions/, Tasks/)
step-definitions/ # web/, mobile/
support/          # parameter.config.ts
configs/          # wdio.shared.conf.ts, wdio.<modo>.conf.ts
scripts/          # run.mjs
```

Anotar qué subcarpetas de Screenplay existen realmente (`Tasks/`, `UI/`, `Questions/`, `Interactions/`, `Data/`, `shared/`) y en qué contexto (web / mobile).

### 2. Dependencias con sus versiones

Leer `package.json` y registrar la versión exacta declarada (no asumir):

| Dependencia | Por qué importa |
|---|---|
| `@serenity-js/core`, `@serenity-js/web`, `@serenity-js/webdriverio`, `@serenity-js/cucumber`, `@serenity-js/rest` | Versión de Serenity/JS (esperado `^3.x`). |
| `webdriverio`, `@wdio/cli`, `@wdio/*` | Versión de WebdriverIO (esperado `^9.x`). |
| `@cucumber/cucumber` | Versión de Cucumber (esperado `^11.x`). |
| `typescript` | Target y strictness (`es2022`, `strict: true`). |
| `@wdio/allure-reporter`, `@serenity-js/serenity-bdd`, `wdio-video-reporter`, `wdio-cucumberjs-json-reporter` | Reporters activos; alimentan la evidencia. |

### 3. Configuraciones

- `configs/wdio.shared.conf.ts`: hooks, timeouts, workarounds, reporters.
- Cada `configs/wdio.<modo>.conf.ts`: patrón de merge sobre `shared`, `specs`, `capabilities`, `cucumberOpts`.
- En configs web, confirmar `'wdio:enforceWebDriverClassic': true` en cada capability.
- `tsconfig.json`: `target`, `strict`, paths.
- Inventario de `.env.<modo>` disponibles y su correspondencia con los modos de `scripts/run.mjs`.

### 4. Workarounds documentados

- Workaround de window handles para `NATIVE_APP` en `wdio.shared.conf.ts` (ver `native-app-window-handles.md`).
- Cualquier `overwriteCommand`/`addCommand` o parche técnico comentado.
- Notas de troubleshooting (por ejemplo, bundle id / package verificados contra el binario en mobile).

### 5. Convenciones de nomenclatura y tags

- Naming de `.feature` y de archivos Screenplay.
- Tags de canal (`@web`, `@mobile`, `@android`, `@ios`, `@api`, `@desktop`) y de suite (`@smoke`, `@regression`).
- Patrón de UI Mapping por contexto: web con `PageElement`/`By`, mobile con selectores `string`.
- `setDefaultTimeout` declarado por step file.

## Consolidación

El resultado del análisis se consolida en un objeto único (ver `convention-detection.md` para el esquema sugerido) que se usa como contrato para todos los archivos nuevos. Cualquier elemento no determinable por lectura directa se marca como pendiente y se solicita al usuario; no se asume.
