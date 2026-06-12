#!/usr/bin/env bash
set -e
echo "=== K6 pre-flight ==="

if ! command -v k6 > /dev/null 2>&1; then
  echo "[fail] k6 no encontrado en PATH."
  echo "Sugerencia: brew install k6 | apt install k6 | choco install k6"
  exit 1
fi

K6_VERSION=$(k6 version 2>/dev/null | head -n 1 | awk '{print $2}' | sed 's/^v//')
echo "k6 version: $K6_VERSION"
K6_MAJOR=$(echo "$K6_VERSION" | cut -d. -f1)
K6_MINOR=$(echo "$K6_VERSION" | cut -d. -f2)
if [[ "$K6_MAJOR" == "0" && "$K6_MINOR" -lt 50 ]]; then
  echo "[warn] k6 $K6_VERSION < 0.50.0. Recomendado actualizar para handleSummary y thresholds compuestos."
fi
echo "[ok] k6 disponible"

if [[ -n "$BASE_URL" ]]; then
  echo "Verificando BASE_URL=$BASE_URL ..."
  curl -sI --max-time 5 "$BASE_URL" > /dev/null || {
    echo "[fail] BASE_URL inaccesible (timeout 5s). Degradar a scaffold-only."
    exit 1
  }
  echo "[ok] BASE_URL alcanzable"
else
  echo "[fail] BASE_URL no definido. Exportar antes de ejecutar el smoke."
  exit 1
fi

if [[ "$AUTH_REQUIRED" == "true" ]]; then
  if [[ -z "$AUTH_TOKEN" ]]; then
    echo "[fail] AUTH_TOKEN requerido por el spec (security) pero no exportado."
    exit 1
  fi
  echo "[ok] AUTH_TOKEN presente"
fi

echo "=== preflight ok ==="
