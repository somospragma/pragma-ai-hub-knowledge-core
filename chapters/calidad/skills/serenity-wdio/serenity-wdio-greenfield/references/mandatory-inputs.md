# Inputs obligatorios (Serenity WDIO Greenfield)

Antes de generar cualquier archivo se validan los inputs obligatorios. Si alguno falta, rechazar la solicitud indicando el input faltante por nombre. La verificacion es binaria: presente o ausente.

## Inputs comunes

| Input | Descripcion | Regla |
|---|---|---|
| `project_name` | Nombre del proyecto/carpeta raiz | Obligatorio, kebab-case |
| `platform_context` | web \| web_movil \| movil \| desktop \| api | Obligatorio, nunca asumido |
| `base_url` o `target` | URL base (web/api) o app bajo prueba (movil/desktop) | Obligatorio segun el contexto |

## Inputs por contexto movil nativo

| Input | Descripcion | Regla |
|---|---|---|
| `platform_name` | android \| ios | Obligatorio en modo movil |
| `app` | Ruta absoluta al binario (`.apk`, `.app`, `.ipa`) | Preferido; permite deducir identificadores |
| `app_package` / `app_activity` (Android) | Identificadores del binario | Verificar contra el binario real |
| `bundle_id` (iOS) | `CFBundleIdentifier` real | Verificar contra el binario real |

## Verificacion obligatoria del Bundle ID / Package

Nunca inventar el identificador a partir del nombre del repo o del binario. Leer el identificador real del binario antes de fijarlo en `.env.movil.*`:

```bash
# iOS desde un .app
/usr/libexec/PlistBuddy -c "Print :CFBundleIdentifier" ./apps/ios/<App>.app/Info.plist

# Android desde un .apk
aapt dump badging ./apps/android/<App>.apk | grep -E "package|launchable"
```

Si en `wdio.<ios|android>.conf.ts` se provee `appium:app`, el `bundleId` / `appPackage` se vuelve opcional porque Appium lo deduce del binario. Preferir esta forma.

## Enlace transversal

La validacion se alinea con el protocolo `[[calidad-mandatory-inputs-protocol]]`, que define el contrato de inputs obligatorios y el mensaje de rechazo por input faltante.
