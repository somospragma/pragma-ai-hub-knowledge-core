---
id: extend-karate-brownfield
version: 1.0.0
scope: stack
type: workflow
chapter: calidad
stack: [automation]
description: Flujo para extender un proyecto Karate existente con nuevos features, respetando convenciones detectadas y reglas de cliente.
tags: [karate, brownfield, workflow]
---

# Workflow — Extender proyecto Karate brownfield

## Cuándo usar

Cuando `[[calidad-intent-detection]]` y `[[calidad-brownfield-vs-greenfield]]` identifican un escenario brownfield para Karate: el usuario provee al menos `karate-config.js` + un `.feature` del proyecto existente y solicita agregar pruebas para nuevos endpoints.

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

Lista completa en `[[karate-mandatory-inputs-brownfield]]`.

## Pasos

### 1. Detectar convenciones cliente-específicas
Pistas: paths con prefix de ticket (`{TICKET-XXX}`), variable de base URL no estándar, naming de scenarios con frases tipo "solicitud exitosa/fallida", headers transversales presentes en TODOS los features (p. ej. `Transaction-Id`, `Sid`, `Auth-Id`, `X-Channel`). El usuario también puede declararlo explícitamente. Si detectas convenciones cliente-específicas, activa las reglas documentadas en `references/client-specific-conventions.md`.

### 2. Validar inputs adicionales
Si el cliente impone convenciones, exigir `user_story` y `firma`. Validar `Body_Mode` ∈ {A, B}. Si falta cualquier obligatorio, detente y solicítalo (`[[calidad-mandatory-inputs-protocol]]`).

### 3. Analizar convenciones existentes
Aplicar el algoritmo de `[[karate-convention-detection]]`. Anota `features_dir`, `bodies_dir`, `package_name`, `base_url_var`, `header_style`, `body_loading_style`, `scenario_naming_pattern`, variables de `karate-config.js`. Si hay conflicto entre convención autodetectada y convenciones declaradas por el cliente, las del cliente ganan.

### 4. Calcular cobertura
Aplica `[[karate-negative-coverage-formula]]`. Si hay headers transversales obligatorios del cliente, súmalos aunque el spec no los marque como required (ver `references/client-specific-conventions.md`).

### 5. Generar SOLO `.feature` y body JSON
- `.feature` en `features_dir` detectado, con naming y tags del proyecto (siguiendo las convenciones cliente-específicas detectadas si aplican).
- Body JSON sólo si `Body_Mode = A`; nombre y ubicación según `bodies_dir`.
- Sin tocar `pom.xml`, `karate-config.js`, `TestRunner.java`, `logback-test.xml`, ni schemas existentes.

### 6. Validar
- Convenciones detectadas respetadas al 100% (header_style, body_loading_style, naming, tags).
- Convenciones cliente-específicas aplicadas si corresponde (naming, headers transversales obligatorios, assertions field-by-field).
- Ningún archivo de infraestructura generado.
- Verifica que el `pom.xml` existente cumpla `[[karate-feature-file-location-constraint]]`; si no, repórtalo al usuario sin modificarlo.

Entrega con `[[calidad-streaming-files-protocol]]`, trazabilidad con `[[calidad-test-evidence-and-traceability]]`.

### Fase final obligatoria — Ejecutar, triar y auto-corregir

**Esta fase es parte del contrato de entrega del workflow, no opcional.** Brownfield: la auto-corrección aplica **EXCLUSIVAMENTE** a los `.feature` y bodies recién generados por este workflow; NUNCA a los preexistentes del cliente, aunque fallen (ver `[[calidad-brownfield-vs-greenfield]]` sección "Auto-corrección en brownfield").

1. **Resolver modo de operación** con el usuario (`full` / `dry-run` / `scaffold-only` / `execute-only`). Default: `full` salvo cliente regulado (HIPAA, SOX, PCI-DSS Level 1, FedRAMP — clientes con convenciones cliente-específicas estrictas suelen ameritar `dry-run`) que defaultea a `dry-run`. Si el agente carece de capacidad técnica para ejecutar (sin `mvn`, sin acceso al ambiente del cliente), degradar a `scaffold-only` y reportar `partial`.
2. **Ejecutar** vía `[[calidad-test-execution-orchestration]]` filtrado por el tag de la nueva historia (`mvn test -Dkarate.options="--tags @user-story:{ticket-id}"`), de modo que la corrida toque sólo los features nuevos.
3. Si hay fallos: aplicar `[[calidad-failure-triage-and-classification]]` para clasificar cada uno como deterministic / flaky y diagnosticar causa raíz. Si un test preexistente del cliente falla por daño colateral (p. ej. cambio compartido en `karate-config.js`), detenerse y reportar — NO auto-corregir.
4. Si triage habilita correcciones: invocar `[[test-self-correction-loop]]` (workflow) que aplica `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Respetar `max_iterations` (default 3) y los **anti-cheating guardrails**: nunca relajar headers transversales del cliente, aserciones de negocio o status codes para forzar verde.
5. Reportar estado final: `success` (todos los nuevos tests pasan determinísticamente) | `partial` (entregado scaffold, no se pudo ejecutar) | `failed` (escalado a humano con feature, scenario, assertion, response y hipótesis).
6. Archivar evidencia + audit log de correcciones aplicadas según `[[calidad-test-evidence-and-traceability]]`.

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
