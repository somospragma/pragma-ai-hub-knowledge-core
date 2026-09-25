---
id: serenity-wdio-test-execution-runner
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [serenity-wdio]
description: Ejecutar suites de pruebas del proyecto usando el orquestador scripts/run.mjs, gestionar variables de entorno por modo (.env.web, .env.api, .env.movil.android, .env.movil.ios), seleccionar la configuración wdio correcta según --mode y --platform, y manejar el ciclo de vida de Appium/WebDriver.
tags: [serenity-wdio, test-execution, run-mjs, wdio, appium, env-files, modes, platform, orquestador]
---

## Instrucción

El punto de entrada para toda ejecución de tests en este proyecto es el orquestador `scripts/run.mjs`. No ejecutar `wdio` directo; hacerlo omite la carga del archivo `.env.*` correspondiente.

```bash
npm test                              # default: --mode=web
node ./scripts/run.mjs --mode=<m> [--platform=<p>]
```

El orquestador:

1. Lee `--mode` y `--platform` (o variables `MODE` / `MOBILE_PLATFORM`).
2. Carga el `.env.*` correspondiente con `dotenv`.
3. Ejecuta `npx wdio run <config>` con el config mapeado.
4. Genera el reporte con `npx serenity-bdd run --features ./features`.

### Tabla de modos

| Comando npm | Mode | Platform | Config | .env file |
|---|---|---|---|---|
| `npm run test:web` | `web` | — | `configs/wdio.web.conf.ts` | `.env.web` |
| `npm run test:web_movil` | `web_movil` | — | `configs/wdio.web_mobile.conf.ts` | `.env.web_movil` |
| `npm run test:movil:android` | `movil` | `android` | `configs/wdio.android.conf.ts` | `.env.movil.android` |
| `npm run test:movil:ios` | `movil` | `ios` | `configs/wdio.ios.conf.ts` | `.env.movil.ios` |
| `npm run test:api` | `api` | — | `configs/wdio.api.conf.ts` | `.env.api` |
| `npm run test:desktop` | `desktop` | — | `configs/wdio.desktop.conf.ts` | `.env` |
| `npm run test:all` | `all` | (android default) | secuencial todos | varios |

Regla: si se pasa `--mode=movil` SIN `--platform`, el script aborta con código 2.

### Anti-patrones de ejecución

- Correr `wdio` directo sin pasar por `run.mjs` (no carga el `.env.*` correcto).
- Usar `process.env.PLATFORM` como modo en scripts.
- Commitear `.env.*` con credenciales reales.
- Modificar `cucumberOpts.timeout` para enmascarar flakiness.
- Lanzar `npm test:movil` sin `--platform`.
- Usar Appium basePath `/wd/hub` en Appium 3 (debe ser `/`).
- Instalar drivers Appium dentro del repo (deben ir en el global de Appium).

Para el detalle completo de variables de entorno por modo, flujo de selección del orquestador, configuración de Appium, cómo agregar un nuevo modo, comandos utilitarios y diagnóstico de fallos comunes, ver las referencias:

- `references/env-variables.md` — variables de entorno por archivo `.env.*`.
- `references/orquestador-y-modos.md` — flujo del orquestador, Appium, cómo agregar un nuevo modo y salidas/artefactos.
- `references/diagnostico-ejecucion.md` — diagnóstico de fallos comunes y checklist previa a la ejecución.
