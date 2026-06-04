#!/usr/bin/env bash
# {{project_name}} — orquestador de los 5 scripts K6.
#
# Tras generar el proyecto: chmod +x run-all.sh
# Ejecucion: ./run-all.sh   (o npm run all)
#
# set -e detiene en el primer fallo: smoke debe pasar antes que load, etc.
# Si necesitas correr todos los scripts ignorando fallos, comenta la siguiente linea.
set -euo pipefail

BASE_URL="${BASE_URL:-{{baseUrl}}}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

export BASE_URL
export AUTH_TOKEN

mkdir -p results

echo "==> smoke-test.js"
k6 run tests/smoke-test.js

echo "==> load-test.js"
k6 run tests/load-test.js

echo "==> stress-test.js"
k6 run tests/stress-test.js

echo "==> spike-test.js"
k6 run tests/spike-test.js

echo "==> soak-test.js"
k6 run tests/soak-test.js

echo "==> {{project_name}}: all scripts completed"
