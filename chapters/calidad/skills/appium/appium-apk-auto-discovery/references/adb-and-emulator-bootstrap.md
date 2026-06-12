# ADB + Emulator + Appium Bootstrap

Esta referencia consolida los comandos necesarios para llevar el entorno desde "cero" hasta "listo para crear sesión Appium". El skill no asume que el operador tiene emulador corriendo ni Appium server arrancado; valida cada precondición y arranca lo que falte.

## 1. Verificar adb

```bash
adb version
adb devices
```

Esperado: la salida lista al menos un device en estado `device` (no `unauthorized`, no `offline`).

Ejemplo aceptable:

```
List of devices attached
emulator-5554   device
```

Ejemplo NO aceptable (abortar y reportar):

```
List of devices attached
emulator-5554   unauthorized
```

Resolución manual del `unauthorized`: aceptar el diálogo de RSA en el device. El skill NO toca el device físico interactivamente; reporta al usuario.

## 2. Arrancar emulador (solo si no hay device físico)

Listar AVDs disponibles:

```bash
emulator -list-avds
```

Arrancar uno en background:

```bash
nohup emulator -avd <nombre_avd> -no-snapshot-load -no-boot-anim -netdelay none -netspeed full > /tmp/emulator.log 2>&1 &
```

Esperar boot completo (bloqueante, hasta ~90s):

```bash
adb wait-for-device
until [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = "1" ]; do
  sleep 2
done
```

Si pasa de 120 s sin completar → matar emulador y reportar `partial` al usuario.

## 3. Validar APK e instalar

Validar legibilidad y extraer metadata:

```bash
aapt dump badging "$APK_PATH" | head -20
```

Buscar:

- `package: name='com.example.app'` → `appPackage`
- `launchable-activity: name='com.example.app.MainActivity'` → `appActivity`

Si `aapt dump badging` falla → abortar auto-discovery, caer a deferred.

Instalar (o reinstalar):

```bash
adb install -r -g "$APK_PATH"
```

Flags: `-r` reinstala manteniendo data; `-g` concede todos los runtime permissions (importante para que el crawl no se trabe en diálogos de permisos).

## 4. Lanzar la app

```bash
adb shell am start -n "$APP_PACKAGE/$APP_ACTIVITY"
```

Esperar ~2 s a que la activity esté en foreground. Verificar con:

```bash
adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'
```

Debe mencionar `$APP_PACKAGE`.

## 5. Arrancar Appium server local

Verificar primero si ya hay uno corriendo:

```bash
curl -s -m 3 http://127.0.0.1:4723/status | jq -r '.value.ready'
```

Si retorna `true` → reusar. Si no responde → arrancar:

```bash
nohup appium --address 127.0.0.1 --port 4723 --base-path / --log-level info > /tmp/appium.log 2>&1 &
APPIUM_PID=$!
echo $APPIUM_PID > /tmp/appium.pid
```

Esperar readiness (hasta ~30 s):

```bash
until curl -s -m 2 http://127.0.0.1:4723/status | jq -e '.value.ready == true' >/dev/null 2>&1; do
  sleep 1
done
```

Persistir el PID para poder limpiar después (ver `safety-and-cleanup.md`).

## 6. Cleanup (resumen — detalle completo en `safety-and-cleanup.md`)

Al terminar el crawl (éxito o error):

```bash
# 1. Cerrar sesión Appium (vía DELETE /session/{id})

# 2. Desinstalar la app
adb uninstall "$APP_PACKAGE" || true

# 3. Matar appium server SOLO si nosotros lo arrancamos
if [ -f /tmp/appium.pid ]; then
  kill "$(cat /tmp/appium.pid)" 2>/dev/null || true
  rm /tmp/appium.pid
fi

# 4. Opcional: cerrar emulador SOLO si nosotros lo arrancamos
# adb -s emulator-5554 emu kill
```

## Matriz de fallos comunes

| Síntoma | Causa probable | Acción |
|---|---|---|
| `adb devices` vacío | No hay emulador, ni device USB conectado | Arrancar emulador o pedir al usuario conectar device |
| Device en `unauthorized` | Falta aceptar RSA prompt | Reportar al usuario, abortar |
| `aapt: command not found` | Android SDK build-tools no en PATH | Reportar; degradar a deferred |
| `appium: command not found` | Appium no instalado | `npm i -g appium` o degradar a deferred |
| `/status` no responde | Server colgado o port en uso | Matar PID y reintentar una vez |
| Boot no completa en 120 s | AVD corrupto o sistema lento | Reportar `partial`, degradar a deferred |
