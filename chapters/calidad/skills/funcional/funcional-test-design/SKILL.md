---
id: calidad-funcional-test-design
version: 1.0.0
scope: stack
type: skill
chapter: calidad
stack: [funcional]
description: "Diseña casos de prueba de alto nivel desde HUs analizadas: selección de técnica ISTQB (particiones, BVA, tablas de decisión, transición de estados, pairwise, casos de uso, error guessing, exploratorio), formato Gherkin español data-driven, alineación BDD/ATDD/TDD y trazabilidad CA a caso al 100%."
tags: [funcional, test-design, istqb, bva, equivalence-partitioning, decision-table, pairwise, gherkin, bdd, traceability]
---

# Test Design — Casos de Prueba de Alto Nivel con Técnicas Formales

## Cuándo aplicar

- Cuando el usuario pide diseñar casos de prueba desde HUs, criterios de aceptación, reglas de negocio o un example map.
- Como fase de diseño del workflow `[[calidad-design-test-cases]]` (que además los publica al ALM).
- Como insumo upstream de la automatización: los casos de alto nivel diseñados aquí son la fuente de los `.feature` de Karate/Appium y los specs de Playwright — se diseña una vez, se automatiza después.

Prerrequisito: la HU pasó por `[[calidad-funcional-story-analysis]]` con veredicto `ready | ready_with_warnings`. Diseñar sobre una HU `not_ready` produce casos que validan ambigüedades — se rechaza y se ofrece el análisis primero.

## Lectura obligatoria antes de producir el entregable

Este SKILL es el índice; el método vive en `references/`. **Abrir estos ANTES de escribir el entregable** y declarar cuáles se leyeron (traza en `[[calidad-pipeline-state-tracking]]`):

| Reference | Para qué |
|---|---|
| `references/technique-selection-guide.md` | Qué técnica aplica según el comportamiento |
| `references/equivalence-partitioning-bva.md` | Particiones y valores límite |
| `references/test-case-format.md` | Formato canónico del caso y matriz de trazabilidad |

## Instrucción

1. **Clasificar la HU y elegir técnicas** — con `references/technique-selection-guide.md`: el tipo de comportamiento (validación de entradas, reglas combinadas, ciclo de vida, flujo de usuario, configuración multi-plataforma) determina las técnicas. La selección se declara y justifica ANTES de escribir casos — nunca "casos por intuición".
2. **Aplicar las técnicas formales** que correspondan:
   - Particiones de equivalencia + valores límite: `references/equivalence-partitioning-bva.md` (obligatoria ante cualquier campo con rango, longitud, formato o monto).
   - Tablas de decisión y transición de estados: `references/decision-tables-state-transition.md` (reglas combinadas y ciclos de vida de entidades).
   - Combinatoria pairwise: `references/combinatorial-pairwise.md` (matrices plataforma/país/rol — reduce explosión combinatoria con cobertura de pares).
   - Error guessing y charters exploratorios: `references/exploratory-charters-error-guessing.md` (complementan, nunca sustituyen, a las técnicas formales).
3. **Derivar del example map si existe** — cada ejemplo verde del refinamiento (`[[calidad-funcional-story-refinement]]`) se convierte en al menos un caso; las reglas azules definen particiones y tablas.
4. **Redactar los casos** — formato de `references/test-case-format.md`: Gherkin en español (Dado/Cuando/Entonces/Y), data-driven con parámetros `@param` y tabla de valores cuando hay variantes, priorización risk-based vía `[[calidad-business-driven-prioritization]]` (nunca por keywords), precondiciones y datos concretos (coordinados con `[[calidad-test-data-management]]`).
5. **Alinear con la estrategia del equipo** — `references/bdd-atdd-alignment.md`: si el equipo trabaja BDD/ATDD, los casos SON los ejemplos ejecutables futuros (mismo Gherkin que consumirá la automatización); si es tradicional, formato paso | resultado esperado. Preguntar, no asumir.
6. **Verificar la cobertura (quality gate del diseño)** — matriz CA→casos: cada criterio de aceptación con al menos un caso positivo y, donde aplique, negativo; cada caso traza a un CA o a una regla (casos huérfanos = alcance inventado, se eliminan o se justifica su regla). Cobertura < 100% de CA = diseño incompleto, no se entrega como terminado.

## Restricciones

- **NUNCA diseñar desde la nada**: sin CA ni reglas escritas no hay diseño — hay adivinación. Devolver al análisis/refinamiento.
- **NUNCA limitar la cantidad de casos por estética**: la cobertura la dictan las técnicas y los CA. Tampoco inflar: dos casos que ejercitan la misma partición con datos distintos son uno solo parametrizado.
- **Los casos de alto nivel no incluyen detalles de implementación de automatización** (selectores, endpoints internos): describen comportamiento observable. La bajada a código es de los stacks de automatización.
- Casos de seguridad y compliance diseñados aquí heredan la regla maestra del chapter: una vez automatizados con tags `@security`/`@compliance`, no se modifican por auto-corrección.
- Trazabilidad bidireccional obligatoria en el entregable (tabla CA ↔ casos).

## Cross-links

- `references/technique-selection-guide.md`
- `references/equivalence-partitioning-bva.md`
- `references/decision-tables-state-transition.md`
- `references/combinatorial-pairwise.md`
- `references/exploratory-charters-error-guessing.md`
- `references/test-case-format.md`
- `references/bdd-atdd-alignment.md`
- `[[calidad-funcional-story-analysis]]`, `[[calidad-funcional-story-refinement]]`, `[[calidad-design-test-cases]]`, `[[calidad-alm-mcp-integration]]`, `[[calidad-business-driven-prioritization]]`
