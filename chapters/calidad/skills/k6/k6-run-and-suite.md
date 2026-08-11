---
id: calidad-k6-run-and-suite
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [k6]
description: Comandos para instalar y ejecutar scripts K6 individuales y la suite completa con run-all.sh.
tags: [k6, cli, install, run, env-vars, run-all]
---

# Ejecución de K6 — comandos y suite

Una vez generado el proyecto con `[[calidad-k6-greenfield]]`, los scripts se ejecutan vía CLI directo (`k6 run`), vía `npm run` o vía `run-all.sh`.

## Instalación

| OS | Comando |
|---|---|
| macOS | `brew install k6` |
| Windows | `winget install k6 --source winget` |
| Linux (Debian/Ubuntu) | `sudo gpg -k && sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69 && echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \| sudo tee /etc/apt/sources.list.d/k6.list && sudo apt-get update && sudo apt-get install k6` |

## Env vars

| Variable | Requerida | Descripción |
|---|---|---|
| `BASE_URL` | Sí | URL base del servicio bajo prueba (consume `config.js`). |
| `AUTH_TOKEN` | Solo si el spec define `security` | Token Bearer para Authorization. |
| Custom (ej. `CHANNEL`, `TENANT_ID`) | Opcional | Otras variables que `config.js` exponga vía `__ENV`. |

## Comandos individuales

```bash
# Directo
k6 run -e BASE_URL=https://api.example.com/v1 -e AUTH_TOKEN=xyz tests/smoke-test.js
k6 run -e BASE_URL=https://api.example.com/v1                    tests/load-test.js

# Vía npm scripts (ya configurados en package.json — ver k6-project-structure)
npm run smoke
npm run load
npm run stress
npm run spike
npm run soak
npm run all
```

## `run-all.sh`

Ejecuta los 5 scripts en orden (smoke → load → stress → spike → soak). `set -e` detiene la cadena si uno falla sus thresholds.

```bash
#!/bin/bash
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)/tests"

echo '=== K6 Performance Test Suite ==='
echo '--- Smoke Test ---'
k6 run -e BASE_URL=$BASE_URL "$PROJECT_DIR/smoke-test.js"
echo '--- Load Test ---'
k6 run -e BASE_URL=$BASE_URL "$PROJECT_DIR/load-test.js"
echo '--- Stress Test ---'
k6 run -e BASE_URL=$BASE_URL "$PROJECT_DIR/stress-test.js"
echo '--- Spike Test ---'
k6 run -e BASE_URL=$BASE_URL "$PROJECT_DIR/spike-test.js"
echo '--- Soak Test ---'
k6 run -e BASE_URL=$BASE_URL "$PROJECT_DIR/soak-test.js"
echo '=== All tests completed ==='
```

Exporta primero la variable: `export BASE_URL=https://api.example.com/v1` y luego `bash run-all.sh` o `npm run all`.

## Restricciones

- Nunca hardcodear `BASE_URL` o `AUTH_TOKEN` dentro de los scripts; siempre vía `__ENV` con fallback en `config.js`.
- Si el spec no define security, no exportar `AUTH_TOKEN` ni incluirlo en los comandos.
- Los resultados quedan en `results/` (ver [[calidad-k6-greenfield]] (consultar `references/handle-summary-evidence.md` en su subfolder)); esa carpeta debe estar en `.gitignore`.
