---
id: calidad-funcional-test-plan
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [funcional]
description: "Elabora planes de prueba basados en ISO/IEC/IEEE 29119-3 (con equivalencia IEEE 829): objetivos, alcance, riesgos con análisis, estrategia embebida, tipos, premisas, criterios de entrada/salida/suspensión, ambientes, datos, roles y cronograma. Más los entregables satélite: RTM, informes de avance y reporte de cierre."
tags: [funcional, test-plan, iso-29119, ieee-829, risk-analysis, rtm, traceability, deliverables]
---

# Test Plan — Plan de Pruebas y Entregables de Gestión

## Cuándo aplicar

- Cuando el usuario pide un plan de pruebas para un release, proyecto o iniciativa (formal para clientes que lo exigen, o ligero para equipos ágiles — el esqueleto es el mismo, la profundidad cambia).
- Como fase del workflow `[[calidad-build-test-strategy-and-plan]]`.
- Para los entregables satélite del proceso: matriz de trazabilidad (RTM), informes de avance y reporte de cierre.

## Instrucción

1. **Resolver el nivel del plan** — release/iteración vs proyecto/máster. Preguntar al usuario qué exige su contexto (cliente regulado suele exigir plan formal completo; equipo ágil interno, plan ligero de 3-5 páginas). La estructura no cambia; la profundidad sí.
2. **Construir el documento** — con `references/test-plan-structure.md` (estructura basada en ISO/IEC/IEEE 29119-3, mapeada a IEEE 829 para clientes que lo pidan): objetivos, alcance in/out, ítems de prueba, estrategia (embebida desde `[[calidad-funcional-test-strategy]]` o referenciada), tipos de prueba, premisas y consideraciones, dependencias.
3. **Análisis de riesgos** — con `references/risk-analysis-matrix.md`: riesgos de PRODUCTO (heredados del risk map de la estrategia) + riesgos de PROYECTO (ambientes, datos, gente, plazos, terceros), cada uno con probabilidad × impacto, mitigación, contingencia y dueño. Un plan sin riesgos con dueño es una lista de deseos.
4. **Criterios de entrada, salida y suspensión** — con `references/entry-exit-criteria.md`: qué debe ser cierto para empezar (DoR de las HUs, ambiente, datos), para declarar terminado (cobertura, defectos abiertos por severidad), y para suspender/reanudar (bloqueos de ambiente, tasa de fallos).
5. **Trazabilidad y métricas** — con `references/traceability-rtm.md`: la RTM (requisito → CA → caso → ejecución → defecto) como columna vertebral; se construye desde el diseño (`[[calidad-funcional-test-design]]`) y se mantiene con las ejecuciones. Si hay ALM, la RTM se materializa con links nativos (`[[calidad-alm-mcp-integration]]`) y el plan referencia las queries/vistas.
6. **Informes de avance y cierre** — con `references/progress-and-closure-reports.md`: formato del informe periódico (avance, bloqueos, métricas, riesgo re-evaluado) y del reporte de cierre (cumplimiento de criterios de salida, defectos residuales con riesgo aceptado, lecciones). El executive report post-corrida de los stacks (`[[calidad-executive-report-generator]]`) alimenta estos informes, no los reemplaza.
7. **Gate humano** — el plan se presenta al usuario/stakeholders y se aprueba antes de regir. Cambios de alcance re-abren el plan (versionado del documento).

## Restricciones

- **NUNCA inventar** datos de contexto del plan: SLAs, fechas, nombres de responsables, ambientes — lo que no se sepa queda "a determinar" con dueño y fecha, jamás rellenado con plausibilidades.
- **El plan compromete lo verificable**: criterios de salida medibles (números, no adjetivos). "Calidad satisfactoria" no es un criterio; "0 defectos CRITICAL/HIGH abiertos y cobertura 100% de CA CRITICAL" sí.
- Riesgo sin mitigación, contingencia y dueño no entra a la matriz — se termina de elaborar o se registra como pregunta.
- El plan referencia la estrategia; no la contradice. Si el plan necesita desviarse (recorte de alcance por plazo), la desviación se declara como decisión de riesgo aceptada por quien corresponde.
- Documentos vivos: plan, RTM e informes llevan versión y fecha; la historia de cambios se conserva.

## Cross-links

- `references/test-plan-structure.md`
- `references/risk-analysis-matrix.md`
- `references/entry-exit-criteria.md`
- `references/traceability-rtm.md`
- `references/progress-and-closure-reports.md`
- `[[calidad-funcional-test-strategy]]`, `[[calidad-funcional-test-design]]`, `[[calidad-alm-mcp-integration]]`, `[[calidad-build-test-strategy-and-plan]]`, `[[calidad-executive-report-generator]]`
