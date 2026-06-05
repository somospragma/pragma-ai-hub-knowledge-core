# STRATEGY.md — {{project_name}} (Karate)

Documento de estrategia previo a la generación de código. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.feature`. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — {{sut_description}}
- Tipo: API REST / SOAP / GraphQL — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}}
- Stack tecnológico del SUT: {{sut_stack}}
- Tipo de relación: greenfield (proyecto Karate nuevo)
- Spec: {{spec_path}} ({{spec_format}}: OpenAPI 3.x / Swagger 2.0 / WSDL)
- Firma: {{firma}}

## 2. Volumen y SLAs

Karate cubre validación funcional y contract. Los SLAs de performance no se ejercitan aquí (eso es K6), pero sí los SLAs funcionales:

- Disponibilidad esperada del SUT durante la corrida (% uptime).
- Tiempo de respuesta máximo tolerable por endpoint para que un test no sea considerado timeout (no es SLA, es timeout técnico).
- Error rate aceptable en happy paths: 0%.
- Tasa de fallo aceptable en suite completa: 0% (todos los tests deben pasar determinísticamente).

| Métrica | Valor declarado |
|---|---|
| Disponibilidad SUT en corrida | {{availability}} |
| Timeout por request | {{request_timeout}} ms |
| Error rate happy paths | 0% |

## 3. Alcance funcional

- Endpoints en scope: {{endpoints_in_scope}}
- Endpoints fuera de scope: {{endpoints_out_of_scope}} (justificación: {{out_of_scope_reason}})
- Criterios de aceptación por endpoint: {{acceptance_criteria}}
- User story principal: {{user_story_id}} — {{user_story_summary}}

## 4. Dependencias externas

- Auth: {{auth_type}} ({{auth_endpoint}}). Si el spec NO declara `security`, no se emite `Authorization` (regla `[[calidad-mandatory-inputs-protocol]]`).
- Base URL: {{base_url}} (también disponible como variable `{{baseUrlVar}}` en `karate-config.js`).
- Servicios externos consumidos por el SUT (mockear o probar): {{external_services}}

## 5. Riesgos conocidos

- WAF en ambiente de prueba: {{waf_status}} — proveedor: {{waf_provider}}, allowlist coordinada: {{waf_allowlist}}
- Rate limits documentados: {{rate_limits}}
- Datos sensibles tratados: {{sensitive_data}}
- Restricciones regulatorias: {{regulatory_constraints}}

## 6. Próximos pasos

- Archivos a generar (alto nivel): `pom.xml`, `karate-config.js`, `TestRunner.java`, features bajo `src/test/java/com/testing/features/`, schemas `-match.json`.
- Comando de ejecución: `mvn test` (filtros opcionales por tag).
- Reporte ejecutivo: formato {{report_format}} (default `html`) generado por `[[generate-executive-report]]` al cierre.

## 7. Estrategia Karate

### 7.1 Cobertura por endpoint (effective_minimum)

Aplicar la fórmula `[[karate-negative-coverage-formula]]`. Declarar antes de generar:

| Endpoint | Effective minimum | Required fields | Headers críticos | Cobertura cifrado | Risk |
|---|---|---|---|---|---|
| POST /pet | 10 | name, status | Content-Type | N/A | HIGH |
| GET /pet/findByStatus | 8 | (query) status | — | N/A | MEDIUM |
| GET /pet/{id} | 6 | (path) id | — | N/A | MEDIUM |

### 7.2 Risk map

`{ POST /pet: HIGH, GET /pet/findByStatus: MEDIUM, GET /pet/{id}: MEDIUM, DELETE /pet/{id}: HIGH }`

Reglas: HIGH eleva el `effective_minimum` calculado; CRITICAL agrega cobertura de cifrado obligatoria si la firma declara cifrado.

### 7.3 Conventions cliente (solo brownfield)

| Convention | Valor detectado | Fuente |
|---|---|---|
| Body_Mode | (n/a en greenfield) | — |
| Scenario_Prefix | (n/a en greenfield) | — |

En greenfield se aplican defaults del chapter (`Scenario:` literal, body en `request {...}` JSON inline).

### 7.4 Schemas de contrato

Listar schemas `-match.json` a generar (uno por schema respuesta):

- `pet-match.json` ← `Pet` schema del spec
- `order-match.json` ← `Order` schema
- `user-match.json` ← `User` schema

Notación: `#type` para required, `##type` para optional. Sin `##[] #type`.

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar features. Cambios posteriores requieren actualizar este documento y re-aprobar.
