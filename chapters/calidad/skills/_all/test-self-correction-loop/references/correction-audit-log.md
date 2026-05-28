# Correction Audit Log

Toda corrección aplicada por el loop debe registrarse en el audit log. Sin entrada en el log, la corrección es inválida y debe revertirse. El log es parte de la **evidencia auditable** del entregable del chapter (ver `[[calidad-test-evidence-and-traceability]]`).

## Formato canónico (JSON)

Una entrada por iteración del loop, por test.

```json
{
  "loop_run_id": "uuid",
  "test_id": "users.spec.ts::create user",
  "iteration": 1,
  "timestamp": "2026-05-27T14:32:11.482Z",
  "framework": "playwright",
  "mode": "full",
  "client": { "id": "acme-corp", "regulated": false },
  "trigger": {
    "failure_classification": "flaky + locator_stale",
    "classification_source": "calidad-failure-triage-and-classification",
    "evidence": [
      "evidence/loop-uuid/iter-0/trace.zip",
      "evidence/loop-uuid/iter-0/screenshot-login.png",
      "evidence/loop-uuid/iter-0/dom-snapshot.html"
    ]
  },
  "change": {
    "file": "pages/UsersPage.ts",
    "lines_changed": [42, 43],
    "diff_unified": "@@ -42,2 +42,2 @@\n-  emailInput = this.page.getByLabel('Email');\n+  emailInput = this.page.getByRole('textbox', { name: /Email|Correo/i });",
    "before": "  emailInput = this.page.getByLabel('Email');",
    "after": "  emailInput = this.page.getByRole('textbox', { name: /Email|Correo/i });",
    "justification": "Selector primary getByLabel('Email') no resolvía tras release de i18n. Healing fallback getByRole + name regex resolvió en el live app. DOM snapshot adjunto muestra label='Correo' en español.",
    "release_notes_link": "https://repo/releases/v2.3.0",
    "guardrails_checked": [
      "NO_ASSERTION_CHANGE",
      "NO_THRESHOLD_LOOSENING",
      "NO_SECURITY_TAG_TOUCH",
      "NO_FIXTURE_DEGRADATION",
      "NO_TEST_DATA_SIMPLIFICATION",
      "NO_AUTH_BYPASS",
      "NO_COMMAND_FILTERING",
      "NO_FRAMEWORK_DOWNGRADE",
      "NO_TEST_DELETION",
      "NO_SKIP_WITHOUT_TICKET"
    ],
    "guardrails_passed": true,
    "guardrails_violated": []
  },
  "result": {
    "rerun_status": "passed",
    "rerun_iteration": 2,
    "rerun_evidence": ["evidence/loop-uuid/iter-1/trace.zip"],
    "outcome": "validated"
  },
  "sut_context": {
    "url": "https://staging.acme.com",
    "commit": "abc123def",
    "deployed_at": "2026-05-27T10:00:00Z",
    "environment": "staging"
  },
  "reverted": false,
  "revert_reason": null
}
```

## Casos especiales

### Entrada bloqueada por guardrail

```json
{
  "loop_run_id": "uuid",
  "test_id": "checkout.spec.ts::pay with card",
  "iteration": 1,
  "timestamp": "...",
  "trigger": { "failure_classification": "deterministic + assertion_mismatch", "...": "..." },
  "change": {
    "file": "tests/checkout.spec.ts",
    "diff_unified": "@@ -88 +88 @@\n-  await expect(response.status()).toBe(200);\n+  await expect(response.status()).toBeLessThan(500);",
    "justification": "(propuesta del agente)",
    "guardrails_checked": ["NO_ASSERTION_CHANGE", "NO_CHECK_REMOVAL", "NO_MATCHER_LOOSENING"],
    "guardrails_passed": false,
    "guardrails_violated": ["NO_MATCHER_LOOSENING", "NO_ASSERTION_CHANGE"]
  },
  "result": {
    "outcome": "blocked_by_guardrail",
    "applied": false
  }
}
```

### Entrada en modo `dry-run` (propuesta sin aplicar)

```json
{
  "...": "...",
  "mode": "dry-run",
  "change": { "...": "..." },
  "result": {
    "outcome": "proposed_pending_human_approval",
    "applied": false,
    "patch_file": "evidence/loop-uuid/iter-0/proposed.patch"
  }
}
```

### Entrada de reversión

```json
{
  "loop_run_id": "uuid",
  "test_id": "users.spec.ts::create user",
  "iteration": 3,
  "timestamp": "...",
  "action": "revert",
  "reason": "strict_mode_escalation",
  "reverted_iterations": [1, 2, 3],
  "result": { "outcome": "workspace_restored_to_pristine" }
}
```

## Campos obligatorios

| Campo | Obligatorio | Notas |
|---|---|---|
| `loop_run_id` | sí | UUID v4. Une todas las entradas del mismo loop. |
| `test_id` | sí | Convención `path::test_name`. |
| `iteration` | sí | 0..max_iterations. |
| `timestamp` | sí | ISO 8601 UTC. |
| `trigger.failure_classification` | sí | Output del triage. |
| `trigger.evidence` | sí | Paths absolutos o relativos a la raíz de evidence storage. Mínimo 1 elemento. |
| `change.file` | sí (si aplica) | Omitir si `outcome: blocked_by_guardrail` previo al cambio. |
| `change.diff_unified` | sí | Formato unified diff estándar. |
| `change.justification` | sí | Texto en prosa, mínimo 1 frase. |
| `change.guardrails_checked` | sí | Lista completa de reglas evaluadas. |
| `change.guardrails_passed` | sí | Booleano. |
| `result.outcome` | sí | Enum: `validated` \| `failed_continued` \| `escalated` \| `blocked_by_guardrail` \| `proposed_pending_human_approval` \| `workspace_restored_to_pristine`. |
| `sut_context.commit` | sí | Hash del SUT en el momento del run. |

## Persistencia

- Almacenamiento junto con evidence (ver `[[calidad-test-evidence-and-traceability]]`).
- Formato preferido: JSONL (`audit-log.jsonl`), una entrada por línea, append-only.
- Ruta sugerida: `<evidence-root>/<loop_run_id>/audit-log.jsonl`.
- Inmutable una vez escrita; correcciones se anotan con entradas adicionales (`action: revert`, `action: amend`), nunca borrando entradas previas.

## Retención

- Clientes no regulados: alineado con la política de retención de evidencia del cliente (default 90 días).
- Clientes regulados: ver `regulated-client-overrides.md` (mínimo 7 años para HIPAA, SOX, PCI-DSS Level 1).

## Auditoría

El audit log debe ser legible por:

- Humano del chapter (revisión técnica).
- Auditor del cliente (compliance).
- Otros agentes del chapter (input para `[[calidad-failure-triage-and-classification]]` en patrones repetidos).

Cualquier ausencia o inconsistencia en el log invalida la corrección y obliga a reversión.
