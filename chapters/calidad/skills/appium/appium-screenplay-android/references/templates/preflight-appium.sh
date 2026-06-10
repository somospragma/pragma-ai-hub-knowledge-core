#!/usr/bin/env bash
set -e
echo "=== Appium Screenplay Android pre-flight ==="

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d. -f1)
echo "Java major version: $JAVA_VERSION"
if [[ "$JAVA_VERSION" != "21" ]]; then
  echo "[fail] Java $JAVA_VERSION detectado. Serenity 4.x + scaffold requiere JDK 21."
  echo "Sugerencia macOS: export JAVA_HOME=\$(/usr/libexec/java_home -v 21)"
  exit 1
fi
echo "[ok] JDK 21 disponible"

if [[ -x "./gradlew" ]]; then
  GRADLE_VERSION=$(./gradlew --version 2>/dev/null | grep '^Gradle' | awk '{print $2}')
  echo "Gradle wrapper version: $GRADLE_VERSION"
  if [[ "$GRADLE_VERSION" != 8.10* ]]; then
    echo "[warn] Gradle $GRADLE_VERSION distinto del esperado 8.10. Ver appium-gradle-version-matrix."
  fi
  echo "[ok] gradlew presente"
else
  echo "[fail] gradlew no encontrado o no ejecutable."
  echo "Sugerencia: gradle wrapper --gradle-version 8.10 && chmod +x gradlew"
  exit 1
fi

if ! command -v appium > /dev/null 2>&1; then
  echo "[fail] appium no encontrado. Sugerencia: npm i -g appium && appium driver install uiautomator2"
  exit 1
fi
APPIUM_VERSION=$(appium --version 2>/dev/null)
echo "Appium version: $APPIUM_VERSION"
APPIUM_MAJOR=$(echo "$APPIUM_VERSION" | cut -d. -f1)
if [[ "$APPIUM_MAJOR" -lt 2 ]]; then
  echo "[fail] Appium $APPIUM_VERSION < 2.0.0. El scaffold requiere V2."
  exit 1
fi
echo "[ok] Appium V2 disponible"

if ! command -v adb > /dev/null 2>&1; then
  echo "[fail] adb no encontrado. Instalar Android SDK platform-tools."
  exit 1
fi

DEVICES=$(adb devices | tail -n +2 | grep -c "device$" || true)
if [[ "$DEVICES" -eq 0 ]]; then
  echo "[warn] adb no detecta devices/emuladores. Modo full no ejecutable; degradar a scaffold-only."
else
  echo "[ok] $DEVICES device(s) detectado(s)"
fi

if [[ -n "$APK_PATH" ]]; then
  if [[ ! -f "$APK_PATH" ]]; then
    echo "[fail] APK_PATH=$APK_PATH no existe"
    exit 1
  fi
  if command -v aapt > /dev/null 2>&1; then
    PKG=$(aapt dump badging "$APK_PATH" 2>/dev/null | grep "^package:" | head -n 1)
    echo "APK package info: $PKG"
  else
    echo "[warn] aapt no disponible; no se puede leer appPackage/appActivity reales"
  fi
fi

echo "=== preflight ok ==="
