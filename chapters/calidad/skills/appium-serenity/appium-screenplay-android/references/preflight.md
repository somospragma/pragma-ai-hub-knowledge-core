# Pre-flight check — Appium Screenplay Android greenfield

Antes de generar el proyecto Appium Screenplay Android el agente debe validar el toolchain local (Gradle wrapper, Appium server, ADB, JDK 21) y la presencia de al menos un device o emulador cuando el modo de operación pide runtime real. El protocolo de enforcement está descrito en `[[calidad-pre-generation-protocol]]`.

## Validaciones obligatorias

- `./gradlew --version` debe responder con Gradle 8.10 (versión esperada, ver ``gradle-version-matrix.md``). Si el wrapper no existe en el path destino, sugerir crearlo con `gradle wrapper --gradle-version 8.10`.
- `appium --version` debe responder con Appium V2 (≥ 2.0.0). En V1 el flujo NO es compatible con el driver `UiAutomator2` que usa el scaffold.
- `adb devices` debe listar al menos un device o emulador cuando el operador eligió modo `full`. En `scaffold-only` esta validación es informativa, no bloqueante.
- `aapt dump badging $APK_PATH | grep package` debe leer `appPackage` y `appActivity` reales del APK. Si los valores difieren de los inputs declarados, ofrecer al usuario sobrescribir antes de generar.
- JDK 21 disponible (`java -version` debe reportar `21.x`). Versiones inferiores rompen Serenity 4.x.

## Degradación cuando `adb devices` está vacío

Si no hay device ni emulador activo y el operador pidió modo `full`, ofrecer al usuario las siguientes opciones:

1. Arrancar emulador automáticamente: `emulator -avd <nombre>` (requiere SDK Android instalado y al menos un AVD configurado).
2. Degradar a `scaffold-only`: el scaffold queda válido pero el runtime no se ejecuta. Reportar `partial`.
3. Usar device cloud (BrowserStack, SauceLabs, AWS Device Farm). En este caso, el `android.conf` se ajusta para apuntar al endpoint remoto y se sustituyen capabilities por las del proveedor.

Documentar la decisión en `.evidence/preflight-result.json`.

## Degradación cuando `gradlew` falta

Si el directorio destino no contiene `gradlew`/`gradlew.bat`, sugerir crearlo con `gradle wrapper --gradle-version 8.10` antes de generar. Si Gradle no está instalado a nivel sistema, el scaffold incluirá el wrapper completo (`gradle-wrapper.jar` + `gradle-wrapper.properties`) y bastará con `chmod +x gradlew`.

## Script shippeable

El agente debe copiar ``references/templates.md` (sección `preflight-appium.sh`)` al proyecto generado bajo `scripts/preflight.sh`. El script reproduce las validaciones en CI o en máquinas de desarrolladores. Ver `[[calidad-delivery-gate-contract]]` para la convención de entregables y `[[calidad-post-generation-protocol]]` para el archivado del resultado del pre-flight.
