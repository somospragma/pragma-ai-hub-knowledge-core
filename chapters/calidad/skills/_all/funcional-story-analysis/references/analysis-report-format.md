
# Formato del reporte de análisis

Un reporte por HU + resumen agregado si es lote. En markdown (persistible como archivo o como comentario del work item vía [[calidad-alm-mcp-integration]]).

## Estructura por HU

```markdown
# Análisis de HU — {ID}: {título}

**Fuente**: {azure|jira|manual} {link al work item si aplica}
**Veredicto DoR**: ready | ready_with_warnings | not_ready
**Bloqueantes**: {n} | **Menores**: {m}

## 1. INVEST
| Criterio | Veredicto | Evidencia |
|---|---|---|
| Independent | pass/warn/fail | "cita" — justificación en una línea |
| ... (los 6) | | |

## 2. Criterios de aceptación
| CA | Veredicto | Hallazgos |
|---|---|---|
| CA-1 "resumen corto" | pass/warn/fail | numerados, con cita |

Cobertura de familias: autorización {sí/no}, validación entrada {sí/no},
estados {sí/no}, errores de dependencias {sí/no}, ... 
Proporción happy/negativo: {x}/{y}.

## 3. Ambigüedades y vacíos — preguntas para el PO
| # | Tipo | Cita | Pregunta | Severidad |
|---|---|---|---|---|
| 1 | condicional incompleta | "si el cupo es suficiente..." | ¿Comportamiento exacto cuando el cupo NO es suficiente? | bloqueante |

## 4. Qué falta para `ready`
Lista accionable, un ítem por acción (responde pregunta N, parte la HU, agrega CA de X).
```

## Resumen agregado (lotes)

```markdown
# Análisis de lote — {sprint/plan/consulta} ({n} HUs)
| HU | Veredicto | Bloqueantes | Preguntas |
|---|---|---|---|
Distribución: ready {a} / ready_with_warnings {b} / not_ready {c}
Top 3 patrones repetidos del lote (ej. "ninguna HU cubre caminos negativos")
```

## Reglas

1. El veredicto va **arriba** — quien lee 10 segundos se lleva lo esencial.
2. Toda fila cita evidencia; sin cita, la fila no va.
3. Las preguntas al PO se redactan listas para pegar en el refinamiento (autocontenidas, sin "ver arriba").
4. Si se publica al ALM: como **comentario** del work item (nunca editando la descripción), con prefijo `[QA análisis {fecha ISO}]`. Registrar el link del comentario en la evidencia local.
5. Persistencia local: `analysis/{HU-ID}-analysis-{fecha}.md` dentro del `output_path` del proyecto funcional.
