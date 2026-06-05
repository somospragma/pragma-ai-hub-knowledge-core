#!/usr/bin/env bash
# {{project_name}} — orquestador de la suite K6 modular.
#
# Tras generar el proyecto: chmod +x run-all.sh
# Ejecucion: ./run-all.sh   (o npm run all)
#
# set -e detiene en el primer fallo: linea-base debe pasar antes que carga, etc.
# Si necesitas correr todos los escenarios ignorando fallos, comenta la siguiente linea.
set -euo pipefail

BASE_URL="${BASE_URL:-{{baseUrl}}}"
AUTH_TOKEN="${AUTH_TOKEN:-}"

export BASE_URL
export AUTH_TOKEN

mkdir -p results

for scenario in linea-base carga estres; do
  echo "==> Running $scenario"
  mkdir -p "results/$scenario"
  k6 run \
    -e BASE_URL="$BASE_URL" \
    -e AUTH_TOKEN="$AUTH_TOKEN" \
    -e SCENARIO_NAME="$scenario" \
    "tests/$scenario/main.js"
done

echo "==> {{project_name}}: all scenarios completed"
