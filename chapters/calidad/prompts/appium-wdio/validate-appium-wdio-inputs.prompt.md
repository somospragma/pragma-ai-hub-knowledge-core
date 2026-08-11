---
id: calidad-appium-wdio-validate-inputs-prompt
version: 1.0.0
scope: stack
type: prompt
chapter: calidad
stack: [appium-wdio]
description: Prompt para validar los inputs de una solicitud Appium WebdriverIO y emitir un JSON con is_valid, errores, valores coercionados y prerequisitos de entorno por plataforma.
tags: [appium, webdriverio, inputs, validation, prompt, json]
---

# Prompt — Validar inputs Appium WebdriverIO

## Variables

- `{{inputs}}` — objeto JSON con los campos del request: `project_name`, `output_path`, `platforms`, `app_source`, `execution_mode`, `user_story`, `test_cases`, `locator_map`, `base_url`, `languages`.

## Template

```
Eres un analista QA del Chapter Calidad de Pragma. Recibes los inputs de una solicitud para generar o extender un arquetipo Appium multi-plataforma en TypeScript (WebdriverIO + cucumber-js). Aplica las reglas de validacion y emite UN UNICO objeto JSON. No inventes valores. No emitas prosa.

Inputs:
---
{{inputs}}
---

Reglas de validacion:

1. Si `project_name` esta ausente o vacio, agregar a `validation_errors`: "Falta project_name.".
2. Si `output_path` esta ausente o vacio, agregar: "Falta output_path.".
3. Si `platforms` esta ausente, vacio, o no es un array, agregar: "Falta platforms (array con al menos una plataforma).".
4. Si algun elemento de `platforms` no pertenece a {android, ios, ipad, tablet, android-web, ios-web}, agregar: "Plataforma no soportada: <valor>.".
5. Si `app_source` esta ausente o vacio Y `platforms` contiene alguna plataforma de app nativa (android, ios, ipad, tablet), agregar: "Falta app_source (ruta al binario o identificador de app instalada).".
6. Si `execution_mode` esta ausente o no pertenece a {local, cloud, both}, agregar: "Falta execution_mode (local | cloud | both).".
7. Si NO viene `user_story` Y `test_cases` no tiene al menos 1 item, agregar: "Debes enviar user_story o test_cases para generar escenarios.".
8. Si `platforms` contiene alguna plataforma web (android-web, ios-web) y `base_url` esta ausente, agregar: "Falta base_url para las plataformas de navegador movil.".

Coercion (aplicar solo si ninguna regla fallo):
- `execution_mode` ausente → "local".
- `languages` ausente → ["es"].
- `locator_map` ausente → marcar `locator_map_provided: false`.

Prerequisitos de entorno (no son errores de input: se reportan como advertencias que el agente debe verificar antes de ejecutar):
- Si `platforms` incluye ios, ipad o ios-web → agregar a `environment_prerequisites`: "macOS con Xcode y command line tools", "driver xcuitest instalado en Appium".
- Si `platforms` incluye ios o ipad con dispositivo fisico → agregar: "credenciales de firma (xcodeOrgId, xcodeSigningId)".
- Si `platforms` incluye android, tablet o android-web → agregar: "Android SDK platform-tools en el PATH", "driver uiautomator2 instalado en Appium".
- Si `platforms` incluye android-web o ios-web → agregar: "chromedriver compatible con la version de Chrome o WebView del dispositivo".
- Si `execution_mode` es cloud o both → agregar: "credenciales del device farm por variable de entorno".

Produce un JSON con la siguiente forma exacta:

{
  "is_valid": true,
  "validation_errors": [],
  "coerced_values": {
    "execution_mode": "local",
    "languages": ["es"],
    "locator_map_provided": false
  },
  "environment_prerequisites": [],
  "deferred_selectors_required": true
}

- `is_valid` es true si `validation_errors` esta vacio, false en caso contrario.
- Si `is_valid` es false, omitir `coerced_values` o dejarlo vacio.
- `deferred_selectors_required` es true cuando `locator_map_provided` es false: los selectores se generan diferidos y marcados como pendientes, nunca inventados.
- Mantener el orden de las reglas en `validation_errors`.
```

## Ejemplo de uso

Input con plataformas iOS y sin mapa de identificadores:

```json
{
  "project_name": "suite-mobile",
  "output_path": "./salida/suite-mobile",
  "platforms": ["android", "ios"],
  "app_source": "./app.apk",
  "execution_mode": "local",
  "user_story": "Como usuario quiero autenticarme con usuario y contraseña"
}
```

Salida esperada: `is_valid: true`, `deferred_selectors_required: true`, y los prerequisitos de macOS, Xcode y ambos drivers de Appium en `environment_prerequisites`.
