---
id: calidad-post-generation-protocol
version: 1.1.0
scope: chapter
type: steering
chapter: calidad
description: "Protocolo obligatorio que el agente DEBE ejecutar después de emitir el último archivo y antes del mensaje de cierre. Garantiza ejecución, triage, evidencia y delivery-gate."
tags: [protocol, mandatory, post-generation, execution, triage, evidence, delivery-gate, enforcement]
---

# Post-Generation Protocol — Disciplina Obligatoria Después del Último Archivo

## Rol

Después de emitir todos los archivos, ejecutar este protocolo en orden. Saltarse cualquier paso = entrega inválida.

Aplica a los 5 IDEs soportados y a los 4 frameworks del chapter, tanto en greenfield como en brownfield.

## Pasos

0. **Traza y bitácora** — Actualizar `.evidence/pipeline-state.json` y `.evidence/session-log.md` (`[[calidad-pipeline-state-tracking]]`) al entrar y tras CADA paso. Ninguna fase se marca `done` sin su evidencia.

0.b **Instrumentación ANTES de ejecutar** — Verificar que la evidencia se va a generar: logfile del servidor, log del mock si aplica, hook de captura y volcado de jerarquía por fallo. Instrumentar después de un fallo es diagnosticar a ciegas el primero.

1. **Coherence checks sobre el repo recién emitido**: los paths esperados existen; fixtures y datos están importados por al menos un test (si no, es código muerto); compila en seco según el stack; y en Cucumber, sin definiciones duplicadas ni pasos indefinidos en un `--dry-run` filtrado.

1.5. **Preflight y comando** — Antes de ejecutar nada: comando salido del repositorio y preflight verde con salida registrada (`[[calidad-execution-discipline-protocol]]`, `[[calidad-execution-preflight]]`).

2. **Ejecutar tests según `modo`** (`full` ejecuta y captura exit code y artefactos; `dry-run` documenta comandos sin correr; `scaffold-only` omite con razón; `execute-only` no genera). Cadencia obligatoria: **gate de UN escenario → suite completa como inventario → corrección aislada test por test → suite de regresión** (`[[calidad-smoke-gate-policy]]`, `[[calidad-test-self-correction-loop]]`). Verificar el conteo de escenarios ejecutados contra el filtro pedido antes de interpretar cualquier resultado. En K6, sin smoke 1:1 verde no se corren Carga ni Estrés.

3. **Triar los fallos** con `[[calidad-failure-triage-and-classification]]`: re-ejecutar **solo el test en cuestión** N=3 para separar determinista de flaky, mirar la evidencia antes de hipotetizar, y exigir la cadena completa antes de declarar un defecto del SUT.

4. **Auto-corregir con guardrails** si el triage lo habilita: `[[calidad-test-self-correction-loop]]` con `[[calidad-test-self-healing]]` cuando aplique. Un fallo a la vez, máximo 3 iteraciones, y después escalar. NUNCA tocar assertions de contrato, seguridad o compliance.

5. **Persistir evidencia** en `.evidence/` según `[[calidad-test-evidence-and-traceability]]`: configuración de sesión, manifiesto de generación, log de ejecución, log de auditoría de correcciones y cobertura declarada contra entregada. Ante bloqueo de ambiente, emitir el status según `[[calidad-environment-blocker-evidence]]`, cerrar `partial` con `blocker: "environment_blocked_<type>"` y **no** intentar auto-corregirlo.

6. **Emitir delivery_gate yaml** según `[[calidad-delivery-gate-contract]]` antes del mensaje final.

7. **Reportar estado formal**: `success | partial | failed` con causa y blockers.

## Restricciones

- NUNCA declarar `success` sin ejecución real en modo `full`.
- NUNCA modificar test para hacerlo pasar cuando el SUT está roto (anti-cheating).
- NUNCA omitir `.evidence/` — sin evidencia = entrega inválida.

## Cross-links

`[[calidad-test-execution-orchestration]]`, `[[calidad-failure-triage-and-classification]]`, `[[calidad-test-self-correction-loop]]`, `[[calidad-test-self-healing]]`, `[[calidad-test-evidence-and-traceability]]`, `[[calidad-delivery-gate-contract]]`.
