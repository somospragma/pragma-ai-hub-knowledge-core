
# Estructura del proyecto K6 (greenfield)

## Árbol

```
{project_name}/
├── package.json
├── README.md
├── run-all.sh
├── .gitignore
└── tests/
    ├── config.js
    ├── utils.js
    ├── smoke-test.js
    ├── load-test.js
    ├── stress-test.js
    ├── spike-test.js
    └── soak-test.js
```

La carpeta `results/` se genera en runtime; no se versiona.

## `package.json`

```json
{
  "name": "{project-name}-k6",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "smoke":  "k6 run tests/smoke-test.js",
    "load":   "k6 run tests/load-test.js",
    "stress": "k6 run tests/stress-test.js",
    "spike":  "k6 run tests/spike-test.js",
    "soak":   "k6 run tests/soak-test.js",
    "all":    "bash run-all.sh"
  }
}
```

## `.gitignore`

```
results/
node_modules/
*.log
.DS_Store
```

## `run-all.sh`

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

`set -e` aborta la suite si cualquier script falla sus thresholds.

## README.md (esqueleto mínimo)

Debe documentar:

- Cómo instalar K6 (ver `[[k6-run-and-suite]]`).
- Env vars: `BASE_URL` (requerido), `AUTH_TOKEN` (solo si el spec define security).
- Comandos npm: `smoke`, `load`, `stress`, `spike`, `soak`, `all`.
- Tier de thresholds elegido y justificación (Conservative / Moderate / Relaxed — ver `[[k6-thresholds-three-tiers]]`).
- Política de calibración (`[[calibrate-k6-thresholds]]`).
