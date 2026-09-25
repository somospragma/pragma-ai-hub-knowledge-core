# Orquestacion y modos (Serenity WDIO Greenfield)

El orquestador `scripts/run.mjs` resuelve `--mode`, `--platform` y `--tags`, carga el `.env.<modo>` correcto y lanza WebdriverIO seguido del reporte serenity-bdd.

## Correspondencia modo -> config -> env

| `--mode` | Config | Env asociado | `--platform` |
|---|---|---|---|
| `web` | `configs/wdio.web.conf.ts` | `.env.web` | no aplica |
| `web_movil` | `configs/wdio.web_mobile.conf.ts` | `.env.web_movil` | no aplica |
| `movil` | `configs/wdio.android.conf.ts` | `.env.movil.android` | `android` |
| `movil` | `configs/wdio.ios.conf.ts` | `.env.movil.ios` | `ios` |
| `desktop` | `configs/wdio.desktop.conf.ts` | `.env` (o `.env.desktop`) | no aplica |
| `api` | `configs/wdio.api.conf.ts` | `.env.api` | no aplica |
| `all` | ejecuta la secuencia web, web_movil, movil, desktop, api | por modo | opcional |

Valores validos de `--mode`: `web`, `web_movil`, `movil`, `desktop`, `api`, `all`.
Valores validos de `--platform`: `android`, `ios` (solo en modo `movil`).

## Comandos de ejemplo por modo

```bash
node ./scripts/run.mjs --mode=web
node ./scripts/run.mjs --mode=web_movil
node ./scripts/run.mjs --mode=movil --platform=android
node ./scripts/run.mjs --mode=movil --platform=ios
node ./scripts/run.mjs --mode=desktop
node ./scripts/run.mjs --mode=api
node ./scripts/run.mjs --mode=all
```

## Sincronia atomica al crear un config nuevo

Al crear `configs/wdio.<modo>.conf.ts`, en la misma entrega:

1. Crear `.env.<modo>` en la raiz con variables mock documentadas.
2. Agregar en `run.mjs` la entrada en `modeToConfig` y el mapeo `mode -> envFile`.
3. Agregar en `package.json` el script `"test:<modo>": "node ./scripts/run.mjs --mode=<modo>"`.
4. Actualizar `README.md` con el comando y la fila de la tabla modo -> config -> env.

Un config sin sus contrapartes es codigo muerto: la sincronia debe ser atomica.
