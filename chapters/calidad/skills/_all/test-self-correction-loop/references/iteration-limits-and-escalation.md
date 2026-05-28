# Iteration Limits and Escalation

Límites duros del loop y formato canónico del escalation report cuando el agente debe entregar el control al humano.

## Límites

| Límite | Default | Justificación |
|---|---|---|
| `max_iterations` por loop | 3 | Tres intentos consecutivos sin éxito son señal de problema más profundo. |
| Recurrencia semanal por test | 2 | Si el mismo test entra al loop más de 2 veces en una semana, marcarlo como "rebelde" y escalar — la auto-corrección no está resolviendo la causa raíz. |
| Tiempo total del loop por test | 10 minutos | Más allá de eso, el costo en pipeline supera el beneficio; escalar. |
| Tokens LLM consumidos por loop | tope configurable | Cuando el repair requiere LLM (regeneración de selector, parseo de error), aplicar cap de costo. Default sugerido: 50K tokens por loop. |
| Suite máximo re-ejecutado por iteración | el test fallido y dependencias directas | Re-ejecutar el suite completo en cada iteración es ruido caro; reducir el blast radius. |

## Cuándo escalar a humano (escalation triggers)

El loop transiciona a `ESCALATED` automáticamente si **alguna** condición se cumple:

1. `iteration >= max_iterations` sin éxito.
2. Cualquier regla de `anti-cheating-guardrails.md` se activó en `DIAGNOSING`.
3. Cliente clasificado como regulado y modo es `dry-run` → escalation obligatoria por cada propuesta (no aplicar nada en automático).
4. `[[calidad-failure-triage-and-classification]]` no encuentra match en `failure-pattern-catalog.md`.
5. El loop entra en oscilación: fix A causa fallo B; fix B causa que regrese fallo A. Detección: dos diffs de iteraciones consecutivas se anulan entre sí.
6. Recurrencia semanal del mismo test supera 2 entradas al loop.
7. Tiempo o tokens consumidos exceden los caps.
8. SUT inestable detectado durante el loop (≥1 fallo de infraestructura en los re-runs). Pasa a `[[calidad-failure-triage-and-classification]]` como `environment` y se escala.

## Formato del escalation report

El report es JSON estructurado, persistido junto a la evidencia, **y** un resumen humano en markdown para el handover.

### JSON canónico

```json
{
  "loop_run_id": "uuid",
  "test_id": "users.spec.ts::create user",
  "framework": "playwright",
  "client": { "id": "...", "regulated": false },
  "mode": "full",
  "iterations_attempted": 3,
  "iterations_max": 3,
  "final_state": "ESCALATED",
  "trigger": "max_iterations_reached",
  "changes_attempted": [
    { "iteration": 1, "summary": "ajustar timeout 5s→10s", "outcome": "failed_other_tests", "reverted": true },
    { "iteration": 2, "summary": "cambiar selector getByLabel→getByRole", "outcome": "did_not_resolve", "reverted": true },
    { "iteration": 3, "summary": "actualizar expected text 'Welcome'→'Bienvenido'", "outcome": "broke_other_tests_consistency", "reverted": true }
  ],
  "evidence": [
    "evidence/run-id/trace-i1.zip",
    "evidence/run-id/trace-i2.zip",
    "evidence/run-id/trace-i3.zip",
    "evidence/run-id/screenshots/login-fail.png"
  ],
  "agent_hypothesis": "Posible bug del SUT en POST /users (response shape cambió).",
  "recommended_action": "Revisión humana del endpoint /users. Abrir ticket en backend del cliente.",
  "sut_context": { "url": "...", "commit": "abc123", "deployed_at": "2026-05-27T10:00:00Z" }
}
```

### Resumen humano (markdown del handover)

```
Test: users.spec.ts::create user
Iteraciones: 3/3
Último estado: FAILED
Razón: assertion mismatch persistente después de 3 intentos.

Cambios intentados (revertidos):
  - i1: ajustar timeout 5s→10s (causó timeout en otros tests).
  - i2: cambiar selector getByLabel→getByRole (no resolvió).
  - i3: actualizar expected text "Welcome"→"Bienvenido" (otro test falló por consistencia).

Evidencia:
  - traces: evidence/run-id/trace-i{1,2,3}.zip
  - screenshots: evidence/run-id/screenshots/login-fail.png

Hipótesis del agente: posible bug del SUT en el endpoint POST /users.
Acción solicitada: revisión humana del SUT.

Sin cambios persistidos en el repositorio (todos revertidos por exceder max_iterations en modo estricto).
```

## Reversión en modo estricto

Cuando el cliente o el contrato exige modo estricto:

- Al alcanzar `ESCALATED`, revertir **todos** los cambios aplicados durante el loop (los `iteration > 0`) usando los snapshots del audit log.
- Garantizar que el workspace queda en el estado previo a `PRISTINE → EXECUTED` del loop.
- Registrar la reversión en el audit log con `action: revert`, `reason: strict_mode_escalation`.

En modo no estricto (default no regulado), los cambios revertidos quedan disponibles como branch local para que el humano los inspeccione, pero no se persisten al branch principal.
