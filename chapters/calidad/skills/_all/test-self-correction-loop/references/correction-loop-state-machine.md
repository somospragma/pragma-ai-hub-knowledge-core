# Correction Loop State Machine

State machine canónica del self-correction loop. Cualquier corrección que no atraviese explícitamente estos estados se considera inválida y debe revertirse.

## Diagrama

```
                          ┌────────────┐
                          │  PRISTINE  │  tests recién generados / extendidos
                          └─────┬──────┘
                                │ invocar [[calidad-test-execution-orchestration]]
                                ▼
                          ┌────────────┐
                          │  EXECUTED  │  exit code + parseo a esquema común
                          └─────┬──────┘
                                │
                  ¿hubo fallos? │
            ┌───────────────────┴──────────────────┐
           NO                                     SÍ
            │                                      │
            ▼                                      ▼
      ┌───────────┐                          ┌────────┐
      │ VALIDATED │ ← salir, generar         │ FAILED │ invocar
      └───────────┘   evidencia              └────┬───┘ [[calidad-failure-triage-and-classification]]
                                                  │
                       ¿el triage permite        │
                          auto-corrección?       │
              ┌────────────────────────────────┴──────────────┐
             NO                                              SÍ
              │                                               │
              ▼                                               ▼
        ┌───────────┐                                  ┌────────────┐
        │ ESCALATED │ ← humano + report completo       │ DIAGNOSING │ identificar cambio
        └───────────┘                                  └────┬───────┘ mínimo necesario
                                                            │
                       ¿cumple anti-cheating               │
                            guardrails?                    │
              ┌────────────────────────────────────────────┴──────┐
             NO                                                  SÍ
              │                                                   │
              ▼                                                   ▼
        ┌───────────┐                                       ┌────────┐
        │ ESCALATED │                                       │ FIXING │ aplicar cambio
        └───────────┘                                       └────┬───┘ + audit log
                                                                 │
                                                                 ▼
                                                       ┌───────────────┐
                                                       │ RE-EXECUTING  │
                                                       └───────┬───────┘
                                                               │
                                  ¿pasó?                       │
                  ┌────────────────────────────────────────────┤
                 SÍ                                            NO
                  │                                             │
                  ▼                                             ▼
            ┌───────────┐                  ¿iteration < max_iterations?
            │ VALIDATED │                  ┌──────────┴─────────┐
            └───────────┘                 SÍ                   NO
                                          │                    │
                                          ▼                    ▼
                                    (volver a FAILED)    ┌───────────┐
                                                         │ ESCALATED │ + revertir
                                                         └───────────┘   en modo estricto
```

## Tabla de estados

| Estado | Semántica | Entradas válidas | Side effects |
|---|---|---|---|
| `PRISTINE` | Tests generados o extendidos por un workflow del chapter. Aún no ejecutados. | inicio del loop | — |
| `EXECUTED` | Ejecución completada. Resultado parseado en esquema común (`references/result-schema-common.md` del skill de orchestration). | desde `PRISTINE` o `RE-EXECUTING` | persiste evidencia (`[[calidad-test-evidence-and-traceability]]`) |
| `FAILED` | Hay >0 fallos. Triage invocado por cada fallo. | desde `EXECUTED` | escribe `triage_report.json` por fallo |
| `DIAGNOSING` | Identificación del cambio mínimo necesario, sobre el diff expected/actual y el catálogo `failure-pattern-catalog.md`. | desde `FAILED` (si el triage habilita auto-fix) | produce propuesta de cambio en memoria, aún no aplicada |
| `FIXING` | Cambio validado contra guardrails y aplicado. Audit log persistido. | desde `DIAGNOSING` (si guardrails pasan) | escribe en `correction-audit-log.md`; modifica archivos en el workspace |
| `RE-EXECUTING` | Re-ejecutar **SOLO el test que se está corrigiendo**, aislado por su identificador/tag. NUNCA la suite completa. | desde `FIXING` | nuevo bloque de evidencia con `iteration=N` |
| `REGRESSION` | Suite completa, **una sola vez**, cuando ya no quedan fallos abiertos: confirma que las correcciones no rompieron nada. | desde `VALIDATED` del último fallo | evidencia de la corrida completa final |
| `VALIDATED` | El test pasa. `correction_count` queda registrado en evidencia del run. | desde `EXECUTED` (sin fallos) o desde `RE-EXECUTING` (pasó) | reporte final `success` |
| `ESCALATED` | Imposible auto-corregir. Contexto completo entregado al humano. | desde `FAILED` (triage bloquea), `DIAGNOSING` (guardrails bloquean), `RE-EXECUTING` (max_iterations agotado) | escalation report (ver `iteration-limits-and-escalation.md`); en modo estricto, revertir cambios del loop |

## Transiciones prohibidas

- `RE-EXECUTING` lanzando la **suite completa** en cada iteración: prohibido. El aislamiento es la regla; la suite completa solo aparece en `REGRESSION`, al final.
- `PRISTINE → FIXING` (sin ejecutar previamente: ciego, prohibido).
- `EXECUTED → FIXING` (sin triage previo: viola el contrato anti-cheating).
- `FAILED → FIXING` (sin diagnóstico ni guardrails: ciego, prohibido).
- `DIAGNOSING → FIXING` cuando los guardrails se evaluaron pero alguna regla activó → debe ir a `ESCALATED`.
- `VALIDATED → FIXING` (no hay nada que corregir).

## Ejemplo end-to-end — iteración exitosa

```
1. PRISTINE         users.spec.ts generado por playwright-from-live-app.
2. EXECUTED         npx playwright test → 1 failed (locator stale en login).
3. FAILED           triage clasifica: flaky + locator_stale (i18n update detectado).
4. DIAGNOSING       diff-aware-repair-rules permite ajustar selector (regla "selector text change i18n").
5. FIXING           getByLabel('Email') → getByRole('textbox', { name: /Correo|Email/i }).
                    Audit log entry creado con: archivo, diff, evidencia (DOM snapshot), guardrails OK.
6. RE-EXECUTING     test pasa en run #2.
7. VALIDATED        reporte final: success, correction_count=1.
```

## Ejemplo end-to-end — escalación

```
1. PRISTINE         orders.spec.ts del cliente Banco-X (regulado HIPAA, modo dry-run).
2. EXECUTED         falla: POST /orders devuelve 500.
3. FAILED           triage clasifica: deterministic + bug del SUT (response cambió, no es contract drift).
4. ESCALATED        (no se intenta auto-corregir).
                    Escalation report entregado a humano con: evidencia (request/response/trace),
                    hipótesis (bug del SUT), recomendación (abrir ticket en backend del cliente).
                    Cero cambios aplicados a tests.
```
