#!/usr/bin/env bash
set -e
echo "=== Playwright pre-flight ==="

NODE_VERSION=$(node --version 2>/dev/null | sed 's/^v//' | cut -d. -f1)
if [[ -z "$NODE_VERSION" ]]; then
  echo "[fail] node no encontrado en PATH"
  exit 1
fi
echo "Node major version: $NODE_VERSION"
if [[ "$NODE_VERSION" -lt 18 ]]; then
  echo "[fail] Node $NODE_VERSION < 18. Playwright 1.45.x requiere Node 18+."
  echo "Sugerencia: nvm install 18 && nvm use 18"
  exit 1
fi
echo "[ok] Node $NODE_VERSION compatible"

npx --no-install playwright --version > /dev/null 2>&1 || npx playwright --version > /dev/null 2>&1 || {
  echo "[fail] playwright CLI no disponible. Ejecutar: npm i -D @playwright/test"
  exit 1
}
echo "[ok] Playwright CLI disponible"

if [[ ! -d "${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}" ]]; then
  echo "[warn] cache de browsers no encontrado. Ejecutar: npx playwright install --with-deps"
fi

if [[ -n "$BASE_URL" ]]; then
  echo "Verificando BASE_URL=$BASE_URL ..."
  curl -sI --max-time 5 "$BASE_URL" > /dev/null || {
    echo "[fail] BASE_URL inaccesible (timeout 5s). Degradar a scaffold-only."
    exit 1
  }
  echo "[ok] BASE_URL alcanzable"
else
  echo "[warn] BASE_URL no definido. Suite @live no podrá ejecutarse hasta exportarlo."
fi

if [[ -n "$BACKEND_URL" ]]; then
  echo "Verificando BACKEND_URL=$BACKEND_URL ..."
  curl -sI --max-time 5 "$BACKEND_URL" > /dev/null || {
    echo "[fail] BACKEND_URL inaccesible (timeout 5s)."
    exit 1
  }
  echo "[ok] BACKEND_URL alcanzable"
fi

echo "=== preflight ok ==="
