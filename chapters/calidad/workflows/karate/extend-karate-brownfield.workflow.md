---
id: calidad-extend-karate-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [karate]
description: Flujo para extender un proyecto Karate existente con nuevos features, respetando convenciones detectadas y reglas de cliente.
tags: [karate, brownfield, workflow]
---

# Workflow — Extender proyecto Karate brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario brownfield para Karate: el usuario provee al menos `karate-config.js` + un `.feature` del proyecto existente y solicita agregar pruebas para nuevos endpoints.

### Pre-flight (OBLIGATORIO)

Antes de cualquier acción, ejecutar [[calidad-karate-greenfield]] (consultar `references/preflight.md` en su subfolder) del stack. En brownfield aplica los mismos checks de versión/tooling. Si falla → degradar a `scaffold-only` con razón documentada.

Cumplir el protocolo `[[calidad-pre-generation-protocol]]` incluso en brownfield: confirmar inputs (incluido `modo`), declarar coverage de los archivos NUEVOS (no de los preexistentes), esperar confirmación del usuario.

### Regla brownfield específica — Auto-corrección

La auto-corrección y self-healing aplican EXCLUSIVAMENTE a los archivos NUEVOS que este workflow genera. Los archivos preexistentes del cliente (tests, Page Objects, fixtures, configs) son INTOCABLES bajo ningún concepto, aunque fallen. Si tests preexistentes fallan en la ejecución:

1. Reportar el fallo al usuario con triage (deterministic vs flaky).
2. NUNCA modificar el test preexistente.
3. NUNCA modificar fixtures, data o configs preexistentes para hacer pasar tests.
4. Escalar a humano con el contexto completo del fallo.

Esta regla es non-negotiable y es enforcement obligatorio del `[[calidad-test-self-correction-loop]]` y sus `references/anti-cheating-guardrails.md`.

Refuerzos adicionales:
- **Step isolation** (ver `[[calidad-step-isolation-pattern]]`) aplica a los features y scenarios NUEVOS. Los features preexistentes mantienen su estructura aunque no cumplan el patrón; no se les aplica refactor.
- **Validación contractual no superficial** (ver `references/contractual-checks-from-user-story.md` del skill K6 como referencia de granularidad equivalente para escenarios Karate basados en historia/spec) aplica solo a scenarios nuevos. NO re-escribir matchers ni checks preexistentes.

### Paso previo — Análisis condicional con STRATEGY.md

Si el alcance del brownfield es **grande** (≥3 endpoints/HUs/escenarios nuevos, o cambios cross-cutting que afectan multiple features preexistentes): generar `STRATEGY.md` según el template [[calidad-karate-greenfield]] (template en ``references/templates.md` (sección `STRATEGY.md`)`) y el skill `[[calidad-pre-design-strategy-document]]`. Esperar aprobación del usuario antes de continuar.

Si el alcance es **pequeño** (1-2 cambios puntuales): omitir STRATEGY.md y proceder directo a generación, documentando la decisión en `.evidence/scope-decision.md`.

Respetar convenciones del proyecto cliente: el STRATEGY del brownfield documenta lo NUEVO, no rediseña lo existente.

## Inputs

| Input | Obligatorio | Notas |
|---|---|---|
| `spec` | Sí | OpenAPI 3.x, Swagger 2.0 o WSDL del nuevo endpoint. |
| Archivos de proyecto existente | Sí | Mínimo `karate-config.js` + 1 `.feature`. |
| `ticket_id` | Sí si el cliente impone convenciones; recomendado en otros | Identificador de historia o ticket. |
| `Body_Mode` | Sí | `A` (JSON externo) \| `B` (inline / step-by-step). |
| `Scenario_Prefix` | No | Se autodetecta del proyecto (ej. `{TICKET-XXX}`). |
| `user_story` | Obligatorio si el cliente impone convenciones | Tag `@user-story:{ticket-id}`. |
| `firma` | Obligatorio si el cliente impone convenciones | Documento técnico. |

Lista completa en `[[calidad-karate-brownfield]] (consultar `references/mandatory-inputs-brownfield.md` en su subfolder)`.

## Pasos

### Paso 0 — Leer la traza del pipeline (SIEMPRE)

Aplica `[[calidad-pipeline-state-tracking]]` antes de tocar nada: si el `project_root`/`output_path` ya tiene `.evidence/pipeline-state.json`, leerlo y abrir el turno reportando fase actual, pendientes, bloqueos y `open_corrections`. Si no existe, crearlo con las fases de la ruta brownfield en `pending`. Actualizarlo al cerrar cada fase, con evidencia.

En brownfield el riesgo de perder el hilo es MAYOR que en greenfield: son sesiones largas sobre proyectos grandes del cliente, que es justo donde el contexto se llena y el proceso se fragmenta.


### 1. Detectar convenciones cliente-específicas
Pistas: paths con prefix de ticket (`{TICKET-XXX}`), variable de base URL no estándar, naming de scenarios con frases tipo "solicitud exitosa/fallida", headers transversales presentes en TODOS los features (p. ej. `Transaction-Id`, `Sid`, `Auth-Id`, `X-Channel`). El usuario también puede declararlo explícitamente. Si detectas convenciones cliente-específicas, activa las reglas documentadas en `references/client-specific-conventions.md`.

### 2. Validar inputs adicionales
Si el cliente impone convenciones, exigir `user_story` y `firma`. Validar `Body_Mode` ∈ {A, B}. Si falta cualquier obligatorio, detente y solicítalo (`[[calidad-mandatory-inputs-protocol]]`).

### 3. Analizar convenciones existentes
Aplicar el algoritmo de `[[calidad-karate-brownfield]] (consultar `references/convention-detection.md` en su subfolder)`. Anota `features_dir`, `bodies_dir`, `package_name`, `base_url_var`, `header_style`, `body_loading_style`, `scenario_naming_pattern`, variables de `karate-config.js`. Si hay conflicto entre convención autodetectada y convenciones declaradas por el cliente, las del cliente ganan.

### 4. Calcular cobertura
Aplica `[[calidad-karate-greenfield]] (consultar `references/negative-coverage-formula.md` en su subfolder)`. Si hay headers transversales obligatorios del cliente, súmalos aunque el spec no los marque como required (ver `references/client-specific-conventions.md`).

### 5. Generar SOLO `.feature` y body JSON
- `.feature` en `features_dir` detectado, con naming y tags del proyecto (siguiendo las convenciones cliente-específicas detectadas si aplican).
- Body JSON sólo si `Body_Mode = A`; nombre y ubicación según `bodies_dir`.
- Sin tocar `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, ni schemas existentes.

### 6. Validar
- Convenciones detectadas respetadas al 100% (header_style, body_loading_style, naming, tags).
- Convenciones cliente-específicas aplicadas si corresponde (naming, headers transversales obligatorios, assertions field-by-field).
- Ningún archivo de infraestructura generado.
- Verifica que el `pom.xml` existente cumpla `[[calidad-karate-greenfield]] (consultar `references/file-location-constraint.md` en su subfolder)`; si no, repórtalo al usuario sin modificarlo.

Entrega con `[[calidad-streaming-files-protocol]]`, trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Brownfield: la auto-corrección aplica **EXCLUSIVAMENTE** a los `.feature` y bodies recién generados por este workflow; NUNCA a los preexistentes del cliente, aunque fallen (ver `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

**Cadencia de corrección (aplica a los tests nuevos de esta corrida)**: gate de un escenario → suite de los tests nuevos como inventario → **corrección aislada, re-ejecutando SOLO el test que se corrige** → regresión de los nuevos. Nunca relanzar la suite en cada iteración. Detalle en `[[calidad-test-self-correction-loop]]`. La suite preexistente del cliente no entra en este ciclo.


1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP — clientes con convenciones cliente-específicas estrictas suelen ameritar `dry-run`) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin `mvn`, sin acceso al ambiente del cliente), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` filtrado por el tag de la nueva historia (`mvn test -Dkarate.options="--tags @user-story:{ticket-id}"`), de modo que la corrida toque sólo los features nuevos.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky y diagnosticar causa raíz. Si un test preexistente del cliente falla por daño colateral (p. ej. cambio compartido en `karate-config.js`), detenerse y reportar — NO auto-corregir.
4. Si triage habilita correcciones: invocar `[[calidad-test-self-correction-loop-workflow]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar headers transversales del cliente, aserciones de negocio o status codes para forzar verde.
5. Reportar estado final: `success` (todos los nuevos tests pasan determinísticamente) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con feature, scenario, assertion, response y hipótesis).
6. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`.
7. **Invocar `[[calidad-post-generation-protocol]]`** para coherence checks post-emisión (find paths, grep imports cruzados, compile/lint dry-run sobre archivos nuevos) antes de cerrar.
8. **Smoke gate universal (tests nuevos)**: antes de declarar `success`, ejecutar el smoke gate del stack según [[calidad-smoke-gate-policy]]. En brownfield Karate, el gate ejecuta **únicamente los features nuevos** filtrados por tag: `mvn test -Dkarate.options="--tags @smoke and @new"` o equivalente filtrado por path del feature recién generado. Los features preexistentes NO se ejecutan en el gate para no inflar tiempo ni contaminar resultados. Si fallan tests preexistentes al correr la suite completa después, eso NO bloquea la entrega — se reporta como issue separado.
9. **Evidencia de bloqueo de ambiente**: si la ejecución sufre bloqueo de ambiente (WAF/network/auth/rate limit/SSL), emitir `.evidence/execution-status.json` según [[calidad-environment-blocker-evidence]]. El estado pasa a `partial` con razón.
10. **Metadata por corrida**: emitir `results/karate/{date}/{ISO}-metadata.json` según el schema universal [[calidad-execution-metadata-schema]]. En brownfield, el campo `workload_or_scope` debe distinguir "N features/scenarios nuevos sobre M preexistentes".
11. **Reporte ejecutivo**: invocar `[[calidad-generate-executive-report]]` para producir reporte consolidado en `.evidence/report-{ISO}.{html|pptx|docx|md}`, usando `karate-report-template.md`. El reporte debe segregar explícitamente "features/scenarios nuevos (en scope de esta sesión)" de "features preexistentes (referencia, no ejecutados en el gate)".
12. **Emitir el bloque `delivery_gate` yaml** según `[[calidad-delivery-gate-contract]]` — **precondición: leer `.evidence/pipeline-state.json` y verificar cero fases obligatorias pendientes; con pendientes NO se emite el gate, se emite reporte de estado y el trabajo continúa** — con: status declarado coherente con execution, manifest de archivos nuevos, evidencia (`.evidence/session-config.json`, `.evidence/generation-manifest.json`, execution log si modo=full, `.evidence/execution-status.json` si hubo bloqueo de ambiente, metadata por corrida, reporte ejecutivo, audit log si hubo correcciones), blockers (fallos en tests preexistentes del cliente reportados como blocker con status `partial`, jamás auto-corregidos).

## Criterios de finalización

1. Convenciones detectadas respetadas al 100%.
2. Ningún archivo de infraestructura generado (`pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, schemas existentes intactos).
3. Convenciones cliente-específicas aplicadas si corresponde (ver `references/client-specific-conventions.md`):
   - Feature naming `{ticket-prefix}-{us-description}.feature`.
   - Scenarios con prefijo `{ticket-prefix}-{ticket-id} solicitud exitosa/fallida - ...`.
   - Tags del proyecto (p. ej. `@happyPath @regression @smoke` positivo / `@negative @regression` negativo) respetados.
   - Headers one-by-one, body step-by-step, assertions field-by-field si el proyecto lo usa.
   - Headers transversales obligatorios del cliente cubiertos (missing + invalid-format donde aplique).
4. Fórmula de cobertura aplicada y declarada.
5. Sin lógica condicional en aserciones; `Examples` sin celdas vacías.
6. Comando `mvn test` filtrado por tag de la nueva historia provisto en la entrega.
7. Tests nuevos ejecutados al menos una vez. Estado: `success` / `partial` / `failed` reportado.
8. Si hubo fallos: clasificación de cada uno (deterministic vs flaky) y causa raíz documentada. Fallos de tests preexistentes del cliente reportados al humano, NO auto-corregidos.
9. Si hubo correcciones aplicadas: audit log persistido con anti-cheating guardrails verificados. Auto-corrección sólo tocó los features/bodies generados por este workflow.
10. Si el modo es `dry-run` o `scaffold-only`: scaffold + comando de ejecución + diffs propuestos entregados; ninguna corrección aplicada sin aprobación humana.
11. Tests en suites `@security`, `@contract`, `@compliance`, `@regulatory` NO fueron modificados por auto-corrección bajo ningún concepto (regla anti-cheating maestra). Los headers transversales obligatorios del cliente quedan intocables.
