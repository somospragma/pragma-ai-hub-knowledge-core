# Safety & Cleanup

El skill manipula recursos compartidos: device/emulador, Appium server, instalación de APK. Dejar cualquiera de ellos en estado dirty es inaceptable porque rompe el siguiente crawl, ensucia builds CI, y puede causar comportamientos confusos para el usuario al día siguiente. Este documento define el contrato de cleanup obligatorio.

## Inventario de recursos a limpiar

| Recurso | Origen | Cleanup |
|---|---|---|
| Sesión Appium | `POST /session` durante el crawl | `DELETE /session/{id}` |
| APK instalado | `adb install -r` durante bootstrap | `adb uninstall $APP_PACKAGE` |
| Appium server | `appium --address ...` (solo si lo arrancamos nosotros) | `kill $APPIUM_PID` |
| Emulador | `emulator -avd ...` (solo si lo arrancamos nosotros) | `adb -s $SERIAL emu kill` |
| Archivos temporales | `/tmp/appium.log`, `/tmp/emulator.log`, `/tmp/appium.pid` | `rm -f` |

## Reglas

1. **Cleanup es siempre en `finally`** — ya sea que el crawl haya tenido éxito o haya fallado por excepción.
2. **Cleanup respeta lo que NO arrancamos** — si el usuario ya tenía Appium server corriendo, NO matarlo. Detección: archivo `/tmp/appium.pid` solo existe si nosotros lo arrancamos.
3. **Cleanup tolera errores individuales** — cada paso usa `|| true` en bash o try/except en Python; falla un paso, intentar los demás.
4. **Cleanup persiste su propio resultado** — `.evidence/cleanup-result.json` documenta qué se limpió, qué falló, y qué comandos manuales aplicar si quedó algo pendiente.

## Secuencia canónica

### Pseudocódigo

```python
def cleanup(state):
    result = {"session_closed": False, "apk_uninstalled": False,
              "appium_killed": False, "emulator_killed": False,
              "errors": []}

    # 1. Cerrar sesión Appium
    if state.session_id:
        try:
            requests.delete(f"http://127.0.0.1:4723/session/{state.session_id}", timeout=10)
            result["session_closed"] = True
        except Exception as e:
            result["errors"].append({"step": "delete_session", "error": str(e)})

    # 2. Desinstalar APK
    if state.app_package:
        rc = subprocess.run(["adb", "uninstall", state.app_package], capture_output=True)
        if rc.returncode == 0:
            result["apk_uninstalled"] = True
        else:
            result["errors"].append({"step": "uninstall", "error": rc.stderr.decode()})

    # 3. Kill Appium SOLO si nosotros lo arrancamos
    if state.we_started_appium and os.path.exists("/tmp/appium.pid"):
        try:
            pid = int(open("/tmp/appium.pid").read().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(2)
            # SIGKILL si sigue vivo
            try:
                os.kill(pid, 0)
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.remove("/tmp/appium.pid")
            result["appium_killed"] = True
        except Exception as e:
            result["errors"].append({"step": "kill_appium", "error": str(e)})

    # 4. Kill emulador SOLO si nosotros lo arrancamos
    if state.we_started_emulator and state.emulator_serial:
        rc = subprocess.run(["adb", "-s", state.emulator_serial, "emu", "kill"],
                            capture_output=True)
        if rc.returncode == 0:
            result["emulator_killed"] = True
        else:
            result["errors"].append({"step": "kill_emulator", "error": rc.stderr.decode()})

    # 5. Persistir resultado
    write_json(".evidence/cleanup-result.json", result)
    return result
```

### Bash equivalente (para skills no-Python)

```bash
cleanup() {
  local errors=()

  # 1. Cerrar sesión Appium
  if [ -n "$SESSION_ID" ]; then
    curl -s -X DELETE "http://127.0.0.1:4723/session/$SESSION_ID" -m 10 \
      || errors+=("delete_session_failed")
  fi

  # 2. Desinstalar APK
  if [ -n "$APP_PACKAGE" ]; then
    adb uninstall "$APP_PACKAGE" >/dev/null 2>&1 \
      || errors+=("uninstall_failed:$APP_PACKAGE")
  fi

  # 3. Kill Appium si lo arrancamos
  if [ -f /tmp/appium.pid ]; then
    kill "$(cat /tmp/appium.pid)" 2>/dev/null \
      || errors+=("kill_appium_failed")
    sleep 2
    kill -9 "$(cat /tmp/appium.pid)" 2>/dev/null || true
    rm -f /tmp/appium.pid
  fi

  # 4. Kill emulador si lo arrancamos
  if [ -n "$WE_STARTED_EMULATOR" ] && [ -n "$EMULATOR_SERIAL" ]; then
    adb -s "$EMULATOR_SERIAL" emu kill 2>/dev/null \
      || errors+=("kill_emulator_failed")
  fi

  # 5. Persistir resultado
  printf '{"errors":[%s]}\n' "$(IFS=,; echo "${errors[*]/#/\"}" | sed 's/,/", "/g')\"" \
    > .evidence/cleanup-result.json
}

trap cleanup EXIT INT TERM
```

## Manejo de fallos de cleanup

Si después de cleanup quedan errores en el resultado, REPORTAR al usuario con comandos manuales explícitos:

```
Cleanup parcial. Comandos manuales recomendados:

  # Si quedó la app instalada:
  adb uninstall com.example.app

  # Si quedó el server colgado:
  pkill -f appium

  # Si quedó el emulador encendido:
  adb -s emulator-5554 emu kill
  
  # O simplemente:
  pkill -f emulator
```

NUNCA declarar `success` si cleanup tuvo errores no recuperables. Degradar a `partial` y documentar.

## Anti-patterns

- **NO** usar `pkill -f appium` indiscriminadamente: puede matar el server del usuario que existía antes.
- **NO** ejecutar `adb kill-server`: afecta otras conexiones del usuario.
- **NO** asumir que cleanup terminó por silencio: validar con `adb shell pm list packages | grep $APP_PACKAGE` (debe NO aparecer) y `curl /status` (debe fallar si lo matamos).
- **NO** dejar `.evidence/` sin el `cleanup-result.json`: si el archivo falta, el siguiente paso no puede auditar.

## Integración con el lifecycle del skill

```
try:
    bootstrap()          # adb, emulator, appium, install APK, launch
    crawl()              # discovery loop
    extract_selectors()  # post-process
    generate_pages()     # emit Java
except Exception as e:
    log_failure(e)
    raise
finally:
    cleanup()            # SIEMPRE
```

`cleanup()` se llama incluso si `bootstrap()` falló parcialmente — el flag `we_started_X` en el state controla qué intentar limpiar de forma idempotente.
