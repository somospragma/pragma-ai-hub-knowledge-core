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

- Tier elegido y justificación (banca core, API normal, servicio interno).
- Fecha y ambiente del baseline usado.
- Valores P95/P99/error rate medidos.
- Próxima fecha de recalibración (ej. cada release mayor).

## Criterios de finalización

- Los 5 scripts tienen `options.thresholds` actualizados al tier elegido.
- El smoke re-corrido pasa los nuevos thresholds.
- El tier y su justificación están documentados en `README.md`.
- Se conserva el JSON del baseline usado para auditoría (`results/${timestamp}-summary.json`).
