---
id: appium-validate-inputs-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [appium]
description: Prompt para aplicar las 5 reglas de validación de inputs Appium y emitir un JSON con is_valid, errores y valores coercionados.
tags: [appium, inputs, validation, prompt, json]
---

# Prompt — Validar inputs Appium Screenplay Android

## Variables

- `{{inputs}}` — objeto JSON con los campos del request: `platform_name`, `project_name`, `apk_path`, `include_login_case`, `user_story`, `test_cases`, `app_package`, `app_activity`, `platform_version`, `device_name`, `automation_name`, `appium_server_url`, `selectors`.

## Plantilla

```
Eres un analista QA del Chapter Calidad de Pragma. Recibes los inputs de una solicitud para generar un proyecto Appium V2 Android (Screenplay + Serenity + Cucumber). Aplica las 5 reglas de validacion y emite UN UNICO objeto JSON. No inventes valores. No emitas prosa.

Inputs:
---
{{inputs}}
---

Reglas:

1. Si `platform_name` viene presente y en minusculas no es "android", agregar a `validation_errors`: "En Appium V2 solo se soporta Android.".
2. Si `apk_path` esta ausente o vacio, agregar: "Falta apk_path.".
3. Si `project_name` esta ausente o vacio, agregar: "Falta project_name.".
4. Si NO viene `user_story` Y `test_cases` no tiene al menos 1 item, agregar: "Debes enviar user_story o test_cases para generar escenarios.".
5. Si `include_login_case` esta ausente o no es booleano ni coercible ("true", "1", "si", "sí", "yes"), agregar: "Falta include_login_case (true/false).".

Coercion:
- `include_login_case` strings "true"/"1"/"si"/"sí"/"yes" (case-insensitive) → true; "false"/"0"/"no" → false.
- Otros campos opcionales: aplicar defaults solo si la regla NO falla.
  - `app_package` ausente → "com.example.app"  (marcar en `coerced_values.app_package_is_default=true`).
  - `app_activity` ausente → ".MainActivity"  (marcar en `coerced_values.app_activity_is_default=true`).
  - `platform_version` ausente → "12.0".
  - `device_name` ausente → "Android Emulator".
  - `automation_name` ausente → "UiAutomator2".
  - `appium_server_url` ausente → "http://127.0.0.1:4723".

Produce un JSON con la siguiente forma exacta:

{
  "is_valid": true,
  "validation_errors": [],
  "coerced_values": {
    "include_login_case": true,
    "app_package": "com.example.app",
    "app_package_is_default": true,
    "app_activity": ".MainActivity",
    "app_activity_is_default": true,
    "platform_version": "12.0",
    "device_name": "Android Emulator",
    "automation_name": "UiAutomator2",
    "appium_server_url": "http://127.0.0.1:4723"
  }
}

- `is_valid` es true si `validation_errors` esta vacio, false en caso contrario.
- Si `is_valid` es false, omitir `coerced_values` o dejarlo vacio.
- Mantener el orden de las reglas en `validation_errors`.
```
