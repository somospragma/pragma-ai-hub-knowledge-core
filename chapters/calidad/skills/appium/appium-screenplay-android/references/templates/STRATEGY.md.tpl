# STRATEGY.md — {{project_name}} (Appium Android)

Documento de estrategia previo a la generación de scaffolding Gradle / Screenplay / Cucumber. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.feature` o `.java`. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- App bajo prueba: {{app_name}} — {{app_description}}
- Tipo de SUT: Mobile Android nativa / híbrida — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico de la app: {{app_stack}}
- Tipo de relación: greenfield (proyecto Appium nuevo)
- iOS: NO está en scope (`[[appium-android-only-scope-rationale]]`).
- APK: {{apk_path}} (validado vía `aapt dump badging`)
- `app_package`: {{app_package}} (default `com.example.app` si falta — declarar TODO en README)
- `app_activity`: {{app_activity}} (default `.MainActivity` si falta — declarar TODO en README)
- Firma: {{firma}}

## 2. Volumen y SLAs

Appium cubre validación E2E mobile. Los SLAs aplicables:

- Cumplimiento por feature: 100% de los escenarios `@android @smoke` pasan determinísticamente en la device matrix declarada.
- Tiempo de arranque máximo de la app: {{startup_time_max}} ms (verificado por `AppIsResponsive`).
- Cobertura de locators reales: >= {{real_locators_pct}}% (si se eligió auto-discovery).
- Disponibilidad de Appium server durante la corrida: 100%.

| Métrica | Valor declarado |
|---|---|
| % éxito por feature @smoke por device | 100% |
| Startup máximo app | {{startup_time_max}} ms |
| Locators reales resueltos | >= {{real_locators_pct}}% |

## 3. Alcance funcional

- Screens / features en scope: {{features_in_scope}}
- Screens / features fuera de scope: {{features_out_of_scope}} ({{out_of_scope_reason}})
- User stories: {{user_stories}}
- Test cases adicionales (`@proposed`): {{test_cases}}

## 4. Dependencias externas

- Auth: {{auth_strategy}} (login real con credenciales reales, login mockeado backend, sin auth).
- Backend al que la app consume: {{backend_url}}
- Servicios push / notifications / 3rd party SDKs: {{external_sdks}}
- Data de prueba: {{test_data_strategy}} (usuario seed, cleanup post-run, etc.)

## 5. Riesgos conocidos

- Estabilidad del emulador / device: {{device_stability_risk}}
- Variabilidad por versión de Android: {{android_version_variability}}
- Permisos runtime (cámara, ubicación, notificaciones): {{runtime_permissions}}
- Datos sensibles tratados por la app: {{sensitive_data}}
- Restricciones regulatorias: {{regulatory_constraints}}

## 6. Próximos pasos

- Archivos a generar: `build.gradle`, `settings.gradle`, `gradlew`, `gradle/wrapper/gradle-wrapper.properties`, `serenity.properties`, `android.conf`, `README.md`, Page Objects bajo `co.com.pragma.*`, Tasks (`LoginTask`, etc.), `*.feature` con escenarios `@smoke` + `@proposed`, `LoginRunner.java`.
- Comando de ejecución: `./gradlew clean test aggregate -p <project_path> -Dcucumber.filter.tags=@smoke`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) con device matrix y locators auto-discovery vs deferred.

## 7. Estrategia Appium

### 7.1 Capabilities

| Capability | Valor |
|---|---|
| platformName | Android |
| platformVersion | {{platform_version}} (default 12.0) |
| deviceName | {{device_name}} (default `Android Emulator`) |
| automationName | {{automation_name}} (default `UiAutomator2`) |
| appPackage | {{app_package}} |
| appActivity | {{app_activity}} |
| app | {{apk_path}} |
| appiumServerUrl | {{appium_server_url}} (default `http://127.0.0.1:4723`) |
| noReset | {{no_reset}} |
| autoGrantPermissions | {{auto_grant_permissions}} |

### 7.2 Device matrix

| Device | Tipo | OS | Form factor | Prioridad |
|---|---|---|---|---|
| Pixel 6 (emulador) | emulator | Android 12 | phone | CRITICAL |
| Galaxy S22 (real) | real | Android 13 | phone | HIGH |
| Galaxy A52 (real) | real | Android 11 | phone | MEDIUM |

(Editar la matrix según devices realmente disponibles. Cada celda del reporte ejecutivo se desglosa por feature en esta matrix.)

### 7.3 Screens identificadas

| Screen | Page Object | Selectores estimados | Locator source |
|---|---|---|---|
| Login | LoginPage | 5 | {{login_locator_source}} |
| Dashboard | DashboardPage | 12 | {{dashboard_locator_source}} |
| Checkout | CheckoutPage | 8 | {{checkout_locator_source}} |

### 7.4 Locator strategy

- Modo: {{locator_mode}} (`auto-discovery` o `deferred`).
- Si `auto-discovery`: el agente recorre la app vía APK + emulador + Appium server (paso 4 del workflow) y persiste resultados en `.evidence/locators-discovered.json` con score de confianza por locator. Aplica `[[appium-apk-auto-discovery]]`.
- Si `deferred`: cada Page Object queda con `// TODO: update real locator`. El usuario completa después con `[[complete-deferred-locators]]` usando Appium Inspector.

### 7.5 Escenarios `@smoke` y `@proposed`

- 2 escenarios `@android @smoke` mínimos siempre: arranque + login básico (si `include_login_case = true`).
- N escenarios `@android @proposed` derivados de `user_story` / `test_cases`. Cumplir `[[appium-gherkin-syntax-rules]]` (≤80 chars por línea, newlines a espacios).

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar el scaffold Gradle + Screenplay.
