---
id: calidad-test-self-correction-loop
version: 1.2.0
scope: chapter
type: skill
chapter: calidad
description: "Loop de auto-corrección de tests: ejecutar → triage → decidir si es test design issue → proponer fix → re-ejecutar → validar. Incluye guardrails anti-cheating estrictos para NO modificar tests que esconden bugs reales del SUT."
tags: [self-correction, loop, auto-fix, anti-cheating, guardrails, diff-aware, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "max 3 iteraciones respetadas; tras la tercera sin éxito, escalado a humano con reporte"
    failure_message: "Bloqueado: el loop superó 3 iteraciones sin escalar. Más iteraciones esconden bugs reales del SUT."
  - check: "no se modificó assertion de contrato, security ni compliance (anti-cheating estricto)"
    failure_message: "Bloqueado: se detectó modificación de assertion de contrato/security/compliance — violación de anti-cheating."
  - check: "audit log persistido en .evidence/audit-log-<fecha>.md con diff por iteración y guardrail verificado"
    failure_message: "Bloqueado: no hay audit log de las correcciones; sin trazabilidad la auto-corrección es inválida."
  - check: "input de triage presente y clasificación distinta a bug del SUT antes de activar el loop"
    failure_message: "Bloqueado: el loop se activó sin triage previo o sobre fallos clasificados como bug del SUT."
  - check: "cada iteración de corrección re-ejecutó SOLO el test corregido (aislado); la suite completa se corrió una vez al inicio para inventariar fallos y una vez al final como regresión"
    failure_message: "Bloqueado: se relanzó la suite completa dentro del ciclo de corrección. Cada iteración debe aislar el test que se está corrigiendo."
---

# Test Self-Correction Loop — Auto-corrección Controlada con Guardrails Anti-Cheating

## Cuándo aplicar

Aplica este skill **únicamente después** de que `[[calidad-failure-triage-and-classification]]` haya clasificado el fallo como:

- `deterministic + test design issue`, o
- `flaky` con causa auto-corregible (locator stale, timing/sync ajustable, fixture data state recuperable).

**NUNCA** aplicar sobre fallos clasificados como `deterministic + bug del SUT`, `deterministic + breaking change`, ni cuando el triage no pudo concluir. En esos casos el control pasa al humano y al equipo del cliente vía `[[calidad-failure-triage-and-classification]]`.

Este skill es invocado como **fase final obligatoria** del workflow `[[calidad-test-self-correction-loop]]`, que a su vez es la cola común de todos los workflows de construcción de tests del chapter (Karate, Playwright, K6, Appium, greenfield y brownfield).

Cruzar siempre con `[[calidad-chapter-perspective]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-security-testing]]` y `[[calidad-cicd-integration]]`.

## Cadencia de ejecución: aislar para corregir, suite para confirmar

El ciclo completo, en este orden y sin atajos:

| # | Momento | Qué se ejecuta | Por qué |
|---|---|---|---|
| 1 | Gate 1:1 | **Un** escenario crítico (`@smoke-gate`) | Destapa los problemas transversales con un solo diagnóstico (`[[calidad-smoke-gate-policy]]`) |
| 2 | Inventario | **Suite completa, una vez** | Saber TODOS los fallos que hay, no descubrirlos de a uno |
| 3 | Agrupar | (sin ejecutar) | Varios fallos suelen compartir causa raíz: se agrupan y se corrige la causa, no cada síntoma |
| 4 | Corrección | **SOLO el test que se está corrigiendo**, aislado, en cada iteración | Es la regla de este skill (ver abajo) |
| 5 | Regresión | **Suite completa, una vez más** | Confirmar que las correcciones no rompieron nada |

**Regla dura del paso 4**: mientras se corrige un test, cada re-ejecución corre **ese test y nada más** (por nombre/tag: `-Dcucumber.filter.tags=@TC-207`, `--grep "nombre exacto"`, `-Dtest=...`, `--tests`). Relanzar la suite completa en cada iteración está prohibido: multiplica el tiempo, mezcla el resultado del cambio con ruido de otros fallos y hace imposible atribuir la mejora — verificado en campo, donde el usuario tuvo que pedirlo tres veces ("no ejecutes tantos test hasta no confirmar el primero exitoso, siempre reejecuta solo el que intentas corregir").

Corolarios:

- **Un fallo a la vez.** Si el inventario dio 5 fallos, se toma uno, se aísla, se corrige y se cierra antes de pasar al siguiente. Corregir cinco en paralelo y relanzar todo impide saber qué arregló qué (es la misma lógica de "una variable por iteración").
- **Si el fallo aislado sigue rojo tras 3 iteraciones**, escala — no se lanza la suite "a ver si con otros datos pasa".
- **La suite completa nunca es una herramienta de diagnóstico**: es inventario (paso 2) o confirmación (paso 5).

## Modos de operación

Hereda los modos definidos en `[[calidad-test-execution-orchestration]]`:

| Modo | Comportamiento en el loop |
|---|---|
| `full` | Aplica correcciones automáticamente, hasta `max_iterations` (default 3). Logea cada cambio en `references/correction-audit-log.md`. |
| `dry-run` | Propone el diff, valida guardrails, **NO aplica** nada. Entrega patch + justificación + evidencia y espera aprobación humana. |
| `scaffold-only` | Este skill **NO aplica**: no hay ejecución previa, por tanto no hay nada que corregir. |
| `execute-only` | Este skill **NO aplica**: no se modifican tests existentes bajo este modo. |

**Default por perfil de cliente**:

- Clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP, GDPR-bajo-DPIA): `dry-run` obligatorio.
- Resto: `full`.

Si el cliente exige explícitamente "no AI modifications to tests", forzar `dry-run` aunque sea modo `full` por contrato técnico. Ver `references/regulated-client-overrides.md`.

## Instrucción

El skill implementa una **state machine** estricta. Cada transición exige verificación; saltarse cualquier estado anula la corrección.

```
PRISTINE → generar tests (delegado a los workflows de framework)
   ↓
EXECUTED → invocar [[calidad-test-execution-orchestration]]
   ↓
   ¿hubo fallos?
     NO → VALIDATED, salir.
     SÍ ↓
FAILED → invocar [[calidad-failure-triage-and-classification]] por cada fallo
   ↓
   ¿classification permite auto-corrección?
     NO → ESCALATED, reportar a humano con todo el contexto, salir.
     SÍ ↓
DIAGNOSING → identificar el cambio mínimo necesario
             (ver references/diff-aware-repair-rules.md)
   ↓
   ¿el cambio cumple anti-cheating guardrails?
   (ver references/anti-cheating-guardrails.md)
     NO → ESCALATED, salir.
     SÍ ↓
FIXING → aplicar cambio. Loguear en references/correction-audit-log.md.
   ↓
RE-EXECUTING → invocar ejecución de nuevo
   ↓
   ¿pasó?
     SÍ → VALIDATED (con `correction_count` registrado en evidencia).
     NO ↓
        ¿iteration < max_iterations (default 3)?
          SÍ → volver a FAILED.
          NO → ESCALATED. En modo estricto, revertir todos los cambios del loop.
```

El detalle completo del state machine — semántica de cada estado, side effects, ejemplos end-to-end — está en `references/correction-loop-state-machine.md`.

## Restricciones

Estas son las restricciones más críticas del chapter; cada una está justificada en `references/anti-cheating-guardrails.md`. Su violación invalida la entrega.

1. **NUNCA modificar un test para hacerlo pasar cuando el SUT está roto**. Es el antipatrón maestro del chapter. Si el SUT no cumple su contrato, es bug — reportar vía `[[calidad-failure-triage-and-classification]]`, no curar.
2. **NUNCA aflojar assertions, thresholds o severidad** (matchers, tolerancias, error rates) sin justificación documentada y aprobación humana explícita.
3. **NUNCA modificar tests etiquetados `@security`, `@contract`, `@compliance`, `@regulatory`**. Esos suites deben fallar deterministícamente; si fallan, es bug, no test.
4. **NUNCA exceder `max_iterations`** (default 3). Tres intentos sin éxito son señal de problema más profundo que requiere ojo humano.
5. **Cada modificación aplicada debe quedar registrada en audit log** (`references/correction-audit-log.md`) con: archivo, líneas cambiadas, diff antes/después, razón, hash del SUT, evidencia que justificó el cambio, guardrails verificados. Sin audit log, el cambio es inválido y se revierte.
6. **En `dry-run`, NO aplicar nada**: producir patch propuesto + justificación + evidencia para aprobación humana. Aplicar en `dry-run` rompe el contrato con clientes regulados.
7. **Cliente regulado → modo obligatorio `dry-run`**. Default no negociable para HIPAA, SOX, PCI-DSS Level 1, FedRAMP y cualquier sector regulado equivalente. Ver `references/regulated-client-overrides.md`.
8. **Cross-link mandatorio con `[[calidad-failure-triage-and-classification]]`** (input obligatorio del loop) y `[[calidad-test-self-healing]]` (healing es un tipo específico de auto-corrección que opera dentro de este mismo loop). Sin estos cruces el skill está incompleto.

## Cross-links

- `references/correction-loop-state-machine.md` — diagrama y semántica completa del state machine.
- `references/anti-cheating-guardrails.md` — **crítico**. Reglas duras anti-cheating con detección automática.
- `references/diff-aware-repair-rules.md` — tabla de diferencias expected/actual y acción permitida.
- `references/iteration-limits-and-escalation.md` — límites, escalation triggers y formato de report.
- `references/correction-audit-log.md` — formato JSON del audit log, persistencia y retención.
- `references/regulated-client-overrides.md` — reglas para HIPAA, SOX, PCI-DSS Level 1, FedRAMP.

Cross-links con otros assets del chapter:

- `[[calidad-chapter-perspective]]`
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-security-testing]]`
- `[[calidad-cicd-integration]]`
- `[[calidad-test-execution-orchestration]]`
- `[[calidad-failure-triage-and-classification]]`
- `[[calidad-test-self-healing]]`
- `[[calidad-karate-greenfield]]`
- `[[calidad-playwright-greenfield]]`
- `[[calidad-k6-greenfield]]`
- `[[calidad-appium-screenplay-android]]`
- `[[calidad-test-self-correction-loop-workflow]]` (workflow)
