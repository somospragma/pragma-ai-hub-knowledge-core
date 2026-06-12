#!/usr/bin/env bash
set -e
echo "=== Karate pre-flight ==="
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}' | cut -d. -f1)
echo "Java major version: $JAVA_VERSION"
if [[ "$JAVA_VERSION" == "11" || "$JAVA_VERSION" == "17" ]]; then
  echo "[ok] Java $JAVA_VERSION compatible con Karate 1.4.1"
else
  echo "[fail] Java $JAVA_VERSION incompatible. Karate 1.4.1 requiere 11 o 17."
  echo "Sugerencia: export JAVA_HOME=\$(/usr/libexec/java_home -v 11) && export PATH=\$JAVA_HOME/bin:\$PATH"
  exit 1
fi
mvn -version > /dev/null 2>&1 || { echo "[fail] mvn no encontrado"; exit 1; }
echo "[ok] Maven disponible"
echo "=== preflight ok ==="
