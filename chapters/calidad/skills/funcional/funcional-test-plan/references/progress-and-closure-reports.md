
# Informes de avance y reporte de cierre

Los entregables periódicos que hacen visible el proceso. Se alimentan de la RTM, de los delivery gates y executive reports de los stacks ([[calidad-executive-report-generator]]) y del estado del ALM — no se redactan de memoria.

## Informe de avance (periódico: semanal o por hito)

```markdown
# Informe de avance de pruebas — {proyecto} — {fecha} (v{n})

## 1. Resumen ejecutivo (5 líneas máx)
Estado general: verde | amarillo | rojo — con la razón en una frase.

## 2. Avance de ejecución
| Métrica | Valor | Plan | Delta |
|---|---|---|---|
| Casos ejecutados / total | 142/210 (68%) | 75% | -7% |
| Pass / Fail / Bloqueados | 120 / 14 / 8 | | |
| Cobertura CA (ejecución) | 71% | | |
Por prioridad: CRITICAL 100% ejecutado, HIGH 82%...

## 3. Defectos
Abiertos por severidad: CRITICAL {n} / HIGH {n} / MEDIUM {n} / LOW {n}
Nuevos vs cerrados en el periodo; tendencia; top 3 con impacto.

## 4. Bloqueos y suspensiones
Bloqueos activos (con su clasificación environment_blocked_* si aplica), desde cuándo, dueño.

## 5. Riesgos re-evaluados
Cambios a la matriz del plan: materializados, nuevos, degradados.

## 6. Próximo periodo
Foco, hitos, decisiones que se necesitan de stakeholders (explícitas).
```

Regla de oro: el informe **pide las decisiones que necesita** ("necesitamos ambiente estable antes del lunes o el hito 3 se corre") — informar sin pedir decisión es archivar el problema.

## Reporte de cierre

```markdown
# Reporte de cierre de pruebas — {proyecto/release} — {fecha}

## 1. Veredicto contra criterios de salida
| Criterio | Meta | Resultado | Cumple |
|---|---|---|---|
(cada S-n del plan, con evidencia linkeada)
Excepciones aceptadas: quién, cuándo, por qué.

## 2. Resumen de ejecución
Totales finales, por prioridad y por tipo; cobertura de diseño y de ejecución.

## 3. Defectos residuales (riesgo aceptado)
Cada defecto abierto al cierre: severidad, impacto esperado en producción, workaround, quién aceptó.

## 4. Estado de certificación
Si hubo corridas contra mock: confirmación de la re-ejecución real (certification: certified) o el pendiente explícito.

## 5. Entregables
Links: RTM final, casos en ALM, evidencia, executive reports por stack, suites automatizadas en CI.

## 6. Lecciones y recomendaciones
Qué mejorar del proceso (alimenta el siguiente plan); deuda de pruebas que queda (casos LOW diferidos, charters pendientes).
```

## Reglas

1. Números desde las fuentes (ALM queries, delivery gates), citando la fuente; sin números "estimados de cabeza".
2. El semáforo del resumen ejecutivo se justifica con los criterios del plan, no con optimismo.
3. Publicación: markdown local en `reports/` + al ALM/wiki del cliente vía [[calidad-alm-mcp-integration]] si el proyecto lo usa. El reporte de cierre acompaña al delivery gate final, no lo sustituye.
