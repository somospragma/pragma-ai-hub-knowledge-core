# STRATEGY.md — {{project_name}} (K6)

Documento de estrategia previo a la generación de scripts. Debe estar aprobado explícitamente por el usuario antes de emitir el primer `.js` de test. Ver `[[calidad-pre-design-strategy-document]]`.

## 1. Contexto

- SUT: {{sut_name}} — {{sut_description}}
- Tipo de SUT: API REST / GraphQL — completar
- Equipo: {{team_name}}
- Stakeholders consultables: {{stakeholders}} (Dev, Infra, QA lead, PO, capacity planner si aplica)
- Stack tecnológico del SUT: {{sut_stack}}
- Tipo de relación: greenfield (proyecto K6 nuevo)
- Spec: {{spec_path}} ({{spec_format}})
- `base_url`: {{base_url}}
- Firma (perfil del sistema): {{firma}} — derivar tier inicial (mission-critical → Conservative; business-as-usual → Moderate; internal → Relaxed)
- `auth_mode`: {{auth_mode}} (`spec` default / `external`)

## 2. Volumen y SLAs

Sección crítica para K6 — alimenta `options.thresholds` de cada escenario.

| SLA | Valor declarado | Notas |
|---|---|---|
| Usuarios concurrentes sostenido | {{concurrent_users_sustained}} | base para `carga` |
| Usuarios concurrentes peak | {{concurrent_users_peak}} | base para `estres` |
| Peak QPS | {{peak_qps}} | si aplica executor `ramping-arrival-rate` |
| p50 latencia | < {{p50_ms}} ms | global o por endpoint |
| p95 latencia | < {{p95_ms}} ms | global o por endpoint |
| p99 latencia | < {{p99_ms}} ms | opcional |
| Error rate máximo | < {{error_rate_pct}}% | `http_req_failed` |
| Disponibilidad objetivo | >= {{availability_pct}}% | (1 - error_rate) * 100 |
| Ventana de mantenimiento | {{maintenance_window}} | requerida para `carga`, `estres`, `spike`, `soak` |

## 3. Alcance funcional

- Endpoints en scope: {{endpoints_in_scope}}
- Endpoints fuera de scope: {{endpoints_out_of_scope}} ({{out_of_scope_reason}})
- CRUD flows detectados: {{crud_flows}}
- Endpoint objetivo principal vs auxiliares: {{primary_vs_auxiliary}}

## 4. Dependencias externas

- Auth: `auth_mode = {{auth_mode}}`. Si `external`, declarar env var `AUTH_TOKEN` obligatoria en README.
- Endpoint de obtención de token (si aplica `setup()` o `per-vu`): {{auth_endpoint}}
- Refresh policy: {{auth_refresh_strategy}} (setup única / per-vu / refresh on 401)
- Bases de datos: {{database_dependencies}}
- Servicios externos consumidos por el SUT durante la carga: {{external_services}}

## 5. Riesgos conocidos

- WAF en ambiente de prueba: {{waf_status}} — proveedor: {{waf_provider}}. **Allowlist coordinada con Infra es prerrequisito para ejecutar `carga`, `estres`, `spike`, `soak`** (de lo contrario los fallos serán `ENVIRONMENT_BLOCKED`, no SUT_BUG).
- Rate limits documentados: {{rate_limits}}
- Ambiente compartido vs dedicado: {{environment_isolation}}
- Restricciones regulatorias (HIPAA/SOX/PCI/FedRAMP): {{regulatory_constraints}} (modo default `dry-run` si aplica)
- Costo de carga (si SUT cobra por request a terceros): {{cost_per_run}}

## 6. Próximos pasos

- Archivos a generar: 3 obligatorios + opt-in (ver 7.1) + `utils.js`, `config.js`, `package.json`, `run-all.sh`, `README.md`.
- Comando smoke (gate del loop): `k6 run -e BASE_URL=$BASE_URL tests/smoke-test.js` con 1 VU y 1 iteración.
- Comando suite completa: `run-all.sh` orquesta `linea-base → carga → estres`.
- Reporte ejecutivo: formato {{report_format}} (default `html`) con sección K6 (latencias, error rate, disponibilidad, comparación corrida-a-corrida).

## 7. Estrategia K6

### 7.1 Escenarios

Los 3 escenarios obligatorios siempre se generan. `spike` y `soak` son opt-in con justificación.

| Escenario | Obligatorio | Workload (% sostenido) | VUs / arrival rate | Duración | Executor | Justificación opt-in |
|---|---|---|---|---|---|---|
| linea-base (smoke) | sí | 20-30% del sostenido | {{baseline_vus}} | {{baseline_duration}} | `ramping-vus` | — |
| carga (load) | sí | 100% del sostenido | {{load_vus}} | {{load_duration}} | `ramping-vus` o `ramping-arrival-rate` | — |
| estres (stress) | sí | 200-300% del sostenido | {{stress_vus}} | {{stress_duration}} | `ramping-vus` | — |
| spike | no | picos cortos N× sostenido | {{spike_vus}} | {{spike_duration}} | `ramping-arrival-rate` | {{spike_reason}} |
| soak | no | sostenido prolongado | {{soak_vus}} | {{soak_duration}} (1-8 h) | `constant-vus` | {{soak_reason}} |

### 7.2 Tier de thresholds elegido

- Tier: {{thresholds_tier}} (Conservative / Moderate / Relaxed)
- Justificación: {{tier_reason}} (deriva de `user_story.SLA` → `firma.SLA` → default Moderate)
- Aplicar `[[k6-thresholds-three-tiers]]` para los valores numéricos exactos por tier.

### 7.3 Auth strategy

- `auth_mode`: {{auth_mode}}
- Modo de adquisición del token: {{token_acquisition}} (setup única en `setup()` / refresh en handler / per-vu)
- Env vars necesarias: `BASE_URL`{{auth_env_vars_extra}}

### 7.4 Data correlation y CRUD

- Flows CRUD detectados (full / partial): {{crud_detail}}
- IDs dinámicos: aplicar `[[k6-crud-dynamic-id-correlation]]` con guard clause.
- Payload builders en `utils.js` (`buildXxxBody`).

### 7.5 Bloqueos esperados de ambiente

Si se prevé que carga / estres dispare WAF, rate limit, o agote DB, declararlo aquí ANTES de correr para que los fallos no se clasifiquen erróneamente como `SUT_BUG` en el reporte ejecutivo:

- {{expected_environment_blockers}}

## Aprobación

Estado: __PENDIENTE DE APROBACIÓN__

Al recibir "aprobado" del usuario, este documento queda congelado y el agente procede a generar scripts K6.
