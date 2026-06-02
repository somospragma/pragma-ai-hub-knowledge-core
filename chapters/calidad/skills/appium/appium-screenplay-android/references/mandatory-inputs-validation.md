
# Inputs obligatorios y validación

## Tabla de inputs

| Input | Obligatorio | Default | Notas |
|---|---|---|---|
| `project_name` | Sí | — | kebab-case. |
| `apk_path` | Sí | — | ruta absoluta al APK. |
| `include_login_case` | Sí | — | boolean o string coercible: `"true"`, `"si"`, `"sí"`, `"yes"`, `"1"`. |
| `user_story` o `test_cases` | Sí (uno de los dos) | — | mínimo un item si es `test_cases`. |
| `app_package` | No | `com.example.app` | TODO en README si default. |
| `app_activity` | No | `.MainActivity` | TODO en README si default. |
| `platform_version` | No | `12.0` | versión Android. |
| `device_name` | No | `Android Emulator` | nombre del device/emulador. |
| `automation_name` | No | `UiAutomator2` | único driver soportado en V2. |
| `appium_server_url` | No | `http://127.0.0.1:4723` | URL del Appium Server. |
| `selectors` | No | — | si viene, mapear a `AppiumBy.id|xpath|accessibilityId`. |

## 5 reglas de validación

| # | Regla | Mensaje de error |
|---|---|---|
| 1 | `platform_name` (cuando viene) en minúsculas debe ser exactamente `"android"`. | `"En Appium V2 solo se soporta Android."` |
| 2 | `apk_path` no vacío. | `"Falta apk_path."` |
| 3 | `project_name` no vacío. | `"Falta project_name."` |
| 4 | `user_story` presente O `test_cases` con len ≥ 1. | `"Debes enviar user_story o test_cases para generar escenarios."` |
| 5 | `include_login_case` presente (bool o coercible). | `"Falta include_login_case (true/false)."` |

Si cualquier regla falla, **abortar generación** y devolver el mensaje exacto. No intentes adivinar valores.

## Extraer `app_package` y `app_activity` del APK

Procedimiento estándar Android SDK build-tools:

```bash
aapt dump badging /path/to/app.apk | grep -E 'package:|launchable-activity'
```

Salida típica:

```
package: name='com.empresa.app' versionCode='42' versionName='1.4.0'
launchable-activity: name='com.empresa.app.SplashActivity'  label='...' icon='...'
```

Mapear `package: name='X'` → `app_package = X`; `launchable-activity: name='Y'` → `app_activity = Y` (puede ser absoluto o relativo según el manifest).

Si `aapt` no está disponible o `app_package`/`app_activity` no se pueden inferir, generar con los defaults y dejar TODO en README pidiendo al usuario completar.

Rationale del scope Android-only en `[[appium-android-only-scope-rationale]]`.
