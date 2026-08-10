---
id: calidad-pipeline-state-tracking
version: 1.0.0
scope: chapter
type: skill
chapter: calidad
description: "Traza viva del pipeline en .evidence/pipeline-state.json: qué fase está hecha, cuál falta y con qué evidencia. Se escribe tras cada fase y se lee al abrir CUALQUIER sesión, para que el proceso sobreviva a los cortes de contexto y ninguna entrega se declare terminada sin cumplir sus fases."
tags: [pipeline, state, traceability, session-continuity, mandatory, gate, universal]
enforcement: mandatory
verification:
  - check: "al iniciar cualquier sesión sobre un output_path existente, se leyó .evidence/pipeline-state.json y se reportó al usuario dónde quedó el proceso"
    failure_message: "Bloqueado: se retomó trabajo sin leer la traza del pipeline. Riesgo de repetir fases o saltarse las pendientes."
  - check: "cada fase completada actualizó su entrada en pipeline-state.json con status, timestamp y evidencia verificable"
    failure_message: "Bloqueado: hay fases ejecutadas sin registrar en la traza. La traza desactualizada es peor que no tenerla."
  - check: "ninguna fase se marcó done sin la evidencia que su propio gate exige"
    failure_message: "Bloqueado: fase marcada done sin evidencia. Marcar done por haberlo intentado es falsear la traza."
---

# Pipeline State Tracking — La Traza que Sobrevive a la Sesión

## Problema que resuelve

Una generación real no cabe en una sesión: el contexto se llena y el trabajo continúa en otra instancia con un resumen automático que habla de **archivos**, no de **proceso**. Verificado en campo: seis sesiones encadenadas donde el agente saltó fases, repitió trabajo, olvidó correcciones del usuario dentro de la misma sesión y emitió el contrato de cierre dos veces sin haber ejecutado la suite. El conocimiento del chapter no falla ahí; falla la **memoria del progreso**.

La traza es un archivo en disco, no un recuerdo: `.evidence/pipeline-state.json` en el `output_path`.

## Cuándo aplicar

- **Al inicio de CUALQUIER sesión** (nueva o continuación) sobre un `output_path` que ya existe: leer la traza ANTES de hacer nada y reportar al usuario en qué fase quedó, qué sigue y qué está bloqueado. Es el paso 0 de `[[calidad-route-test-generation]]`.
- **Tras completar cada fase** del pipeline: actualizarla en el mismo turno en que la fase termina.
- **Antes de emitir `[[calidad-delivery-gate-contract]]`**: el gate lee la traza y no se emite con fases obligatorias pendientes.

Aplica a los 5 stacks (Karate, Playwright, K6, Appium, funcional); las fases cambian por ruta, el mecanismo no.

## Schema

```json
{
  "schema_version": "1.0",
  "run_id": "2026-08-10T14:05:00Z",
  "project_name": "appium-poc-flujo-credito",
  "stack": "appium",
  "route": "greenfield",
  "mode": "full",
  "execution_target": "mock",
  "sessions": 3,
  "phases": [
    {
      "id": "mandatory_inputs",
      "status": "done",
      "updated_at": "2026-08-10T14:07:11Z",
      "evidence": ".evidence/session-config.json",
      "notes": "5 insumos recibidos; extracción declarada por insumo"
    },
    { "id": "sut_readiness_gate", "status": "done", "evidence": "STRATEGY.md#6" },
    { "id": "strategy_approved",  "status": "done", "evidence": "STRATEGY.md (aprobado por usuario 14:22)" },
    { "id": "mock_up",            "status": "done", "evidence": ".evidence/mock-verification.json" },
    { "id": "prototype_accepted", "status": "blocked", "blocker": "parity_gate_failed: 3 selectores con 0 coincidencias" },
    { "id": "scaffold_emitted",   "status": "pending" },
    { "id": "instrumentation_verified", "status": "pending" },
    { "id": "smoke_gate",         "status": "pending" },
    { "id": "suite_executed",     "status": "pending" },
    { "id": "report_verified",    "status": "pending" },
    { "id": "triage_and_correction", "status": "pending" },
    { "id": "executive_report",   "status": "pending" },
    { "id": "delivery_gate",      "status": "pending" }
  ],
  "next_action": "Corregir los 3 identificadores faltantes en el prototipo y re-correr el gate de paridad",
  "open_corrections": [
    "Usuario pidió usar evidencia visual antes de hipotetizar (sesión 2) — aplicar en todo triage"
  ]
}
```

`status`: `pending | in_progress | done | blocked | skipped`. Todo `skipped` lleva `reason`; todo `blocked` lleva `blocker` con evidencia del sondeo que lo comprobó (ver Restricciones).

`open_corrections` es la memoria de las instrucciones que dio el usuario y que aplican a todo el resto del trabajo: se arrastran entre sesiones y se releen al abrir cada una. Una corrección del usuario que se pierde al cambiar de sesión se paga dos veces.

## Fases mínimas por ruta

| Ruta | Fases obligatorias |
|---|---|
| Automatización (los 4 stacks) | mandatory_inputs · sut_readiness_gate · strategy_approved · [mock_up · prototype_accepted si aplica] · scaffold_emitted · instrumentation_verified · smoke_gate · suite_executed · report_verified · triage_and_correction · executive_report · delivery_gate |
| Funcional | mandatory_inputs · insumos_analizados · [analysis · refinement_approved] o [design_traceability] o [strategy/plan_approved] · alm_write_confirmed · delivery_gate |

Las fases de mock/prototipo solo existen si `execution_target != real`. `executive_report` se marca `skipped` con razón en modos `scaffold-only`/`dry-run`.

## Instrucción

1. **Abrir sesión**: si existe `.evidence/pipeline-state.json`, leerlo y abrir el turno con un resumen de tres líneas — fase actual, qué falta, qué está bloqueado — más las `open_corrections` vigentes. Si no existe y el `output_path` es nuevo, crearlo con todas las fases en `pending`.
2. **Trabajar la fase**: marcarla `in_progress` al empezar.
3. **Cerrar la fase**: marcarla `done` **solo con la evidencia que su gate exige** (path del archivo, comando y exit code, o confirmación explícita del usuario). Sin evidencia no hay `done`.
4. **Registrar correcciones del usuario** en `open_corrections` en el mismo turno en que las recibe.
5. **Actualizar `next_action`** en cada escritura: es lo primero que lee la siguiente sesión.

## Restricciones

- **NUNCA marcar `done` una fase por haberla intentado.** Compilar no es ejecutar; ofrecer no es aprobar; generar no es verificar.
- **NUNCA declarar `blocked` sin evidencia del sondeo.** Un blocker de ambiente exige el comando ejecutado y su salida (`adb devices`, `curl` al mock, `appium --version`). Declarar bloqueos por suposición y cerrar sobre ellos ya ocurrió en campo: dos de tres bloqueos declarados eran falsos y el gate se emitió igual.
- **NUNCA emitir el delivery gate con fases obligatorias en `pending`** — el gate lee esta traza (`[[calidad-delivery-gate-contract]]`).
- La traza **no reemplaza** la evidencia: la referencia. Si el `evidence` apunta a un archivo que no existe, la fase no está `done`.
- La traza se actualiza en el turno de la fase, no "al final": una traza reconstruida de memoria es ficción.

## Cross-links

`[[calidad-route-test-generation]]`, `[[calidad-delivery-gate-contract]]`, `[[calidad-smoke-gate-policy]]`, `[[calidad-mandatory-inputs-protocol]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-post-generation-execution-prompt]]`.
