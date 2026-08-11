
# Enfoque risk-based

El esfuerzo de pruebas es finito; el riesgo lo distribuye. La estrategia identifica riesgos de PRODUCTO (qué puede fallar y doler), los califica y asigna profundidad de prueba proporcional. Los riesgos de PROYECTO (plazos, gente, ambientes) van al plan, no aquí.

## Identificación

Fuentes: criticidad de flujos de negocio (dinero, onboarding, autenticación — [[calidad-business-driven-prioritization]]), exposición regulatoria ([[calidad-context-determined-defaults]]), historial de defectos, complejidad técnica declarada por dev, dependencias externas frágiles, novedad (código nuevo > código estable).

## Calificación (probabilidad × impacto)

| | Impacto bajo | Impacto medio | Impacto alto |
|---|---|---|---|
| **Prob. alta** | MEDIUM | HIGH | CRITICAL |
| **Prob. media** | LOW | MEDIUM | HIGH |
| **Prob. baja** | LOW | LOW | MEDIUM |

- **Impacto**: efecto de la falla en producción — pérdida económica, sanción regulatoria, daño reputacional, usuarios bloqueados. Se califica con negocio, no lo decide QA solo.
- **Probabilidad**: qué tan factible es que la falla exista — complejidad, novedad, historial, calidad del refinamiento.

Cada riesgo se registra: `R-{n}: descripción | prob | impacto | nivel | mitigación de prueba`.

## Del riesgo a la profundidad de prueba

| Nivel de riesgo | Profundidad mínima |
|---|---|
| CRITICAL | Todas las técnicas formales aplicables + negativos exhaustivos + automatización en CI + exploratorio dedicado + (si aplica) performance y seguridad específicas |
| HIGH | Técnicas formales sobre los CA + negativos principales + automatización |
| MEDIUM | Happy path + negativos de primera línea; automatización selectiva |
| LOW | Happy path; puede quedar manual o diferido — decisión declarada |

Este mapeo alimenta directamente: la prioridad de los casos ([[calidad-funcional-test-design]]), el orden de automatización, y la sección de riesgos del plan ([[calidad-funcional-test-plan]] — donde cada riesgo lleva además dueño y contingencia).

## Reglas

1. El risk map se **acuerda con negocio/PO** — QA propone la calificación, negocio confirma el impacto. Sin esa conversación es un mapa de suposiciones.
2. Lo que queda en LOW con poco esfuerzo se declara con todas las letras ("los reportes internos se prueban solo happy path") — riesgo aceptado visible, no hueco silencioso.
3. El mapa es vivo: defectos encontrados suben probabilidad; releases estables la bajan. Revisarlo por release, no escribirlo una vez.
4. Anti-patrón: calificar todo CRITICAL "por si acaso" — si todo es crítico nada lo es, y el mapa deja de decidir.
