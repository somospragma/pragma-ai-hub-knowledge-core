# Dependencias de `package.json` — verificadas con ejecución real

Lista completa de dependencias necesarias para que el arquetipo `serenity-wdio` instale y ejecute de primera. Verificada corriendo `npm install` + smoke gate real (modo `api`) de punta a punta; incluye paquetes periféricos que el resto de las references mencionan de paso pero que no estaban consolidados en un solo lugar.

## `devDependencies` mínimas (todas las plataformas)

```json
{
  "devDependencies": {
    "@serenity-js/core": "^3.31.10",
    "@serenity-js/assertions": "^3.31.10",
    "@serenity-js/cucumber": "^3.31.10",
    "@serenity-js/webdriverio": "^3.31.10",
    "@serenity-js/serenity-bdd": "^3.31.10",
    "@wdio/cli": "^9.10.1",
    "@wdio/local-runner": "^9.10.1",
    "@wdio/cucumber-framework": "^9.10.1",
    "@wdio/spec-reporter": "^9.10.1",
    "@wdio/allure-reporter": "^9.10.1",
    "@cucumber/cucumber": "^11.0.1",
    "typescript": "^5.5.0",
    "ts-node": "^10.9.2",
    "tsx": "^4.19.0"
  }
}
```

## Por qué cada paquete es obligatorio (no solo recomendado)

| Paquete | Sin él, falla con... | Nota |
|---|---|---|
| `@serenity-js/webdriverio` | El actor nunca obtiene abilities automáticas (`CallAnApi`, `BrowseTheWebWithWebdriverIO`); en algunos casos `npm install` falla por peer dependency de `@serenity-js/core`. | Obligatoria aunque el proyecto use el patrón `whoCan(...)` explícito (ver `[[serenity-wdio-api-testing-rest]]`, `references/actor-setup-verificado.md`). |
| `@wdio/cucumber-framework` | `Couldn't find plugin "cucumber" framework, neither as wdio scoped package...`. | Es el framework runner que WebdriverIO carga para `framework: 'cucumber'`; no se instala transitivamente con `@wdio/cli`. |
| `@wdio/spec-reporter` | `Couldn't find plugin "spec" reporter...`. | Necesario para cualquier `reporters: ['spec']` en `wdio.shared.conf.ts`, incluso en modo `api` sin browser. |
| `tsx` | Nada directamente, pero sin ella `@wdio/cli` no puede auto-inyectar el loader ESM que usa para leer `configs/wdio.*.conf.ts` cuando el archivo es `.ts`. | WebdriverIO v9 la detecta e inyecta sola vía `NODE_OPTIONS` si está en `node_modules`; no requiere configuración manual. |
| `ts-node` | Los `step-definitions/*.ts` no compilan al vuelo si el proyecto usa `requireModule`/`autoCompileOpts` con ts-node en vez de tsx. | Mantener ambos (`ts-node` y `tsx`) da flexibilidad; `tsx` es el que WebdriverIO v9 prioriza por defecto. |
| `@serenity-js/serenity-bdd` | El crew `['@serenity-js/serenity-bdd']` declarado en `wdio.shared.conf.ts` no resuelve. | Genera el reporte agregado en `target/site/serenity/`. |

## Deduplicación de `@cucumber/cucumber`

`npm install` puede instalar dos copias físicas de `@cucumber/cucumber` (una en la raíz de `node_modules/`, otra anidada bajo `node_modules/@wdio/cucumber-framework/node_modules/@cucumber/cucumber`) aunque declares la misma versión exacta en ambas dependencias. Esto rompe el registro de step-definitions con el error:

```
Error: You're calling functions (e.g. "Given") on an instance of Cucumber that isn't running (status: PENDING).
This means you may have an invalid installation, potentially due to:
- Cucumber being installed globally
- A project structure where your support code is depending on a different instance of Cucumber
```

Fix verificado: declarar en `package.json` un bloque `overrides` que fuerza una única versión resuelta:

```json
{
  "overrides": {
    "@cucumber/cucumber": "11.0.1"
  }
}
```

Si tras `npm install` la copia anidada persiste (`find node_modules -name "@cucumber" -type d` muestra más de una ruta con `cucumber/` dentro), verificar que la copia anidada tenga exactamente la misma versión que la de la raíz antes de eliminarla manualmente; si son versiones distintas, el `overrides` no se aplicó correctamente y hay que revisar el lockfile.

## Cross-links

`[[serenity-wdio-greenfield]]`, `references/project-structure.md`, `references/preflight.md`, `[[serenity-wdio-api-testing-rest]]` (`references/actor-setup-verificado.md`).
