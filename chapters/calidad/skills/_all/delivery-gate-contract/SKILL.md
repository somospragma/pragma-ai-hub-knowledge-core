---
id: calidad-delivery-gate-contract
version: 1.4.0
scope: chapter
type: skill
chapter: calidad
enforcement: mandatory
description: "Contrato YAML que el agente DEBE emitir literalmente al final de toda generación, antes del mensaje de cierre. Sin este bloque, la entrega se considera incompleta. Universal a los 5 IDEs."
tags: [delivery-gate, contract, mandatory, universal, all-ides]
---

# Delivery Gate Contract — Bloque YAML de Cierre Obligatorio

## Cuándo aplicar

Siempre, al final de todo workflow de generación (greenfield o brownfield, los 4 frameworks). Es lo último que el agente emite antes del mensaje "listo".

Aplica universalmente a los 5 IDEs soportados (Kiro, Claude Code, GitHub Copilot, Amazon Q IDE, Amazon Q CLI). Sin este bloque, la entrega se considera incompleta.

## Precondición: la traza manda

**Antes de emitir el bloque, leer `.evidence/pipeline-state.json` (`[[calidad-pipeline-state-tracking]]`) y verificar que ninguna fase obligatoria está en `pending` o `in_progress`.** Si las hay:

- NO se emite el gate como cierre. Se emite un **reporte de estado** que enumera las fases pendientes y la siguiente acción, y el trabajo continúa.
- Un gate emitido sobre fases pendientes es una entrega falsa, aunque todos sus campos estén rellenos. Verificado en campo: dos gates emitidos en la misma corrida, el primero sin ninguna ejecución y el segundo con `status: success` mientras 3 de 4 escenarios estaban `SKIPPED`.

Reglas de coherencia que el propio agente debe verificar antes de emitir:

| Si… | Entonces… |
|---|---|
| `mode: full` | `suite_executed` y `report_verified` en `done`; `execution.*` con datos reales |
| `status: success` | cero fases obligatorias pendientes, cero `blockers`, y `execution.skipped` coherente con lo realmente ejecutado |
| hay escenarios `SKIPPED` por filtro | NO pueden contarse como `coverage.delivered` |
| `blockers[]` no vacío | cada blocker con **evidencia del sondeo** que lo comprobó (comando + salida), no una afirmación |
| `execution_target: mock` | tráfico verificado contra el mock (ver `mock_evidence.traffic_verified`) |

## Instrucción

Emite literalmente este bloque YAML (rellenando los slots) antes de cualquier despedida:

```yaml
delivery_gate:
  schema_version: "1.1"
  pipeline_state: ".evidence/pipeline-state.json"   # traza leída; cero fases obligatorias pendientes
  phases_pending: []                                # si no está vacío, esto NO es un cierre
  framework: karate | playwright | k6 | appium
  mode: full | dry-run | scaffold-only | execute-only
  execution_target: real | mock | hybrid    # contra qué corrió la fase de ejecución (SUT readiness gate)
  certification: certified | pending_real_integration   # certified SOLO si execution_target: real
  mock_evidence:                            # null si execution_target: real
    tool: mockoon
    data_file: "mocks/mockoon/environment.json"
    faker_seed: 12345
    locator_map: "locator-map.json" | null  # solo front/mobile pre-desarrollo
    front_prototype: true | false           # opt-in: prototipo HTML del front (mocks/front-prototype/)
    app_prototype: true | false             # opt-in: prototipo de app en la tecnología real (mocks/app-prototype/)
    prototype_acceptance: ".evidence/prototype-acceptance.json"  # paridad + fidelidad + CA recorribles
    traffic_verified: true | false          # el SUT (app/front) consumió REALMENTE el mock: peticiones en su log
    switchover_plan: "STRATEGY.md#6"        # dónde quedó documentado el plan mock -> real
  preflight:
    tool_version: "11.0.21"           # Java/Node/k6/Gradle según stack
    verdict: pass | fail | skipped
    notes: "..."
  inputs_confirmed:
    project_name: "..."
    output_path: "..."
    ui_source_or_spec: "..."
    user_story: "HUT-001" | null
    firma: "..." | null
    risk_map: { addPet: HIGH, findPetsByStatus: MEDIUM, ... }
  transversal_capabilities:               # capas complementarias evaluadas (paso 2.5 del router)
    detected:
      - capability: accessibility | seo | security | visual | contract | performance
        skill: calidad-accessibility-testing
        tag: "@accessibility"
        rationale: "..."                  # por qué aplica (risk-first / SUT / sector)
        confirmed_by_user: true | false
    omitted:
      - capability: seo
        reason: "..."                     # por qué no aplica / fuera de alcance / descartada
  coverage:
    declared:
      addPet: 10        # effective_minimum por endpoint/HU/script
      findPetsByStatus: 8
    delivered:
      addPet: 10
      findPetsByStatus: 8
    diff_ok: true
  files_emitted:
    total: 28
    paths:
      - "src/test/java/com/testing/features/pet/addPet.feature  [ok]"
      - "..."
  coherence_checks:
    structure_canonical: pass | fail
    no_dead_code: pass | fail
    compile_dry_run: pass | fail | skipped
    notes: "..."
  execution:
    run_command: "mvn test -f pom.xml"
    exit_code: 0
    total: 28
    passed: 28
    failed: 0
    skipped: 0
    rerun_N3_applied: true | false | not_applicable
    deterministic_failures: 0
    flaky_failures: 0
    smoke_1_1:                          # SOLO K6 — gate obligatorio en modo full
      executed: true | false | skipped
      exit_code: 0                      # int (0 = ok); null si executed=false|skipped
  corrections_applied:
    count: 0
    audit_log: ".evidence/audit-log-20260604.md"
    anti_cheating_violations: 0
  evidence_persisted:
    session_config: ".evidence/session-config.json"
    generation_manifest: ".evidence/generation-manifest.json"
    execution_log: ".evidence/execution-log-20260604.json" | null
    audit_log: ".evidence/audit-log-20260604.md" | null
    coverage_audit: ".evidence/coverage-declared-vs-delivered.json"
    executive_report: ".evidence/report-{ISO}.html" | null   # null si modo scaffold-only/dry-run
  status: success | partial | failed
  blockers: []                          # lista de razones si status != success
  next_steps: []                        # acciones recomendadas al usuario
```

## Restricciones

- Si falta cualquier campo obligatorio → entrega inválida.
- Si `status: success` pero `execution.exit_code != 0` → contradicción, reportar `failed`.
- Si modo es `dry-run` o `scaffold-only` → `execution.*` puede ser `null` pero documentar en `blockers` por qué.
- Si modo es `full` y no se ejecutó → `status: partial` con `blocker: "execution_skipped"`.
- `transversal_capabilities` debe estar presente: si no aplica ninguna capa, declarar `detected: []` y justificar en `omitted`. Una capa con `confirmed_by_user: false` no debe haberse tejido en la suite.
- Si `execution_target: mock | hybrid` → `certification: pending_real_integration` es obligatorio, `mock_evidence` completo, y `next_steps` DEBE incluir la re-ejecución contra integraciones reales (switchover). `certification: certified` con `execution_target != real` es contradicción → entrega inválida.
- Resultados contra mock JAMÁS se presentan como certificación de integración, performance o seguridad del SUT (regla maestra de `[[calidad-sut-readiness-gate]]`).
- **Advertencia de cierre obligatoria**: si `execution_target: mock | hybrid`, el mensaje final al usuario (el que sigue al bloque YAML) DEBE repetir en su primera línea: *"Resultados obtenidos contra mock: validan la construcción de la suite, NO certifican el SUT. Certificación pendiente de re-ejecución contra integraciones reales (ver plan de switchover)."* Decirlo solo al inicio del flujo no basta — el usuario que lee el cierre debe verla ahí (hallazgo de pruebas de campo).

## Verification

```yaml
verification:
  - check: "bloque delivery_gate emitido literalmente como último contenido antes del mensaje de cierre"
    failure_message: "Bloqueado: la entrega no incluye el bloque YAML delivery_gate. Sin este contrato la entrega es inválida."
  - check: "todos los campos obligatorios del schema rellenados (schema_version, framework, mode, status, inputs_confirmed, coverage, files_emitted, evidence_persisted)"
    failure_message: "Bloqueado: el bloque delivery_gate tiene campos obligatorios vacíos o ausentes."
  - check: "consistencia status vs execution.exit_code (success requiere exit_code 0 en modo full)"
    failure_message: "Bloqueado: contradicción entre status declarado y exit_code reportado."
  - check: "modo full sin ejecución real reporta status: partial con blocker execution_skipped"
    failure_message: "Bloqueado: no se puede declarar success en modo full sin evidencia de ejecución."
  - check: "bloque transversal_capabilities presente (detected/omitted); capas tejidas solo si confirmed_by_user"
    failure_message: "Bloqueado: faltó evaluar/registrar las capacidades transversales complementarias (accesibilidad, SEO, seguridad, visual, contract, performance)."
  - check: "execution_target declarado; si es mock o hybrid, certification: pending_real_integration + mock_evidence completo + switchover en next_steps"
    failure_message: "Bloqueado: la corrida contra mock no declara la certificación pendiente o carece de evidencia del mock y plan de switchover."
  - check: "si execution_target es mock o hybrid, el mensaje de cierre posterior al bloque YAML repite la advertencia de certificación pendiente"
    failure_message: "Bloqueado: el cierre no advierte que los resultados contra mock no certifican el SUT. La advertencia al inicio del flujo no sustituye la del cierre."
  - check: "pipeline-state.json leído y sin fases obligatorias pendientes; phases_pending vacío"
    failure_message: "Bloqueado: hay fases del pipeline sin completar. Emitir el gate ahora sería declarar terminada una entrega incompleta."
  - check: "cada blocker declarado incluye la evidencia del sondeo (comando ejecutado + salida) que lo comprueba"
    failure_message: "Bloqueado: hay blockers afirmados sin sondear. Un bloqueo de ambiente supuesto ya cerró una entrega en falso."
  - check: "si execution_target es mock/hybrid, mock_evidence.traffic_verified es true con evidencia del log del mock"
    failure_message: "Bloqueado: no se demostró que el SUT consumiera el mock. Una suite verde contra un SUT que ignora el mock no valida el contrato."
```

## Cross-links

`[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-executive-report-generator]]`, `[[calidad-generate-executive-report]]`.
