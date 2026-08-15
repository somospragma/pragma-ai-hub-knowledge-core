---
id: calidad-playwright-run-and-modes
version: 2.0.0
scope: stack
type: skill
chapter: calidad
stack: [playwright]
description: Comandos y modos de ejecución de Playwright (headless, headed, UI, debug, visual, a11y, filtros, override de BASE_URL, tags live/mocked/hybrid).
tags: [playwright, cli, modes, commands, live, mocked, hybrid]
---

# Modos de ejecución de Playwright

## Setup inicial

```bash
cd {project}
npm install
npx playwright install        # descarga los browsers (chromium, firefox, webkit)
```

## Comandos por modo

```bash
# Headless (default; CI)
npx playwright test

# Headed (UI visible)
npx playwright test --headed

# UI mode (REPL gráfico interactivo)
npx playwright test --ui

# Debug step-by-step con Playwright Inspector
npx playwright test --debug

# Solo regresión visual
npx playwright test tests/visual.spec.ts

# Primera corrida visual: genera baselines en tests/__screenshots__/
npx playwright test tests/visual.spec.ts --update-snapshots

# Solo accesibilidad
npx playwright test tests/accessibility.spec.ts

# Un spec específico
npx playwright test tests/users.spec.ts

# Filtrar por título de test (regex)
npx playwright test -g "create user"

# Override de baseURL por ambiente
BASE_URL=https://dev.app.com npx playwright test

# Abrir el último HTML report
npx playwright show-report
```

## Tabla de modos (flags CLI)

| Modo                              | Comando                                                  | Cuándo usar                                                  |
|-----------------------------------|----------------------------------------------------------|--------------------------------------------------------------|
| Headless                          | `npx playwright test`                                    | CI, corridas rápidas, default                                |
| Headed                            | `npx playwright test --headed`                           | Ver el browser durante la corrida                            |
| UI mode                           | `npx playwright test --ui`                               | Desarrollo iterativo, watch + time-travel                    |
| Debug                             | `npx playwright test --debug`                            | Pausar en cada paso con el Inspector                         |
| Visual                            | `npx playwright test tests/visual.spec.ts`               | Comparar contra baselines de screenshot                      |
| Visual + update snapshots         | `... --update-snapshots`                                 | Primera corrida o cambio intencional de UI                   |
| Accesibilidad                     | `npx playwright test tests/accessibility.spec.ts`        | Verificar WCAG 2.1 AA                                        |
| Filtrado por título               | `... -g "create user"`                                   | Iterar sobre un escenario puntual                            |
| Override de URL                   | `BASE_URL=... npx playwright test`                       | Apuntar a otro ambiente sin tocar el config                  |
| Reporte HTML                      | `npx playwright show-report`                             | Abrir el reporte HTML de la última corrida                   |

## Modos de ejecución (`@live` / `@mocked` / `@hybrid`)

Los tests Playwright generados por este knowledge-core declaran su modo de ejecución mediante **tags en el título o en el `describe`**. Esto separa qué se ejecuta contra backend real, qué corre intercepando red, y qué mezcla ambos. Los flags CLI de la sección anterior son ortogonales a estos tags: se combinan libremente.

### Tags

- **`@live` (default)** — Test corre contra backend real apuntado por `BACKEND_URL` y frontend en `BASE_URL`. Único modo que valida integración real. Obligatorio para la suite smoke.
- **`@mocked` (opt-in)** — Test intercepta toda la red con `page.route()` usando `setupMocks(page)`. Requiere inyectar el fixture `mockApi`. Útil para: error states UI, dev offline, regresión del propio mock.
- **`@hybrid` (opt-in)** — Test corre live por default y mockea endpoints concretos (servicios externos lentos, APIs no disponibles en dev). Requiere `mockApi` parcial.

### Filtrado en CLI

```bash
# Smoke / CI por defecto: solo live
npx playwright test --grep @live

# Desarrollo offline sin backend disponible
npx playwright test --grep @mocked

# Regresión: live + hybrid (sin mocked puros)
npx playwright test --grep "@live|@hybrid"

# Excluir mocked en producción
npx playwright test --grep-invert @mocked
```

### Scripts del proyecto: invocar el binario, no otro script

Un script que llama a otro script del mismo `package.json` pierde los argumentos por el camino: invocado como `npm run test:local -- --grep @smoke`, el filtro llega al runner como si fuera una ruta de archivo. El síntoma —nada se ejecuta, o un error de archivo inexistente con el nombre del tag— no se parece a su causa y se confunde con un cuelgue del runner.

```json
"test:local": "BASE_URL=http://localhost:3000 npm run test",              // rompe el paso de argumentos
"test:local": "BASE_URL=http://localhost:3000 playwright test",           // correcto
```

Cada script repite el comando completo. Es más verboso y es la única forma de que los argumentos de la línea de comandos lleguen intactos.

### Variables de entorno

| Variable      | Descripción                                                                 | Ejemplo                       |
|---------------|-----------------------------------------------------------------------------|-------------------------------|
| `BASE_URL`    | URL del frontend (SPA, sitio web). Se inyecta como `use.baseURL`.           | `https://app.dev.example.com` |
| `BACKEND_URL` | URL del backend real, consumida en tests `@live` y `@hybrid`.               | `https://api.dev.example.com` |
| `MOCK_MODE`   | `off \| full \| partial`. Default `off`. Force-mock para CI sin backend.    | `partial`                     |

### Recomendación de stacks

| Suite / contexto                | Tags recomendados            | Por qué                                                  |
|---------------------------------|------------------------------|----------------------------------------------------------|
| Smoke                           | `@live`                      | Contrato real con el backend; sin excepciones.           |
| Regresión completa              | `@live` mayoritario + `@hybrid` puntual | Cobertura amplia; aísla solo dependencias externas. |
| Error states / edge UI          | `@mocked`                    | Forzar 500, 429, latencias, payloads malformados.        |
| Dev local sin backend           | `@mocked`                    | Iterar UI sin levantar stack completo.                   |
| CI con backend degradado/down   | `MOCK_MODE=full` + `@mocked` | Pipeline no se bloquea; reporta como suite separada.     |

Detalle completo del modelo, risk matrix y configuración de `projects` por tag: `[execution-modes-live-mocked-hybrid](./playwright-greenfield/references/execution-modes-live-mocked-hybrid.md)`.
