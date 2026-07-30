
# Criterios de entrada, salida y suspensión

Todos medibles: un tercero decide si se cumplen sin interpretar. Adjetivo sin número = criterio inválido.

## Criterios de entrada (para iniciar un ciclo de ejecución)

Plantilla base — ajustar valores por proyecto:

- E-1: 100% de las HUs del alcance con veredicto DoR `ready` o `ready_with_warnings` sin bloqueantes ([[calidad-funcional-story-analysis]]).
- E-2: Casos diseñados con trazabilidad 100% CA→caso ([[calidad-funcional-test-design]], quality gate del diseño).
- E-3: Ambiente del nivel correspondiente disponible y con smoke verde — o mock levantado con plan de switchover aprobado si `execution_target: mock` ([[calidad-sut-readiness-gate]]).
- E-4: Datos de prueba disponibles (reales anonimizados o sintéticos con seed registrado — [[calidad-test-data-management]]).
- E-5: Build/versión bajo prueba identificada e instalada (versión exacta en el informe).

## Criterios de salida (para declarar el ciclo/release probado)

- S-1: 100% de casos CRITICAL y HIGH ejecutados; >= {90}% del total ejecutado (lo no ejecutado, listado con motivo).
- S-2: 0 defectos CRITICAL abiertos; 0 HIGH abiertos sin plan de corrección aceptado por negocio; MEDIUM/LOW abiertos documentados como riesgo residual.
- S-3: Cobertura de CA: 100% de los CA del alcance con al menos una ejecución en pass (o defecto asociado).
- S-4: Regresión automatizada verde (suites de los stacks en CI) para los flujos CRITICAL.
- S-5: Si hubo ejecución contra mock: re-ejecución contra integraciones reales completada (`certification: certified` — la corrida mock NUNCA satisface los criterios de salida por sí sola).
- S-6: RTM actualizada y entregada; reporte de cierre emitido.

## Criterios de suspensión y reanudación

| ID | Suspensión (parar de ejecutar) | Reanudación |
|---|---|---|
| SU-1 | Bloqueo de ambiente clasificado (`environment_blocked_*` — [[calidad-environment-blocker-evidence]]) que impide > {50}% del ciclo | Ambiente restablecido + smoke verde |
| SU-2 | Tasa de fallos por defectos de build > {30}% en las primeras {2}h del ciclo (build no probable) | Nuevo build con los defectos bloqueantes corregidos + smoke verde |
| SU-3 | Cambio de alcance en caliente (HUs agregadas/retiradas mid-ciclo) | Plan re-versionado y aprobado |

La ejecución suspendida se reporta `partial` con el criterio SU que aplicó — suspender por criterio es disciplina, no fracaso.

## Reglas

1. Los valores entre `{}` son defaults del chapter: se ajustan por proyecto en la elaboración del plan y quedan fijados en el documento aprobado.
2. Los criterios de salida se verifican con evidencia (queries del ALM, delivery gates de los stacks), no con declaración verbal.
3. Excepciones a un criterio de salida = decisión de riesgo aceptada, con nombre de quien acepta, en el reporte de cierre. El criterio no se reescribe retroactivamente para que "dé".
