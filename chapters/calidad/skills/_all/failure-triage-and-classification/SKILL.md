---
id: calidad-failure-triage-and-classification
version: 1.1.0
scope: chapter
type: skill
chapter: calidad
description: "Clasificar fallos de tests como deterministas vs intermitentes; identificar causa raíz (bug del SUT, test mal diseñado, data state, ambiente, timing, locator stale, infrastructura) antes de proponer cualquier corrección."
tags: [triage, classification, flakiness, root-cause, deterministic, quarantine, enforcement, mandatory]
enforcement: mandatory
verification:
  - check: "re-run N=3 aplicado sobre cada fallo y clasificación deterministic|flaky|flaky_high_variance asignada por test"
    failure_message: "Bloqueado: no se aplicó re-run N=3 ni se clasificó cada fallo. No se puede pasar a corrección sin triage."
  - check: "causa raíz declarada (bug SUT, test design, data state, ambiente, timing, locator stale, infra) antes de proponer fix"
    failure_message: "Bloqueado: triage no produjo causa raíz; auto-corrección sin causa raíz esconde bugs del SUT."
  - check: "fallos clasificados como bug del SUT NO pasan a self-correction; se escalan a humano con reporte"
    failure_message: "Bloqueado: se intentó auto-corregir un bug real del SUT — violación de anti-cheating."
---

# Failure Triage and Classification — Clasificación de Fallos y Análisis de Causa Raíz antes de Corregir

## Cuándo aplicar

Aplica este skill **después de ejecutar tests con `[[calidad-test-execution-orchestration]]` cuando hay >0 fallos**. Es el paso obligatorio que separa la ejecución de la corrección: ningún fallo se "arregla" sin pasar primero por triage. El output de este skill es **input obligatorio para `[[calidad-test-self-correction-loop]]`** — sin clasificación correcta no se debe intentar auto-corrección, porque auto-corregir un bug real del SUT lo esconde.

El triage también alimenta:

- `[[calidad-test-self-healing]]` cuando el patrón es `flaky + locator stale`.
- `[[calidad-test-data-management]]` cuando el patrón es `flaky + data state`.
- El reporte al cliente cuando el patrón es `deterministic + bug del SUT`.

Se aplica a todos los frameworks del alcance del chapter: Playwright, Appium, Karate, K6, Pact y herramientas de visual regression.

## Instrucción

1. **Aislar el fallo.** Antes de clasificar, recolectar la evidencia mínima: `test_id`, mensaje de error completo, stack trace, screenshot/trace (Playwright/Appium), request/response (Karate/API), métricas y thresholds (K6), `environment context` (URL del SUT, branch, commit, runner, OS, browser/device). Sin esta evidencia el triage es opinión, no análisis. Ver `[[calidad-test-evidence-and-traceability]]` para el formato canónico.

2. **Aplicar el protocolo de re-run para determinismo** descrito en `references/re-run-protocol-for-determinism.md`: re-ejecutar el test N veces (default N=3) en el **mismo entorno y con los mismos datos**. Resultado:
   - 3/3 fallan con el mismo error → `deterministic`.
   - 3/3 fallan con errores distintos → `flaky_high_variance` (race condition probable).
   - 1/3 o 2/3 fallan → `flaky`.
   - 0/3 fallan → `flaky` (transient en run 1).

3. **Clasificar el patrón de fallo** contra el catálogo en `references/failure-pattern-catalog.md`. Las categorías canónicas son: bug real del SUT, test design issue, data state, environment, timing/sync, locator stale, infrastructure. Cada patrón del catálogo trae síntomas observables, causa probable, evidencia a recolectar y acción recomendada.

4. **Decidir acción** aplicando el árbol de decisión de `references/bug-vs-test-design-decision-tree.md`. Reglas resumidas:
   - `deterministic + bug del SUT` → reportar al equipo de desarrollo del cliente con la evidencia. **NO modificar el test**.
   - `deterministic + test design issue` → habilitado para `[[calidad-test-self-correction-loop]]`.
   - `flaky + locator stale` → habilitado para `[[calidad-test-self-healing]]`.
   - `flaky + data state` → fixear cleanup/fixtures; ver `[[calidad-test-data-management]]`.
   - `flaky + timing` → ajustar waits explícitos; auto-corregible bajo el loop de self-correction.
   - `flaky + environment` → escalar a plataforma del cliente; el test no es el problema.

5. **Calcular stability score** del test según `references/stability-score-metric.md`: porcentaje verde en las últimas N corridas (default 20) **en runs reales del pipeline**, no en runs locales del agente. Si el score cae bajo 80%, el test se marca para quarantine.

6. **Aplicar el quarantine pattern** si corresponde, siguiendo `references/quarantine-pattern.md`: aislar en suite `@quarantine`, crear ticket de resolución con SLA, y **no bloquear el pipeline principal**. Quarantine sin ticket con SLA equivale a test muerto y está prohibido.

## Restricciones

- **NUNCA** clasificar como "test design issue" sin haber verificado primero el comportamiento real del SUT. Lo que parece test mal escrito puede ser bug de regresión recién introducido.
- **NUNCA** quarantine sin ticket de resolución asociado y SLA explícito. Quarantine sin SLA = test muerto, deuda silenciosa.
- **NUNCA** auto-corregir un test clasificado como `deterministic + bug del SUT`. La auto-corrección en ese caso esconde el bug y rompe el contrato anti-cheating del chapter (ver guardrails en `[[calidad-test-self-correction-loop]]`).
- **El stability score se mide en runs reales del pipeline CI**, no en runs locales del agente. Runs locales no son representativos de la realidad de ejecución.
- **Si el SUT está caído o degradado, suspender el triage** hasta restablecer el ambiente. NO marcar tests como flaky cuando la infraestructura del SUT está rota — es ruido que contamina las métricas de estabilidad.
- **NUNCA** ejecutar el protocolo de re-run sobre tests de performance/K6**: re-correr K6 puede dejar el SUT en estado degradado y los resultados no son comparables run-a-run por la naturaleza del workload. Usar análisis manual de métricas.
- **El triage es obligatorio antes de cualquier auto-corrección**. Saltarse este skill y pasar directo a `[[calidad-test-self-correction-loop]]` está prohibido por la política del chapter.

## Cross-links

- `references/re-run-protocol-for-determinism.md` — protocolo de re-ejecución para distinguir deterministic vs flaky.
- `references/failure-pattern-catalog.md` — catálogo de patrones de fallo con síntomas, causa y acción.
- `references/bug-vs-test-design-decision-tree.md` — árbol de decisión para decidir si corregir el test o reportar bug.
- `references/stability-score-metric.md` — definición y cálculo del stability score.
- `references/quarantine-pattern.md` — mecánica de quarantine con SLA y eliminación tras 30 días.

Cross-links con otros assets del chapter:

- `[[calidad-chapter-perspective]]`
- `[[calidad-mandatory-inputs-protocol]]`
- `[[calidad-test-evidence-and-traceability]]`
- `[[calidad-test-data-management]]`
- `[[calidad-cicd-integration]]`
- `[[calidad-test-execution-orchestration]]`
- `[[calidad-test-self-healing]]`
- `[[calidad-test-self-correction-loop]]`
- `[[calibrate-k6-thresholds]]`
