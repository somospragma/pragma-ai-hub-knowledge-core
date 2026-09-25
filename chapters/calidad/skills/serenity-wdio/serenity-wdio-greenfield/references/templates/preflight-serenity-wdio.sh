#!/usr/bin/env bash
# Pre-flight check para el arquetipo serenity-wdio (WebdriverIO v9 + Serenity/JS v3 + Cucumber 11).
# Uso: ./scripts/preflight.sh [web|web_movil|movil|desktop|api]
# Sin argumento, valida solo el toolchain comun.

set -uo pipefail

MODE="${1:-}"
FAIL=0

echo "== Pre-flight serenity-wdio =="

# --- Comun a todas las plataformas ---
if ! command -v node >/dev/null 2>&1; then
  echo "FALLO: node no encontrado. Se requiere Node.js 18+."
  FAIL=1
else
  NODE_MAJOR="$(node -v | sed 's/^v//' | cut -d. -f1)"
  if [ "$NODE_MAJOR" -lt 18 ]; then
    echo "FALLO: Node.js $(node -v) detectado. Se requiere >= 18."
    FAIL=1
  else
    echo "OK: Node.js $(node -v)"
  fi
fi

if ! npx --no-install wdio --version >/dev/null 2>&1; then
  echo "AVISO: @wdio/cli no resuelve via npx todavia (normal antes de npm install)."
else
  echo "OK: wdio CLI disponible"
fi

# Deteccion de duplicacion de @cucumber/cucumber (causa raiz de "instance of Cucumber
# that isn't running (status: PENDING)" — ver serenity-wdio-troubleshooting Problema 10).
if [ -d "node_modules" ]; then
  CUCUMBER_COPIES="$(find node_modules -type d -name "cucumber" -path "*@cucumber/cucumber" 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$CUCUMBER_COPIES" -gt 1 ]; then
    echo "FALLO: se detectaron $CUCUMBER_COPIES copias de @cucumber/cucumber en node_modules. Aplicar 'overrides' en package.json (ver references/package-dependencies.md) antes de ejecutar."
    FAIL=1
  elif [ "$CUCUMBER_COPIES" -eq 1 ]; then
    echo "OK: una sola copia de @cucumber/cucumber detectada"
  fi
fi

# --- Especifico por modo ---
case "$MODE" in
  web|web_movil)
    if [ -n "${BASE_URL:-}" ]; then
      if curl -sI --max-time 5 "$BASE_URL" >/dev/null 2>&1; then
        echo "OK: BASE_URL accesible ($BASE_URL)"
      else
        echo "FALLO: BASE_URL no responde en 5s ($BASE_URL). Degradar a scaffold-only."
        FAIL=1
      fi
    else
      echo "AVISO: BASE_URL no definida en el entorno."
    fi
    ;;
  movil)
    PLATFORM="${MOBILE_PLATFORM:-${PLATFORM:-}}"
    if [ "$PLATFORM" = "android" ]; then
      if command -v adb >/dev/null 2>&1; then
        if adb devices | grep -qE "device$"; then
          echo "OK: al menos un device/emulador Android detectado"
        else
          echo "AVISO: adb devices no lista devices activos. Modo full requiere uno."
          FAIL=1
        fi
      else
        echo "FALLO: adb no encontrado en PATH."
        FAIL=1
      fi
      if ! command -v appium >/dev/null 2>&1; then
        echo "AVISO: appium CLI no encontrado en PATH (puede estar como dependencia local)."
      fi
    elif [ "$PLATFORM" = "ios" ]; then
      if command -v xcrun >/dev/null 2>&1; then
        if xcrun simctl list devices 2>/dev/null | grep -q "Booted\|Shutdown"; then
          echo "OK: xcrun simctl responde (simuladores disponibles)"
        else
          echo "AVISO: no se detectaron simuladores iOS listados."
        fi
      else
        echo "FALLO: xcrun no disponible. Se requiere macOS + Xcode para iOS."
        FAIL=1
      fi
    else
      echo "FALLO: MOBILE_PLATFORM/PLATFORM debe ser android o ios."
      FAIL=1
    fi
    ;;
  desktop)
    echo "AVISO: validar manualmente Appium Windows Driver y la ruta al binario .exe."
    ;;
  api)
    if [ -n "${API_BASE_URL:-}" ]; then
      if curl -sI --max-time 5 "$API_BASE_URL" >/dev/null 2>&1; then
        echo "OK: API_BASE_URL accesible ($API_BASE_URL)"
      else
        echo "FALLO: API_BASE_URL no responde en 5s ($API_BASE_URL)."
        FAIL=1
      fi
    else
      echo "AVISO: API_BASE_URL no definida en el entorno."
    fi
    ;;
  *)
    echo "AVISO: modo no especificado o no reconocido ($MODE). Solo se valido el toolchain comun."
    ;;
esac

if [ "$FAIL" -ne 0 ]; then
  echo "== Resultado: FALLO. Ver detalles arriba. =="
  exit 1
fi

echo "== Resultado: OK =="
exit 0
