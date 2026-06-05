---
id: calidad-post-generation-protocol
version: 1.0.0
scope: chapter
type: steering
chapter: calidad
description: "Protocolo obligatorio que el agente DEBE ejecutar después de emitir el último archivo y antes del mensaje de cierre. Garantiza ejecución, triage, evidencia y delivery-gate."
tags: [protocol, mandatory, post-generation, execution, triage, evidence, delivery-gate, enforcement]
---

# Post-Generation Protocol — Disciplina Obligatoria Después del Último Archivo

## Rol

Después de emitir todos los archivos, ejecutar este protocolo en orden. Saltarse cualquier paso = entrega inválida.

Aplica a los 5 IDEs soportados (Kiro, Claude Code, GitHub Copilot, Amazon Q IDE, Amazon Q CLI) y a los 4 frameworks del chapter (Karate, Playwright, K6, Appium), tanto en greenfield como en brownfield.

## Pasos

1. **Coherence checks sobre el repo recién emitido**:
   - `find` paths esperados existen (estructura canónica del stack — link a project-structure por framework)
   - `grep` imports cruzados: fixtures/data deben ser importados por ≥1 test. Si no → es dead code, eliminar o usar.
   - Compile dry-run según stack: `mvn compile` / `npx tsc --noEmit` / `k6 inspect tests/*.js` / `./gradlew compileJava`
   - Para Karate: cada feature debe declarar `# cobertura: <N>` en primera línea y N debe coincidir con `effective_minimum`.

2. **Ejecutar tests según `modo`**:
   - `full`: ejecutar tests reales (smoke como mínimo). Capturar exit code, stdout, artefactos.
   - `dry-run`: mostrar plan de ejecución sin correr; documentar comandos.
   - `scaffold-only`: omitir ejecución; documentar razón.
   - `execute-only`: solo ejecuta sin generar.

   **Nota K6 — modo `full`**: el smoke gate 1:1 es obligatorio (ver [[k6-greenfield]] (consultar `references/smoke-1-1-gate.md`)). Solo después del smoke OK se ejecutan los otros escenarios (Carga / Estrés y opt-in Spike / Soak). Si el smoke 1:1 falla, status `partial` con `blocker: "smoke_1_1_failed"`, sin intentar correr Carga ni Estrés.

3. **Aplicar re-run N=3 sobre fallos** (modo full):
   - Por cada test fallido, re-ejecutar 2 veces más.
   - Clasificar: 3/3 fail mismo error → `deterministic`; alterna → `flaky`; 3/3 errores distintos → `flaky_high_variance`.
   - Aplica `[[calidad-failure-triage-and-classification]]`.

4. **Aplicar auto-corrección con guardrails** si triage habilita:
   - Invocar `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique.
   - Anti-cheating estricto: NUNCA modificar assertions de contrato, security, compliance.
   - Max 3 iteraciones. Después → escalar a humano.

5. **Persistir evidencia** en `.evidence/` del proyecto generado:
   - `session-config.json`: inputs + modo + risk_map
   - `generation-manifest.json`: lista de archivos creados (output del paso 1)
   - `execution-log-<fecha>.json`: resultado por test (modo full)
   - `audit-log-<fecha>.md`: correcciones aplicadas con guardrails verificados
   - `coverage-declared-vs-delivered.json`: comparación
   - Si la ejecución termina con bloqueo de ambiente (WAF, rate limit, DNS, IdP caído, device unavailable, browser missing, JDK wrong): emitir `.evidence/execution-status.json` según [[calidad-environment-blocker-evidence]]. El status final del delivery_gate pasa a `partial` con `blocker: "environment_blocked_<type>"`; la auto-corrección NO intenta resolver bloqueos de ambiente.

6. **Emitir delivery_gate yaml** según `[[calidad-delivery-gate-contract]]` antes del mensaje final.

7. **Reportar estado formal**: `success | partial | failed` con causa y blockers.

## Restricciones

- NUNCA declarar `success` sin ejecución real en modo `full`.
- NUNCA modificar test para hacerlo pasar cuando el SUT está roto (anti-cheating).
- NUNCA omitir `.evidence/` — sin evidencia = entrega inválida.

## Cross-links

`[[calidad-test-execution-orchestration]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-test-self-healing]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-delivery-gate-contract]]`.
