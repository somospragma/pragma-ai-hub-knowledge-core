---
id: calibrate-k6-thresholds
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Workflow para recalibrar thresholds K6 a partir de un baseline real medido en una corrida smoke previa.
tags: [k6, thresholds, calibration, baseline, smoke]
---

# Calibrate K6 Thresholds — Workflow

## Cuándo usar

Después de la primera corrida smoke con datos reales del servicio. Los thresholds iniciales generados con `[[k6-greenfield]]` son una estimación (Moderate por default — ver `[[k6-thresholds-three-tiers]]`); este workflow los alinea al comportamiento observado.

Aplícalo también cuando:

- Cambia el ambiente (QA → staging → prod) y los SLAs son distintos.
- Se ajustan recursos (CPU/memoria) del servicio y cambia el baseline.
- Hay regresión sostenida en P95/P99 y se requiere validar si el threshold sigue siendo realista.

## Inputs

- **Obligatorio**: JSON summary del smoke run anterior (archivo `results/${timestamp}-summary.json` exportado por `[[k6-handle-summary-evidence]]`).
- **Opcional**: `user_story.SLA` y/o `firma.SLA` actualizados, si el contexto de negocio cambió.

## Pasos

### Paso 1 — Medir baseline

Lee el JSON del smoke y extrae:

- `metrics.http_req_duration.values["p(95)"]`
- `metrics.http_req_duration.values["p(99)"]`
- `metrics.http_req_failed.values.rate`
- `metrics.checks.values.rate`

### Paso 2 — Seleccionar tier

Compara los valores medidos contra los tres tiers (`[[k6-thresholds-three-tiers]]`):

- Si P95 medido < 500 ms y error rate < 0.001 → candidato Conservative.
- Si P95 medido < 1000 ms y error rate < 0.01 → Moderate.
- Si P95 medido < 2000 ms y error rate < 0.05 → Relaxed.

Si el `user_story` o `firma` declaran un SLA más estricto que el baseline, prevalece el SLA: el servicio no cumple y los thresholds del tier elegido deben fallar el build hasta que se corrija.

### Paso 3 — Actualizar `options.thresholds`

Aplica los valores del tier seleccionado a los 5 scripts (`smoke`, `load`, `stress`, `spike`, `soak`). Usa el snippet correspondiente de `[[k6-thresholds-three-tiers]]`.

### Paso 4 — Re-correr smoke como validación

Ejecuta `npm run smoke` (ver `[[k6-run-and-suite]]`). Si los nuevos thresholds pasan, la calibración es válida. Si fallan, revisa si el servicio degradó o si el tier es demasiado estricto para el baseline real.

### Paso 5 — Documentar

En el `README.md` del proyecto, registra:

- Tier elegido y justificación (mission-critical, business-as-usual, internal — con la razón objetiva del contexto, no del sector).
- Fecha y ambiente del baseline usado.
- Valores P95/P99/error rate medidos.
- Próxima fecha de recalibración (ej. cada release mayor).

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Este workflow **es naturalmente un loop de ejecución + triage + auto-corrección de thresholds**: medir, comparar, ajustar, re-verificar. Aquí formalizamos esa naturaleza alineándola con la capacidad cross-cutting del chapter. Auto-corrección aplica EXCLUSIVAMENTE a los valores numéricos de `options.thresholds`; NUNCA a `checks`, lógica del script, ni a scripts que no sean propiedad de este proyecto.

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default para calibración: `execute-only` (los scripts ya existen; sólo se actualizan thresholds y se re-corre el smoke). Para clientes regulados (HIPAA, SOX, PCI-DSS Level 1, FedRAMP) defaultear a `dry-run` (entregar diff de thresholds propuesto sin aplicar). `scaffold-only` no aplica acá. Si el agente carece de capacidad para correr `k6`, degradar a `dry-run` y reportar `partial`.
2. **Ejecutar** el smoke re-corrido (paso 4) vía `[[calidad-test-execution-orchestration]]`. Capturar el nuevo `results/${timestamp}-summary.json`.
3. Si el smoke falla con los nuevos thresholds: aplicar `[[calidad-failure-triage-and-classification]]`. Distinguir entre:
   - **Tier demasiado estricto vs. baseline real** → ajuste legítimo de tier hacia uno más permisivo, dentro de los tres tiers canónicos. NO inventar tiers ad-hoc.
   - **Servicio degradado** → NO relajar el threshold; reportar al humano que el SUT degradó y mantener el tier alineado al SLA.
   - **Flakiness por ambiente o saturación de red** → reportar y proponer ventana o instancia dedicada; no maquillar con thresholds.
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]`. `[[calidad-test-self-healing]]` típicamente NO aplica acá (no hay selectores). Respetar `max_iterations` (default 3) y los **anti-cheating guardrails maestros de calibración**: jamás cruzar el SLA declarado por el negocio en `user_story` / `firma`; jamás eliminar métricas de `options.thresholds`; jamás convertir `http_req_failed` en un porcentaje absurdo (>0.1) para forzar verde.
5. Reportar estado final: `success` (smoke pasa con tier elegido y SLA respetado) | `partial` (no se pudo ejecutar smoke; se entregaron thresholds propuestos en diff) | `failed` (servicio degradado o flakiness no atribuible a thresholds — escalado a humano con métricas, SLA y razonamiento).
6. Archivar evidencia + audit log de cambios de threshold según `[[calidad-test-evidence-and-traceability]]`. Conservar el JSON del baseline previo y del baseline post-calibración para auditoría.

## Criterios de finalización

- Los 5 scripts tienen `options.thresholds` actualizados al tier elegido.
- El smoke re-corrido pasa los nuevos thresholds.
- El tier y su justificación están documentados en `README.md`.
- Se conserva el JSON del baseline usado para auditoría (`results/${timestamp}-summary.json`).
- [ ] Smoke re-corrido ejecutado al menos una vez con los thresholds nuevos. Estado: `success` / `partial` / `failed` reportado.
- [ ] Si hubo fallos: clasificación (servicio degradado vs tier irreal vs flakiness ambiental) y causa raíz documentada. SLA de negocio NUNCA cruzado.
- [ ] Si hubo correcciones aplicadas (ajuste de tier): audit log persistido con anti-cheating guardrails verificados (sólo se tocaron valores numéricos de `options.thresholds`, dentro de los tres tiers canónicos).
- [ ] Si el modo es `dry-run`: diff de thresholds propuesto entregado; ningún cambio aplicado sin aprobación humana.
- [ ] Métricas `http_req_duration`, `http_req_failed` y `checks` no fueron eliminadas de `options.thresholds` bajo ningún concepto (regla anti-cheating maestra de calibración).
