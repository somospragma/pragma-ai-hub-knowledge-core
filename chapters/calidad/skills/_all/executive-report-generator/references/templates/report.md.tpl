% Reporte ejecutivo — {{project_name}}
% {{firma}}
% {{iso_timestamp}}

# Reporte ejecutivo — {{project_name}}

| Stack | Modo | Fecha corrida | Branch | Commit | Ambiente |
|---|---|---|---|---|---|
| {{framework}} | {{mode}} | {{iso_timestamp}} | {{branch}} | {{commit_short}} | {{environment}} |

## 1. Resumen ejecutivo

<span class="badge badge-{{status_color}}">{{status_color_label}}</span>

{{summary}}

## 2. Cumplimiento de SLAs

{{slas_table}}

## 3. Resultados por escenario / HU / feature

{{scenarios_table}}

## 4. Comparación entre corridas

{{runs_comparison_table}}

## 5. Hallazgos clasificados

{{findings}}

## 6. Recomendaciones por rol

{{recommendations}}

## 7. Anexos

{{annexes}}

---

Reporte generado por `[[calidad-executive-report-generator]]`. Para clasificación de fallos ver `[[calidad-failure-triage-and-classification]]`. Para el contrato de cierre de la entrega ver `[[calidad-delivery-gate-contract]]`.
