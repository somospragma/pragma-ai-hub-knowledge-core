# STRATEGY.md — {{project_name}} (serenity-wdio)

Documento de estrategia previo a la generación de código. Debe estar aprobado explícitamente por el usuario antes de emitir el primer archivo. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — {{sut_description}}
- Tipo: Web / Web móvil (WebView) / Móvil nativo (Android/iOS) / Desktop / API — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico del SUT: {{sut_stack}}
- Tipo de relación: greenfield (proyecto serenity-wdio nuevo)
- Bundle ID / Package (si mobile): {{bundle_id_or_package}} (verificado con `aapt dump badging` / `PlistBuddy`, nunca supuesto)

## 2. Volumen y SLAs

- Disponibilidad esperada del SUT durante la corrida (% uptime): {{availability}}
- Tiempo de respuesta máximo tolerable por página/endpoint crítico: {{response_time_sla}}
- Error rate aceptable en happy paths: 0%
- Tasa de fallo aceptable en la suite `@smoke`: 0% (debe pasar determinísticamente)

## 3. Alcance funcional

- Plataformas en scope (marcar las que apliquen): [ ] web [ ] web_movil [ ] movil-android [ ] movil-ios [ ] desktop [ ] api
- Módulos / historias en scope: {{modules_in_scope}}
- Módulos / historias fuera de scope: {{modules_out_of_scope}} (justificación: {{out_of_scope_reason}})
- Criterios de aceptación por módulo: {{acceptance_criteria}}
- User story principal: {{user_story_id}} — {{user_story_summary}}

## 4. Dependencias externas

- Auth: {{auth_type}} ({{auth_endpoint}}) — aplica a `web`/`api` cuando el flujo requiere login real.
- Base URL / target: {{base_url_or_target}} (web/api: URL; móvil/desktop: ruta al binario `.apk`/`.app`/`.ipa`/`.exe`).
- Servicios externos consumidos por el SUT (mockear o probar): {{external_services}}

## 5. Riesgos conocidos

- WAF en ambiente de prueba (web/api): {{waf_status}} — proveedor: {{waf_provider}}
- Rate limits documentados (api): {{rate_limits}}
- Datos sensibles tratados: {{sensitive_data}}
- Restricciones regulatorias: {{regulatory_constraints}} (fuerza modo `dry-run` si aplica)
- Disponibilidad de device/emulador Android o simulador iOS para runtime real: {{device_availability}}

## 6. Próximos pasos

- Archivos a generar (alto nivel): estructura completa del arquetipo (`configs/wdio.*.conf.ts`, `.env.<modo>`, `scripts/run.mjs`, `features/<canal>/**`, `step-definitions/**`).
- Comando de ejecución: `node ./scripts/run.mjs --mode=<modo> [--platform=<android|ios>] --tags=@smoke`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) generado por `[[generate-executive-report]]` al cierre.

## 7. Estrategia serenity-wdio

### 7.1 Plataformas, modos y configs

| Plataforma declarada | `--mode` | `--platform` | Config generado | Env generado |
|---|---|---|---|---|
| {{plataforma_1}} | {{modo_1}} | {{platform_1_o_na}} | `configs/wdio.{{modo_1}}.conf.ts` | `.env.{{modo_1}}` |

### 7.2 Capabilities y verificación de identificadores (solo mobile/desktop)

- Android: `app_package` / `app_activity` verificados con `aapt dump badging {{apk_path}}`.
- iOS: `bundle_id` verificado con `PlistBuddy -c "Print :CFBundleIdentifier" {{app_path}}/Info.plist`.
- Desktop: ruta absoluta al binario `.exe` verificada.

### 7.3 Locator strategy

- Web: `PageElement.located(By.css|xpath)` — prioridad `data-testid` > `id` > `clase` > `xpath`.
- Mobile: selectores `string` — prioridad Accessibility ID (`~id`) > TestID > texto visible > `android=`/`-ios predicate` > XPath (último recurso). Locators no confirmados quedan `DEFERRED` (ver `[[complete-deferred-locators]]`), nunca inventados.

### 7.4 Screenplay conventions

- Tasks componen Interactions con `Task.where`; Questions sin efectos secundarios.
- Web usa `@serenity-js/web`; mobile encapsula `browser.$` únicamente dentro de Interactions. Prohibido `Target`, `resolveFor(actor)`, `browser.$` directo en Tasks/Steps, hard waits.

### 7.5 Datos de prueba por módulo

- {{modulo}}: fuente de datos ({{fixtures_o_factory}}), estrategia de aislamiento entre escenarios (ver `[[calidad-test-data-management]]` y `references/serenity-wdio-test-data-management.md`).

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar la estructura del proyecto. Cambios posteriores requieren actualizar este documento y re-aprobar.
