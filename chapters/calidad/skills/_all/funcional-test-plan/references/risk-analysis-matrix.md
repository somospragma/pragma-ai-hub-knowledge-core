
# Matriz de riesgos del plan

Dos familias, una matriz. Los riesgos de **producto** vienen del risk map de la estrategia ([[calidad-funcional-test-strategy]], `references/risk-based-approach.md`); los de **proyecto** son propios del plan. Ambos con el mismo rigor.

## Formato

| ID | Tipo | Riesgo | Prob | Impacto | Nivel | Mitigación (reduce prob/impacto) | Contingencia (si ocurre) | Dueño |
|---|---|---|---|---|---|---|---|---|
| RP-1 | producto | El motor de recálculo de intereses produce redondeos erróneos en montos altos | media | alto | HIGH | BVA exhaustivo + casos de borde automatizados en CI (Karate) | Bloqueo del release; corrida de regresión del módulo completo | QA lead |
| RY-1 | proyecto | Ambiente QA compartido con otro equipo; ventanas de inestabilidad | alta | medio | HIGH | Calendario de ventanas acordado; smoke gate antes de cada ciclo | Suspensión según criterio S-2; reprogramación del ciclo | PM |
| RY-2 | proyecto | Datos de prueba del cliente no entregados a la fecha del hito 2 | media | alto | HIGH | data_strategy: synthetic con Faker+seed desde el día 1 ([[calidad-test-data-management]]) | Ejecutar con sintéticos y re-certificar la muestra con datos reales al llegar | QA lead |

## Catálogo de riesgos de proyecto típicos (checklist de elaboración)

- **Ambiente**: no disponible a tiempo, compartido/inestable, sin datos, WAF/rate limits sin allowlist ([[calidad-environment-blocker-evidence]] documenta los bloqueos cuando ocurren).
- **Desarrollo no listo**: el plan cubre el camino mock→real ([[calidad-sut-readiness-gate]]) — el riesgo es el switchover tardío, y su mitigación es el plan de switchover explícito.
- **Datos**: entrega tardía, PII sin anonimizar (riesgo legal — escalar, no mitigar localmente), volumen insuficiente para performance.
- **Insumos funcionales**: HUs sin refinar a la fecha de diseño (mitigación: [[calidad-funcional-story-analysis]] como gate de entrada).
- **Personas**: dependencia de una sola persona con conocimiento del dominio; rotación a mitad de ciclo.
- **Terceros**: sandbox de proveedor inestable, certificaciones externas con agenda propia.
- **Plazo**: compresión del ciclo por retraso de desarrollo — la contingencia canónica es ejecutar por prioridad del risk map (CRITICAL primero) y declarar el recorte como riesgo aceptado, NUNCA "probar más rápido".

## Reglas

1. Riesgo sin dueño, mitigación Y contingencia no entra — se completa o se registra como pregunta abierta.
2. La matriz se **re-evalúa en cada informe de avance** (`progress-and-closure-reports.md`): riesgos materializados pasan a issues, nuevos riesgos entran versionados.
3. Los riesgos que el negocio decide aceptar sin mitigación quedan con la firma de quién aceptó (nombre y fecha en el documento).
4. Anti-patrón: matriz genérica copiada de otro proyecto. Cada riesgo debe nombrar ESTE producto, ESTE ambiente, ESTAS fechas.
