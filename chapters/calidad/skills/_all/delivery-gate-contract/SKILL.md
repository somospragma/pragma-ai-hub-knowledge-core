---
id: calidad-delivery-gate-contract
version: 1.0.0
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

## Instrucción

Emite literalmente este bloque YAML (rellenando los slots) antes de cualquier despedida:

```yaml
delivery_gate:
  schema_version: "1.0"
  framework: karate | playwright | k6 | appium
  mode: full | dry-run | scaffold-only | execute-only
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
```

## Cross-links

`[[calidad-pre-generation-protocol]]`, `[[calidad-post-generation-protocol]]`, `[[calidad-test-execution-orchestration]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-executive-report-generator]]`, `[[generate-executive-report]]`.
